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

    def test_dml_status_enum_only(self):
        self.assertEqual(mod.dml_status(
            "System.DmlException: Insert failed. First exception on row 0; first error: "
            "INSUFFICIENT_ACCESS_OR_READONLY, something secret"),
            "INSUFFICIENT_ACCESS_OR_READONLY")
        self.assertEqual(mod.dml_status(
            "first error: LEAK_PRIVATE_VALUE_TOKEN, secret user id"), "OTHER")
        self.assertEqual(mod.dml_status("no known status"), "UNAVAILABLE")
        payload={"result":{"details":{"runTestResult":{"failures":[
            {"message":"System.DmlException: Insert failed; first error: "
                       "INVALID_FIELD_FOR_INSERT_UPDATE, private record 00ZZZ"}
        ]}}}}
        output="\\n".join(mod.summarize(json.dumps(payload)))
        self.assertIn("dml_code=INVALID_FIELD_FOR_INSERT_UPDATE",output)
        self.assertNotIn("private record",output)

    def test_only_whitelisted_method_and_exception(self):
        payload={"result":{"details":{"runTestResult":{"failures":[
            {"methodName":"listsRealIncidentsWithSearch",
             "message":"System.AuraHandledException: private SECRET_USER data"},
            {"methodName":"unlistedUserSecretMethod",
             "message":"System.SecretInternalException: secret TOKEN"}
        ]}}}}
        output="\\n".join(mod.summarize(json.dumps(payload)))
        self.assertIn("method=listsRealIncidentsWithSearch exception=AURA_HANDLED count=1", output)
        self.assertIn("method=UNLISTED exception=OTHER count=1", output)
        self.assertNotIn("unlistedUserSecretMethod", output)
        self.assertNotIn("SecretInternalException", output)
        self.assertNotIn("SECRET_USER", output)

    def test_setup_and_invalid_cases(self):
        data={"result":{"details":{"runTestResult":{"failures":[
            {"message":"System.DmlException: FIELD_CUSTOM_VALIDATION_EXCEPTION", "stackTrace":"Class.X.@TestSetup: line 4"}
        ]}}}}
        self.assertIn("setup_mentions=1", "\n".join(mod.summarize(json.dumps(data))))
        self.assertEqual(mod.summarize("{}"), ["INCIDENT_APEX_TEST_DIAG: results_unavailable"])
        self.assertEqual(mod.summarize("garbage"), ["INCIDENT_APEX_TEST_DIAG: json_unavailable"])


if __name__ == "__main__":
    unittest.main()
