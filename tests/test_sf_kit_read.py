"""Offline contract tests for Salesforce DevOps Kit read-only operations."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
module_spec = importlib.util.spec_from_file_location("sf_kit_read_report", ROOT/"scripts/ci/sf-kit-read-report.py")
module = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(module)

intent_spec = importlib.util.spec_from_file_location("sf_m5_intent", ROOT/"scripts/ci/sf-m5-chatops-intent.py")
intent = importlib.util.module_from_spec(intent_spec)
intent_spec.loader.exec_module(intent)
SCRIPT = (ROOT/"scripts/ci/sf-kit-read.sh").read_text("utf8")
WORKFLOW = (ROOT/".github/workflows/sf-m5-chatops-plan.yml").read_text("utf8")


class KitReadTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.candidate = self.base/"candidate"
        self.candidate.mkdir()
        (self.candidate/"classes").mkdir()
        self.blobs = {"package.xml": b"<Package/>"}
        for name in ("CompareSecurityCode", "CompareSecurityCodeTest"):
            self.blobs[f"classes/{name}.cls"] = f"public class {name} {{}}".encode()
            self.blobs[f"classes/{name}.cls-meta.xml"] = (b'<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">'
                                                          b'<apiVersion>67.0</apiVersion><status>Active</status></ApexClass>')
        for name, data in self.blobs.items():
            path = self.candidate/name
            path.parent.mkdir(exist_ok=True, parents=True)
            path.write_bytes(data)
        self.remote = self.base/"remote.zip"
        self.zip(self.blobs)

    def zip(self, blobs):
        with ZipFile(self.remote, "w") as z:
            for name, data in blobs.items():
                z.writestr("unpackaged/"+name, data)

    def test_retrieve_summarizes_manifest_scope_only(self):
        report = module.produce("retrieve", "security-apex", self.remote)
        self.assertEqual(report["operation"], "retrieve")
        self.assertEqual(report["result"], "retrieved")
        self.assertEqual(report["component_count"], 2)
        self.assertFalse(report["modified_salesforce"])
        self.assertFalse(report["modified_git"])
        self.assertFalse(report["raw_metadata_included"])
        self.assertNotIn("public class", json.dumps(report))

    def test_compare_equal_vs_drift_without_payload(self):
        report = module.produce("compare", "security-apex", self.remote, self.candidate)
        self.assertEqual(report["result"], "equal")
        self.assertEqual(report["differing_files"], 0)
        modified = dict(self.blobs)
        modified["classes/CompareSecurityCode.cls"] = b"SECRET_REMOTE_CONTENT_9988"
        self.zip(modified)
        report = module.produce("compare", "security-apex", self.remote, self.candidate)
        self.assertEqual(report["result"], "different")
        self.assertEqual(report["differing_files"], 1)
        self.assertEqual(report["differing_members"], ["ApexClass:CompareSecurityCode"])
        self.assertIn("source", report["differing_parts"][0])
        self.assertNotIn("SECRET_REMOTE", json.dumps(report))

    def test_compare_apex_metadata_drift_reports_only_bounded_safe_facts(self):
        modified = dict(self.blobs)
        modified["classes/CompareSecurityCode.cls-meta.xml"] = (
            b'<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">'
            b'<apiVersion>66.0</apiVersion><status>Active</status></ApexClass>'
        )
        self.zip(modified)
        report = module.produce("compare", "security-apex", self.remote, self.candidate)
        self.assertEqual(report["result"], "different")
        self.assertEqual(report["differing_files"], 1)
        self.assertEqual(report["differing_members"], ["ApexClass:CompareSecurityCode"])
        self.assertEqual(report["differing_parts"], ["ApexClass:CompareSecurityCode:metadata"])
        self.assertEqual(len(report["apex_metadata_facts"]), 1)
        self.assertIn("baselineApi=67.0", report["apex_metadata_facts"][0])
        self.assertIn("remoteApi=66.0", report["apex_metadata_facts"][0])
        self.assertTrue(report["apex_metadata_structure"])
        self.assertNotIn("public class", json.dumps(report))

    def test_remote_metadata_outside_manifest_is_rejected(self):
        attack = dict(self.blobs, **{"classes/UnlistedClass.cls": b"unsafe"})
        self.zip(attack)
        with self.assertRaises(module.policy.PolicyError):
            module.produce("retrieve", "security-apex", self.remote)

    def test_issue_schema_explicit_read_operation_never_deploy(self):
        owner="mariojgmaster"
        repo=owner+"/YDUQS_FLOSUM_DEVOPS_SRE_APP"
        for action in ("retrieve", "compare"):
            ev = {
                "action": "opened",
                "sender": {"login": owner},
                "repository": {"full_name": repo, "default_branch": "master"},
                "issue": {"state": "open", "number": 12, "user": {"login": owner},
                          "title": f"SDOA {action.upper()} DevSreFeat security-apex",
                          "body": f"SDOA-CHATOPS/3\noperation={action}\ntarget=DevSreFeat\npackage_id=security-apex\n"}
            }
            result = intent.check(ev, owner, repo, expected_operation=action)
            self.assertEqual(result["operation"], action)
            self.assertEqual(result["confirmation"], "")
            self.assertEqual(result["commit_sha"], "")
            ev["issue"]["body"] += "confirmation=DEPLOY DevSreFeat security-apex\n"
            with self.assertRaises(intent.IntentError):
                intent.check(ev, owner, repo, expected_operation=action)

    def test_workflow_and_shell_readonly_guards(self):
        self.assertIn("--target-metadata-dir", SCRIPT)
        self.assertIn("--zip-file-name package.zip", SCRIPT)
        self.assertNotIn("sf project deploy start", SCRIPT)
        self.assertNotIn("sf project deploy preview", SCRIPT)
        self.assertNotIn("sf project retrieve start --ignore-conflicts", SCRIPT)
        self.assertIn('GITHUB_EVENT_REPOSITORY_PRIVATE', SCRIPT)
        self.assertIn('SDOA_EXPORT_RAW', SCRIPT)
        self.assertIn("SDOA_M5_READ_SUCCEEDED", WORKFLOW)
        self.assertIn("github.event.repository.private", WORKFLOW)
        self.assertIn("retention-days: 1", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
