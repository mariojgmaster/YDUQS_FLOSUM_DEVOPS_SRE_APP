"""Offline safety tests: never print raw Salesforce error text, org data or stacktraces."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
NAME = ROOT / "scripts/ci/sf-deploy-safe-diagnostic.py"
spec = importlib.util.spec_from_file_location("sf_safe_diagnostic", NAME)
diag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diag)


def render(obj, exit_code=1, phase="DRY_RUN"):
    return diag.summarize(json.dumps(obj).encode(), exit_code, phase)


class DiagnosticsTests(unittest.TestCase):
    def test_apex_failure_counts_without_disclosing_failure_details(self):
        private = "System.AssertException: secret-internal-stacktrace"
        org = {
            "status": 1,
            "message": private,
            "result": {
                "done": True, "success": False, "status": "Failed",
                "numberTestErrors": 2, "numberComponentErrors": 0,
                "numberTestsCompleted": 5,
                "details": {
                    "runTestResult": {
                        "failures": [{"name": "PrivateInternalClass",
                                      "methodName": "privateMethod",
                                      "message": private}]
                    }
                }
            }
        }
        output = render(org)
        self.assertIn("cli_exit=1", output)
        self.assertIn("tests_run=5", output)
        self.assertIn("test_errors=2", output)
        self.assertIn("component_errors=0", output)
        self.assertIn("failure_kind=APEX_TEST_FAILURE", output)
        for private_field in ("secret-internal-stacktrace", "PrivateInternalClass",
                              "privateMethod", "System.AssertException"):
            self.assertNotIn(private_field, output)

    def test_component_failures_are_classified_without_values(self):
        value = "SF_TOKEN_and_private_org_data"
        data = {
            "status": 1,
            "result": {
                "status": "Failed", "done": True, "success": False,
                "details": {
                    "componentFailures": [
                        {"fullName": "SensitiveApex", "problem": value},
                        {"fullName": "AnotherClass", "problem": "error"}
                    ]
                }
            }
        }
        output = render(data)
        self.assertIn("component_errors=2", output)
        self.assertIn("failure_kind=METADATA_COMPONENT_FAILURE", output)
        self.assertNotIn(value, output)
        self.assertNotIn("SensitiveApex", output)

    def test_unexpected_json_and_unknown_schema_fail_closed(self):
        output = diag.summarize(b"not-valid-json WITH_SECRET", 2, "DRY_RUN")
        self.assertIn("json=invalid", output)
        self.assertNotIn("WITH_SECRET", output)
        self.assertIn("CLI_OR_JSON", output)
        self.assertIn("json=unexpected", diag.summarize(b"[]", 1, "DRY_RUN"))
        self.assertIn("failure_kind=UNCLASSIFIED", render({"status": 2, "result": {}}))
        self.assertIn("result_status=other", render({"result": {"status": "Internal Name"}}))

    def test_coverage_and_package_dependency_categories(self):
        obj = {"status": 1, "message": "Code coverage failure: secret",
               "result": {"success": False}}
        self.assertIn("failure_kind=APEX_COVERAGE", render(obj))
        obj["message"] = "Package version mismatch: PrivateSpace"
        self.assertIn("failure_kind=MANAGED_PACKAGE_DEPENDENCY", render(obj))
        self.assertNotIn("PrivateSpace", render(obj))

    def test_only_literal_fixed_shape(self):
        out = render({
            "status": 1, "name": "PrivateToken",
            "result": {"success": False, "done": True, "status": "Failed"}
        }, 1, "REAL_DEPLOY")
        self.assertTrue(out.startswith("SDOA_M42_REAL_DEPLOY_DIAG:"))
        self.assertNotIn("PrivateToken", out)
        self.assertIn("json=valid", out)


if __name__ == "__main__":
    unittest.main()
