import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("policy", ROOT / "scripts/ci/sf-deploy-policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_registry_and_explicit_manifest(self):
        d = policy.registry()
        self.assertEqual(policy.target(d, "DevSreFeat")["github_environment"], "sf-devsrefeat-read")
        self.assertEqual(policy.members(policy.pkg_info(d, "security-apex"))["ApexClass"], ["CompareSecurityCode", "CompareSecurityCodeTest"])
        self.assertEqual(policy.members(policy.pkg_info(d, "clone-pipeline-lwc"))["LightningComponentBundle"], ["clonePipelineAction"])
        with self.assertRaises(policy.PolicyError):
            policy.target(d, "PROD")
        with self.assertRaises(policy.PolicyError):
            policy.pkg_info(d, "../../invalid")

    def test_apex_newline_xml_and_changes(self):
        allowed = {"ApexClass":["CompareSecurityCode"]}
        left = {
            "package.xml": b"<Package/>",
            "classes/CompareSecurityCode.cls": b"public class A {}\r\n",
            "classes/CompareSecurityCode.cls-meta.xml": b"<A><B>1</B></A>\n"
        }
        right = dict(left)
        right["classes/CompareSecurityCode.cls"] = b"public class A {}\n"
        right["classes/CompareSecurityCode.cls-meta.xml"] = b"<A>\n  <B>1</B>\n</A>"
        self.assertEqual(policy.compare(left, right, allowed), (True, 0))
        right["classes/CompareSecurityCode.cls"] = b"public class B {}\n"
        self.assertEqual(policy.compare(left, right, allowed), (False, 1))

    def test_drift_diagnostics_only_identify_reviewed_members(self):
        manifest = {"ApexClass": ["One", "Two"]}
        left = {
            "package.xml": b"<Package/>",
            "classes/One.cls": b"public class One { String secret = 'private'; }",
            "classes/One.cls-meta.xml": b"<A/>",
            "classes/Two.cls": b"public class Two {}",
            "classes/Two.cls-meta.xml": b"<A/>",
        }
        right = dict(left)
        right["classes/One.cls"] = b"public class One { String secret = 'changed'; }"
        changed = policy.mismatched_components(left, right, manifest)
        self.assertEqual(changed, ["ApexClass:One"])
        self.assertNotIn("private", ",".join(changed))
        self.assertNotIn("changed", ",".join(changed))
        # Verify a source-only mismatch in ApexClass metadata is identified too.
        right["classes/One.cls"] = left["classes/One.cls"]
        right["classes/Two.cls-meta.xml"] = b"<B/>"
        self.assertEqual(policy.mismatched_components(left, right, manifest), ["ApexClass:Two"])

    def test_drift_part_classification(self):
        manifest = {"ApexClass": ["ClonePipelineControllerTest"]}
        base = {
            "package.xml": b"<Package/>",
            "classes/ClonePipelineControllerTest.cls": b"@IsTest private class A {}",
            "classes/ClonePipelineControllerTest.cls-meta.xml": b"<A><apiVersion>67.0</apiVersion></A>",
        }
        self.assertEqual(policy.mismatched_file_types(base, base, manifest), [])
        meta_changed = dict(base)
        meta_changed["classes/ClonePipelineControllerTest.cls-meta.xml"] = (
            b"<A><apiVersion>66.0</apiVersion></A>"
        )
        self.assertEqual(
            policy.mismatched_file_types(base, meta_changed, manifest),
            ["ApexClass:ClonePipelineControllerTest:metadata"],
        )
        source_changed = dict(base)
        source_changed["classes/ClonePipelineControllerTest.cls"] = (
            b"@IsTest private class B {}"
        )
        self.assertEqual(
            policy.mismatched_file_types(base, source_changed, manifest),
            ["ApexClass:ClonePipelineControllerTest:source"],
        )
        both_changed = dict(source_changed)
        both_changed["classes/ClonePipelineControllerTest.cls-meta.xml"] = (
            meta_changed["classes/ClonePipelineControllerTest.cls-meta.xml"]
        )
        self.assertEqual(
            policy.mismatched_file_types(base, both_changed, manifest),
            [
                "ApexClass:ClonePipelineControllerTest:metadata",
                "ApexClass:ClonePipelineControllerTest:source",
            ],
        )

    def test_lwc_drift_diagnostics_do_not_print_file_contents(self):
        manifest = {"LightningComponentBundle": ["clonePipelineAction"]}
        left = {
            "package.xml": b"<Package/>",
            "lwc/clonePipelineAction/clonePipelineAction.js-meta.xml": b"<A/>",
            "lwc/clonePipelineAction/clonePipelineAction.js": b"original source",
        }
        right = dict(left)
        right["lwc/clonePipelineAction/clonePipelineAction.js"] = b"sensitive org source"
        self.assertEqual(
            policy.mismatched_components(left, right, manifest),
            ["LightningComponentBundle:clonePipelineAction"]
        )

    def test_lwc_whole_bundle_and_unapproved_file(self):
        allowed = {"LightningComponentBundle":["clonePipelineAction"]}
        source = {
            "package.xml": b"<Package/>",
            "lwc/clonePipelineAction/clonePipelineAction.js-meta.xml": b"<root/>",
            "lwc/clonePipelineAction/clonePipelineAction.js": b"export default class A {}"
        }
        self.assertEqual(policy.compare(source, source, allowed), (True, 0))
        source["classes/Unexpected.cls"] = b"secret"
        with self.assertRaises(policy.PolicyError):
            policy.compare(source, source, allowed)

    def test_zip_prefix_and_traversal(self):
        okay = self.root / "okay.zip"
        with zipfile.ZipFile(okay, "w") as f:
            f.writestr("unpackaged/package.xml", "<Package/>")
            f.writestr("unpackaged/classes/Example.cls", "public class Example {}")
        self.assertIn("classes/Example.cls", policy.from_zip(okay))
        bad = self.root / "bad.zip"
        with zipfile.ZipFile(bad, "w") as f:
            f.writestr("unpackaged/package.xml", "<Package/>")
            f.writestr("../private.txt", "do-not-read")
        with self.assertRaises(policy.PolicyError):
            policy.from_zip(bad)

    def test_wildcard_blocked(self):
        original = policy.ROOT
        try:
            policy.ROOT = self.root
            (self.root / "manifest").mkdir()
            (self.root / "manifest/rejected.xml").write_text(
                '<?xml version="1.0"?><Package xmlns="http://soap.sforce.com/2006/04/metadata">'
                '<types><members>*</members><name>ApexClass</name></types><version>67.0</version></Package>'
            )
            with self.assertRaises(policy.PolicyError):
                policy.members({"manifest":"manifest/rejected.xml", "allowed_types":["ApexClass"]})
        finally:
            policy.ROOT = original

if __name__ == "__main__":
    unittest.main()
