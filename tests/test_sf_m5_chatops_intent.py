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
SHA = "a" * 40
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

    def test_deploy_needs_immutable_sha_and_exact_confirmation(self):
        data = event(operation="deploy")
        data["issue"]["body"] = (
            "SDOA-CHATOPS/2\noperation=deploy\ntarget=DevSreFeat\n"
            "package_id=clone-pipeline-apex\ncommit_sha=" + SHA + "\n"
            "confirmation=DEPLOY DevSreFeat clone-pipeline-apex\n"
        )
        outcome = module.check(data, OWNER, REPO, expected_sha=SHA)
        self.assertEqual(outcome["operation"], "deploy")
        self.assertEqual(outcome["commit_sha"], SHA)
        self.assertEqual(outcome["confirmation"], "DEPLOY DevSreFeat clone-pipeline-apex")
        for changed_sha in (None, "b" * 40, ""):
            with self.assertRaises(module.IntentError):
                module.check(data, OWNER, REPO, expected_sha=changed_sha)
        for injected in ("confirmation=DEPLOY OTHER", "commit_sha=INJECT", "package_id=INJECT"):
            altered = dict(data, issue=dict(data["issue"]))
            key = injected.split("=")[0] + "="
            altered["issue"]["body"] = data["issue"]["body"].replace(key, injected + " ", 1)
            with self.assertRaises(module.IntentError):
                module.check(altered, OWNER, REPO, expected_sha=SHA)

    def test_plan_remains_plan_only(self):
        data = event()
        data["issue"]["body"] += "confirmation=DEPLOY DevSreFeat clone-pipeline-apex\n"
        with self.assertRaises(module.IntentError):
            module.check(data, OWNER, REPO)
        data = event(operation="deploy")  # version 1 is not authorized for deploy
        with self.assertRaises(module.IntentError):
            module.check(data, OWNER, REPO, expected_sha=SHA)

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

    def test_workflow_explicit_deploy_and_existing_environment(self):
        for snippet in (
            "issues:", "types: [opened]", "github.actor == github.repository_owner",
            "github.event.issue.user.login == github.repository_owner",
            "github.event.sender.login == github.repository_owner",
            "github.run_attempt == 1", "OPERATION: " + "$" + "{{ needs.resolve.outputs.operation }}",
            "CONFIRMATION: " + "$" + "{{ needs.resolve.outputs.confirmation }}",
            "ref: ${{ github.sha }}", "sf-devsrefeat-read",
            "bash scripts/ci/sf-general-deploy.sh", "SDOA_M5_DEPLOY_SUCCEEDED", "upload-artifact@v4"
        ):
            self.assertIn(snippet, WORKFLOW)
        for forbidden in ("issue_comment:", "pull_request_target:", "OPERATION: deploy"):
            self.assertNotIn(forbidden, WORKFLOW)
        self.assertIn('[[ "$GITHUB_EVENT_NAME" == issues ]]', DEPLOY)
        self.assertIn("SDOA_M5_INTENT_DENIED", DEPLOY)
        self.assertIn("--event \"$GITHUB_EVENT_PATH\"", DEPLOY)
        self.assertIn("--operation \"$OPERATION\" --commit-sha \"$GITHUB_SHA\"", DEPLOY)


if __name__ == "__main__":
    unittest.main()
