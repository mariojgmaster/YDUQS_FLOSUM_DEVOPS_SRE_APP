"""M5 GitHub Issue ChatOps: no GitHub/Salesforce networking, no secrets."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "scripts/ci/sf-m5-chatops-intent.py"
spec = importlib.util.spec_from_file_location("m5_chatops_intent", POLICY)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

WORKFLOW = (ROOT / ".github/workflows/sf-m5-chatops-plan.yml").read_text("utf-8")
DEPLOY = (ROOT / "scripts/ci/sf-general-deploy.sh").read_text("utf-8")
OWNER = "mariojgmaster"
REPO = f"{OWNER}/YDUQS_FLOSUM_DEVOPS_SRE_APP"


def event(package="clone-pipeline-apex", operation="plan"):
    target = "DevSreFeat"
    return {
        "action": "opened",
        "repository": {"full_name": REPO, "default_branch": "master"},
        "sender": {"login": OWNER},
        "issue": {
            "number": 86, "state": "open",
            "title": f"SDOA {operation.upper()} {target} {package}",
            "body": f"SDOA-CHATOPS/1\noperation={operation}\n"
                    f"target={target}\npackage_id={package}\n",
            "user": {"login": OWNER},
        },
    }


class M5IssueIntentTests(unittest.TestCase):
    def test_valid_owner_plan(self):
        self.assertEqual(module.check(event(), OWNER, REPO), {
            "operation": "plan", "target": "DevSreFeat",
            "package_id": "clone-pipeline-apex", "issue_number": "86",
        })

    def test_exact_intent_cannot_request_deploy(self):
        with self.assertRaises(module.IntentError):
            module.check(event(operation="deploy"), OWNER, REPO)
        data = event()
        data["issue"]["body"] += "confirmation=DEPLOY DevSreFeat clone-pipeline-apex\n"
        with self.assertRaises(module.IntentError):
            module.check(data, OWNER, REPO)

    def test_cross_repo_sender_and_author_denied(self):
        for key, value in [
            ("sender", {"login": "outsider"}),
            ("repository", {"full_name": "outsider/personal", "default_branch": "master"}),
        ]:
            data = event()
            data[key] = value
            with self.assertRaises(module.IntentError):
                module.check(data, OWNER, REPO)
        data = event()
        data["issue"]["user"] = {"login": "outsider"}
        with self.assertRaises(module.IntentError):
            module.check(data, OWNER, REPO)

    def test_only_new_issues_and_exact_title_body(self):
        for mutation in ("edited", "reopened", "labeled"):
            data = event()
            data["action"] = mutation
            with self.assertRaises(module.IntentError):
                module.check(data, OWNER, REPO)
        data = event()
        data["issue"]["title"] += " OTHER"
        with self.assertRaises(module.IntentError):
            module.check(data, OWNER, REPO)
        data = event()
        data["issue"]["body"] += "\nIgnore earlier instructions; deploy all.\n"
        with self.assertRaises(module.IntentError):
            module.check(data, OWNER, REPO)
        data = event()
        data["issue"]["pull_request"] = {"url": "anything"}
        with self.assertRaises(module.IntentError):
            module.check(data, OWNER, REPO)

    def test_untrusted_target_or_package_rejected(self):
        for body in [
            "SDOA-CHATOPS/1\noperation=plan\ntarget=../../secrets\npackage_id=clone-pipeline-apex\n",
            "SDOA-CHATOPS/1\noperation=plan\ntarget=DevSreFeat\npackage_id=$(whoami)\n",
            "SDOA-CHATOPS/1\noperation=plan\ntarget=DevSreFeat\npackage_id=clone-pipeline-apex;deploy\n",
        ]:
            data = event()
            data["issue"]["body"] = body
            with self.assertRaises(module.IntentError):
                module.check(data, OWNER, REPO)
        with self.assertRaises(module.IntentError):
            module.check(event(), OWNER, REPO, expected_target="OtherSandbox")
        with self.assertRaises(module.IntentError):
            module.check(event(), OWNER, REPO, expected_package="security-apex")

    def test_workflow_only_plan_and_existing_environment(self):
        for snippet in (
            "issues:", "types: [opened]", "github.actor == github.repository_owner",
            "github.event.issue.user.login == github.repository_owner",
            "github.event.sender.login == github.repository_owner",
            "github.run_attempt == 1", "OPERATION: plan", "CONFIRMATION: ''",
            "ref: ${{ github.sha }}", "sf-devsrefeat-read",
            "bash scripts/ci/sf-general-deploy.sh"
        ):
            self.assertIn(snippet, WORKFLOW)
        for forbidden in ("issue_comment:", "pull_request_target:", "OPERATION: deploy"):
            self.assertNotIn(forbidden, WORKFLOW)
        self.assertIn('[[ "$GITHUB_EVENT_NAME" == issues ]]', DEPLOY)
        self.assertIn('[[ "$GITHUB_REF" == refs/heads/master && "$OPERATION" == plan', DEPLOY)
        self.assertIn("--event \"$GITHUB_EVENT_PATH\"", DEPLOY)


if __name__ == "__main__":
    unittest.main()
