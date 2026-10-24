"""Static controls for real deploy workflow, never runs Salesforce."""
from pathlib import Path
import unittest
import json
import subprocess
import shutil

R = Path(__file__).resolve().parents[1]
W = (R / ".github/workflows/sf-devsrefeat-incidents-deploy.yml").read_text("utf-8")
S = (R / "scripts/ci/sf-incident-sandbox-deploy.sh").read_text("utf-8")

class IncidentDeploySafety(unittest.TestCase):
    def test_manual_owner_sha_and_confirmation(self):
        for x in (
            "workflow_dispatch:", "github.actor == github.repository_owner",
            "github.ref == 'refs/heads/master'", "github.run_attempt == 1",
            "environment: sf-devsrefeat-read", "ref: ${{ github.sha }}",
            "Confirmar protecao da master via API GitHub"
        ):
            self.assertIn(x,W)
        for forbidden in ("pull_request:", "issues:", "workflow_run:", "issue_comment:", "schedule:", "push:"):
            self.assertNotIn(forbidden,W)
        for x in (
            'CONFIRMATION:-}" == "DEPLOY DevSreFeat"', "REQUESTED_SHA,,",
            "EXPECTED_ATTEMPT", "EXPECTED_ACTOR", "EXPECTED_OWNER",
            "python3 scripts/ci/verify-incident-navigation-scope.py"
        ):
            self.assertIn(x,S)

    def test_single_scoped_manifest_and_two_deploys(self):
        target="manifest/sf-devops-sre-incidents-navigation.xml"
        self.assertIn(target,S)
        self.assertEqual(S.count('sf project deploy start'),2)
        self.assertIn("--dry-run",S)
        self.assertIn("RunSpecifiedTests",S)
        self.assertIn('test_class="DevSreIncidentControllerTest"',S)
        self.assertIn("numberTestsCompleted",S)
        self.assertIn("sf project deploy preview",S)
        self.assertIn('--metadata-dir "$tmp_dir/mdapi"', S)
        self.assertIn('sf-incident-navigation-stage.py', S)
        for forbidden in ("--ignore-conflicts", "sf project deploy quick", "destructiveChanges",
                          "manifest/sf-devsrefeat-m3.xml", "https://login.salesforce.com", "--target-org production"):
            self.assertNotIn(forbidden,S)


    def test_preview_parser_counts_from_same_jq_file_as_deploy(self):
        self.assertIn('jq -erf scripts/ci/incident-preview-counts.jq', S)
        self.assertIn('INCIDENT_PREVIEW_PARSE_FAILED', S)
        self.assertIn('preview_summary="$(jq', S)
        self.assertNotIn('read -r deploy_count conflict_count delete_count ignored_count < <(jq', S)
        self.assertIsNotNone(shutil.which("jq"), "jq is needed to test exact production filter")
        preview = {
            "status": 0,
            "result": {
                "toDeploy": [{"name": "safe1"}, {"name": "safe2"}],
                "conflicts": [],
                "toDelete": [],
                "ignored": []
            }
        }
        proc = subprocess.run(
            ["jq", "-erf", str(R / "scripts/ci/incident-preview-counts.jq")],
            input=json.dumps(preview), text=True, capture_output=True, check=False
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "2\t0\t0\t0")

    def test_preview_parser_nonzero_categories_and_empty_preview(self):
        inp = {
            "result": {
                "toDeploy": [],
                "conflicts": [{}],
                "toDelete": [{}, {}],
                "ignored": [{}]
            }
        }
        proc = subprocess.run(
            ["jq", "-erf", str(R / "scripts/ci/incident-preview-counts.jq")],
            input=json.dumps(inp), text=True, capture_output=True, check=False
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "0\t1\t2\t1")
        self.assertIn('sf-incident-navigation-stage.py', S)
        self.assertIn('INCIDENT_DELTA_SECURITY_FAILED', S)
        self.assertIn('--metadata-dir "$tmp_dir/mdapi"', S)

    def test_credential_safety_and_fail_closed(self):
        for x in ('chmod 600', 'trap ', 'INCIDENT_REAL_DEPLOY_UNCONFIRMED',
                  'INCIDENT_DELTA_SECURITY_FAILED', 'INCIDENT_TARGET_DENIED',
                  'INCIDENT_SAME_RUN_DRY_RUN_AND_APEX_TESTS'):
            self.assertIn(x,S)
        self.assertNotIn('cat "$tmp_dir/real.json"',S)
        self.assertNotIn("echo \"$SF_JWT_KEY\"",S)

if __name__ == "__main__":
    unittest.main()
