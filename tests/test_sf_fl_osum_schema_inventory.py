import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "scripts/ci/sf-flosum-schema-inventory.py"
spec = importlib.util.spec_from_file_location("schema_inventory", FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SchemaInventoryTests(unittest.TestCase):
    def test_exact_owner_issue(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "event.json"
            data = {
                "action": "opened",
                "sender": {"login": "owner"},
                "repository": {"owner": {"login": "owner"}},
                "issue": {"title": mod.ISSUE_TITLE, "body": mod.ISSUE_BODY,
                          "user": {"login": "owner"}},
            }
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(mod.verify_issue(path, "owner"))
            data["issue"]["body"] += "\noperation=deploy"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(mod.DiscoveryError):
                mod.verify_issue(path, "owner")

    def test_namespace_and_candidate_limits(self):
        records = ["Flosum__Deployment__c", "Flosum__Release__c",
                   "git__Git_Commit__c", "Flosum__Pipeline__c",
                   "YDUQS_Secret_Deployment__c", "Flosum__Deployment__c"]
        totals, selected = mod.select_candidates({"status": 0, "result": records})
        self.assertEqual(totals["deployment"], 1)
        self.assertEqual(totals["release"], 1)
        self.assertEqual(totals["commit"], 1)
        self.assertEqual(len(selected), 3)
        self.assertEqual(mod.role_for("Flosum__Pipeline__c"), None)
        self.assertIsNone(mod.role_for("Flosum__Deployment__c; echo secret"))

    def test_signal_not_a_dora_measurement(self):
        obj = {"status": 0, "result": {"fields": [
            {"name": "CreatedDate", "type": "datetime"},
            {"name": "Flosum__Deployment_Status__c", "type": "picklist"},
            {"name": "Flosum__Target_Environment__c", "type": "reference"},
            {"name": "Flosum__Completion_Date__c", "type": "datetime"},
            {"name": "Flosum__Commit__c", "type": "reference"},
        ]}}
        flags = mod.signals_for_describe(obj)
        self.assertTrue(flags["lifecycle"])
        self.assertTrue(flags["target"])
        self.assertTrue(flags["time"])
        self.assertTrue(flags["commit_link"])
        self.assertFalse(flags["release_link"])

    def test_denies_malformed_list(self):
        for payload in ({"result": []}, {"status": 0, "result": {}}, None):
            with self.assertRaises(mod.DiscoveryError):
                mod.select_candidates(payload)

    def test_exact_workflow_does_not_expose_payload(self):
        yml = (ROOT / ".github/workflows/sf-devsrefeat-diagnostics.yml").read_text("utf-8")
        self.assertIn("flosum-schema-inventory", yml)
        self.assertIn("github.event.issue.user.login == github.repository_owner", yml)
        self.assertIn('sf-flosum-schema-inventory.py --verify-issue', yml)
        self.assertIn('sf-flosum-schema-inventory.py --inventory', yml)
        program = FILE.read_text("utf-8")
        self.assertNotIn("sf data query ", program)
        self.assertNotIn("sf project deploy ", program)


if __name__ == "__main__":
    unittest.main()
