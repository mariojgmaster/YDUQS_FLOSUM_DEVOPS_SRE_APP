"""Privacy and completeness tests for public-safe Salesforce diagnostic artifacts."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("safe_report", ROOT / "scripts/ci/sf-deploy-safe-diagnostic.py")
diag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diag)


class SafeReportTests(unittest.TestCase):
    def test_all_failures_enumerated_but_messages_and_secrets_never_leak(self):
        sensitive = "JWT_secret_email@corp.com 00D000000000001XYZ"
        payload = {
            "status": 1,
            "result": {
                "status": "Failed", "success": False, "done": True,
                "numberComponentErrors": 2, "numberTestErrors": 1, "numberTestsCompleted": 1,
                "details": {
                    "componentFailures": [
                        {"fullName": "ClonePipelineController", "problem": sensitive,
                         "lineNumber": 31, "columnNumber": 2, "problemType": "Error"},
                        {"fullName": "OrgSecretClass", "problem": sensitive,
                         "lineNumber": 40, "columnNumber": 5, "problemType": "Error"}
                    ],
                    "runTestResult": {"failures": [
                        {"name": "ClonePipelineControllerTest", "methodName": "privateMethod",
                         "message": sensitive, "stackTrace": sensitive}
                    ]}
                }
            }
        }
        report = diag.detailed_report(json.dumps(payload).encode(), 1, "DRY_RUN",
                                      {"ClonePipelineController", "ClonePipelineControllerTest"})
        self.assertEqual(report["enumerated_failures"], 3)
        self.assertEqual(report["component_error_count"], 2)
        self.assertEqual(report["test_error_count"], 1)
        self.assertEqual(report["tests_completed"], 1)
        serialized = json.dumps(report)
        for secret in (sensitive, "OrgSecretClass", "privateMethod", "00D000000000001XYZ",
                       "stackTrace", "problem", "JWT_secret"):
            self.assertNotIn(secret, serialized)
        self.assertIn("ClonePipelineControllerTest", serialized)
        self.assertIn("<unlisted>", serialized)
        self.assertFalse(report["raw_salesforce_payload_included"])

    def test_manifest_resolves_reviewed_members_only(self):
        allowed = diag._allowed_names("clone-pipeline-apex",
                                     ROOT / "config/salesforce-devops/catalog.json", ROOT)
        self.assertIn("ClonePipelineController", allowed)
        self.assertIn("ClonePipelineControllerTest", allowed)
        self.assertNotIn("OrgSecretClass", allowed)

    def test_malformed_json_no_untrusted_content(self):
        payload = b"private.com password=secret"
        report = diag.detailed_report(payload, 1, "DRY_RUN", set())
        self.assertEqual(report["status"], "invalid-json")
        self.assertNotIn("private.com", json.dumps(report))
        self.assertNotIn("secret", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
