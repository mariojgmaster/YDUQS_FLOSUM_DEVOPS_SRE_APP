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
