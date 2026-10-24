"""Incident ChatOps: no credentials, Salesforce or GitHub requests."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts/ci/sf-incident-chatops-intent.py"
spec = importlib.util.spec_from_file_location("incident_intent", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
workflow = (ROOT / ".github/workflows/sf-devsrefeat-incidents-validate.yml").read_text("utf-8")
validator = (ROOT / "scripts/ci/sf-incident-sandbox-validate.sh").read_text("utf-8")
m5 = (ROOT / ".github/workflows/sf-m5-chatops-plan.yml").read_text("utf-8")
OWNER = "mariojgmaster"
REPO = f"{OWNER}/YDUQS_FLOSUM_DEVOPS_SRE_APP"


def event():
    return {
        "action": "opened",
        "repository": {"full_name": REPO, "default_branch": "master"},
        "sender": {"login": OWNER},
        "issue": {
            "number": 123, "state": "open",
            "title": module.TITLE,
            "body": module.BODY,
            "user": {"login": OWNER}
        }
    }


class IncidentIntentTests(unittest.TestCase):
    def test_exact_owner_intent(self):
        self.assertEqual(module.check(event(), OWNER, REPO), 123)
        trimmed = event()
        trimmed["issue"]["body"] = module.BODY.rstrip("\n")
        self.assertEqual(module.check(trimmed, OWNER, REPO), 123)

    def test_not_for_other_people_or_repos(self):
        for obj, key in [("sender", "login"), ("repository", "full_name")]:
            data = event()
            data[obj][key] = "attacker"
            with self.assertRaises(module.IntentError):
                module.check(data, OWNER, REPO)
        data = event()
        data["issue"]["user"]["login"] = "attacker"
        with self.assertRaises(module.IntentError):
            module.check(data, OWNER, REPO)

    def test_only_opened_issues_and_exact_body(self):
        for action in ("labeled", "edited", "reopened"):
            data = event()
            data["action"] = action
            with self.assertRaises(module.IntentError):
                module.check(data, OWNER, REPO)
        for snippet in ("\noperation=deploy\n", "\nmanifest=../../secret\n", "\nconfirmation=DEPLOY DevSreFeat\n", "\nscript=$(whoami)\n"):
            data = event()
            data["issue"]["body"] += snippet
            with self.assertRaises(module.IntentError):
                module.check(data, OWNER, REPO)
        for prop, value in [("title", "SDOA PLAN DevSreFeat incident-intake"),
                            ("number", 0), ("state", "closed")]:
            data = event()
            data["issue"][prop] = value
            with self.assertRaises(module.IntentError):
                module.check(data, OWNER, REPO)
        data = event()
        data["issue"]["pull_request"] = {}
        with self.assertRaises(module.IntentError):
            module.check(data, OWNER, REPO)

    def test_sandbox_job_never_deploys(self):
        for token in (
            "workflow_dispatch:", "types: [opened]",
            "github.actor == github.repository_owner",
            "github.event.issue.user.login == github.repository_owner",
            "github.event.sender.login == github.repository_owner",
            "github.ref == 'refs/heads/master'",
            "github.run_attempt == 1",
            "sf-incident-chatops-intent.py",
            "environment: sf-devsrefeat-read",
            "ref: ${{ github.sha }}"
        ):
            self.assertIn(token, workflow)
        for token in ("pull_request_target:", "sf project deploy quick", "sf project deploy start --manifest"):
            self.assertNotIn(token, workflow)
        self.assertIn("--dry-run", validator)
        self.assertIn("sf-deploy-safe-diagnostic.py", validator)
        self.assertNotIn("sf project deploy quick", validator)
        self.assertIn("startsWith(github.event.issue.title, 'SDOA PLAN ')", m5)


if __name__ == "__main__":
    unittest.main()
