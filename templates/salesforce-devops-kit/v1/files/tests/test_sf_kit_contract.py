"""Portable security contract for the universal Salesforce DevOps Kit."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WF = (ROOT/".github/workflows/sf-m5-chatops-plan.yml").read_text("utf8")
READ = (ROOT/"scripts/ci/sf-kit-read.sh").read_text("utf8")
WRITE = (ROOT/"scripts/ci/sf-general-deploy.sh").read_text("utf8")
spec = importlib.util.spec_from_file_location("intent", ROOT/"scripts/ci/sf-m5-chatops-intent.py")
intent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intent)


class KitContractTests(unittest.TestCase):
    def test_workflow_only_owner_and_first_attempt(self):
        for required in ("issues:", "types: [opened]", "github.repository_owner",
                         "github.event.issue.user.login == github.repository_owner",
                         "github.run_attempt == 1", "ref: " + "$" + "{{ github.sha }}",
                         "bash scripts/ci/sf-kit-read.sh", "bash scripts/ci/sf-general-deploy.sh"):
            self.assertIn(required, WF)
        self.assertNotIn("pull_request_target:", WF)
        self.assertNotIn("issue_comment:", WF)

    def test_read_does_not_write_or_print_raw_payload(self):
        self.assertIn("sf project retrieve start", READ)
        self.assertIn("--target-metadata-dir", READ)
        self.assertNotIn("sf project deploy start", READ)
        self.assertNotIn("set -x", READ)
        self.assertIn("SDOA_KIT_PUBLIC_SAFE_ONLY", READ)

    def test_write_has_explicit_confirmation_and_dry_run(self):
        self.assertIn('[[ "$OPERATION" == plan || "$OPERATION" == deploy ]]', WRITE)
        self.assertIn("sf project deploy start --dry-run", WRITE)
        self.assertIn("SDOA_REAL_DEPLOY_SUCCEEDED", WRITE)
        self.assertIn("SDOA_FINAL_GATE_DENIED", WRITE)

    def test_schema_rejects_freeform(self):
        repo = "customer/repository"
        ev = {
            "action": "opened",
            "sender": {"login": "customer"},
            "repository": {"full_name": repo, "default_branch": "master"},
            "issue": {"user": {"login": "customer"}, "number": 5, "state": "open",
                      "title": "SDOA RETRIEVE sandbox review-apex",
                      "body": "SDOA-CHATOPS/3\noperation=retrieve\ntarget=sandbox\npackage_id=review-apex\n"}
        }
        self.assertEqual(intent.check(ev, "customer", repo)["operation"], "retrieve")
        ev["issue"]["body"] += "deploy=true\n"
        with self.assertRaises(intent.IntentError):
            intent.check(ev, "customer", repo)


if __name__ == "__main__":
    unittest.main()
