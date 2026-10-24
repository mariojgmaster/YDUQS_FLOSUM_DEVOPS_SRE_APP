import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
source = ROOT/"scripts/ci/sf-incident-apex-test-diagnostics.py"
spec = importlib.util.spec_from_file_location("incident_apex_diag", source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ApexFailurePrivacyTests(unittest.TestCase):
    def test_classification_and_scrubbing(self):
        payload = {"result":{"details":{"runTestResult":{"failures":[
            {"name":"DoNotPublishTestClass","methodName":"sensitiveMethod","message":"System.DmlException: REQUIRED_FIELD_MISSING, SECRET_TOKEN_TEXT", "stackTrace":"at secret org"},
            {"type":"System.QueryException","message":"List has no rows for assignment to SObject, private username"},
            {"type":"System.AssertException","message":"Assertion Failed: PRIVATE_SFID"}
        ]}}}}
        rows=mod.summarize(json.dumps(payload))
        output="\n".join(rows)
        for expected in ("REQUIRED_FIELD_MISSING", "QUERY_NO_ROWS", "ASSERTION"):
            self.assertIn(expected, output)
        for forbidden in ("DoNotPublishTestClass", "sensitiveMethod", "SECRET_TOKEN_TEXT", "private username", "PRIVATE_SFID"):
            self.assertNotIn(forbidden, output)

    def test_setup_and_invalid_cases(self):
        data={"result":{"details":{"runTestResult":{"failures":[
            {"message":"System.DmlException: FIELD_CUSTOM_VALIDATION_EXCEPTION", "stackTrace":"Class.X.@TestSetup: line 4"}
        ]}}}}
        self.assertIn("setup_mentions=1", "\n".join(mod.summarize(json.dumps(data))))
        self.assertEqual(mod.summarize("{}"), ["INCIDENT_APEX_TEST_DIAG: results_unavailable"])
        self.assertEqual(mod.summarize("garbage"), ["INCIDENT_APEX_TEST_DIAG: json_unavailable"])


if __name__ == "__main__":
    unittest.main()
