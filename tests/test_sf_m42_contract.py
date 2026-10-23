"""M4.2 invariants; tests do not authenticate, deploy, or need network."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/sf-universal-m4.yml").read_text("utf-8")
SCRIPT = (ROOT / "scripts/ci/sf-general-deploy.sh").read_text("utf-8")


class M42ContractTests(unittest.TestCase):
    def test_form_is_small_and_sha_is_automatically_pinned(self):
        for text in ["options: [plan, deploy]", "options: [DevSreFeat]",
                     "options: [security-apex, clone-pipeline-lwc, clone-pipeline-apex]"]:
            self.assertIn(text, WORKFLOW)
        self.assertNotIn("baseline_sha:", WORKFLOW)
        self.assertNotIn("commit_sha:", WORKFLOW)
        self.assertIn("CONFIRMATION: ${{ inputs.confirmation }}", WORKFLOW)
        self.assertIn("ref: ${{ github.sha }}", WORKFLOW)
        self.assertIn('$(git rev-parse HEAD)', SCRIPT)
        self.assertIn('"$GITHUB_SHA"', SCRIPT)

    def test_manual_owner_master_first_attempt_registered_env(self):
        self.assertIn("workflow_dispatch:", WORKFLOW)
        self.assertNotIn("\n  push:", WORKFLOW)
        self.assertNotIn("\n  schedule:", WORKFLOW)
        self.assertIn("github.repository_owner", WORKFLOW)
        self.assertIn("github.run_attempt == 1", WORKFLOW)
        self.assertIn('[[ "$GITHUB_RUN_ATTEMPT" == 1 ]]', SCRIPT)
        self.assertIn('refs/heads/master', SCRIPT)
        self.assertIn('"$SF_INSTANCE_URL" == "$EXPECTED_INSTANCE_URL"', SCRIPT)
        self.assertIn("SF_JWT_KEY", WORKFLOW)
        self.assertIn('DEPLOY $TARGET $PACKAGE_ID', SCRIPT)

    def test_no_remote_drift_gate_or_preview_or_bypass(self):
        for removed in (
            "BASELINE_SHA", "REQUESTED_SHA", "sf project deploy preview",
            "sf project retrieve start", "git archive", "verify_remote",
            "--ignore-conflicts", "--ignore-errors", "--ignore-warnings",
            "--purge-on-delete", "destructiveChanges.xml",
        ):
            self.assertNotIn(removed, SCRIPT)
        self.assertIn("policy compare --package", SCRIPT)
        self.assertIn("SDOA_CANDIDATE_UNSAFE", SCRIPT)

    def test_dry_run_before_plan_and_before_real_deploy(self):
        dry = SCRIPT.index("sf project deploy start --dry-run --metadata-dir")
        plan = SCRIPT.index('if [[ "$OPERATION" == plan ]]; then')
        real = SCRIPT.index("sf project deploy start --metadata-dir")
        self.assertLess(dry, plan)
        self.assertLess(plan, real)
        for text in (
            "SDOA_M42_DRY_RUN_PASSED", "SDOA_M42_PLAN_OK",
            "SDOA_REAL_DEPLOY_SUCCEEDED", "SDOA_M42_DEPLOY_UNCONFIRMED",
            "SDOA_FINAL_GATE_DENIED", "SDOA_RERUN_DENIED",
            "RunSpecifiedTests", "numberTestErrors",
        ):
            self.assertIn(text, SCRIPT)

    def test_salesforce_outputs_remain_private(self):
        for text in (
            '> "$TEMP/auth.json" 2> "$TEMP/auth.err"',
            '> "$TEMP/dry.json" 2> "$TEMP/dry.err"',
            '> "$TEMP/deploy.json" 2> "$TEMP/deploy.err"',
            "umask 077", "trap cleanup EXIT",
        ):
            self.assertIn(text, SCRIPT)
        self.assertNotIn("set -x", SCRIPT)


if __name__ == "__main__":
    unittest.main()
