"""Only privacy-safe static categories may appear in the diagnostic output."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "scripts/ci/sf-incident-component-diagnostics.py"
spec = importlib.util.spec_from_file_location("incident_diagnostics", p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SafeIncidentDiagnosticTests(unittest.TestCase):
    def test_types_and_reasons_without_exposing_messages(self):
        payload = {
            "result": {"details": {"componentFailures": [
                {"componentType": "ValidationRule", "problem": "Invalid expression API_SECRETPREFIX at line 3"},
                {"componentType": "CustomObject", "problem": "Unknown field SECRET_CUSTOM_FIELD"},
                {"componentType": "UnlistedCustomOrgObject", "problem": "secret unknown problem"}
            ]}}
        }
        output = "\n".join(module.summarize(json.dumps(payload)))
        self.assertIn("type=ValidationRule category=VALIDATION_FORMULA", output)
        self.assertIn("type=CustomObject category=FIELD_OR_REFERENCE", output)
        self.assertIn("type=Other category=UNCLASSIFIED", output)
        for forbidden in ("API_SECRETPREFIX", "SECRET_CUSTOM_FIELD", "UnlistedCustomOrgObject"):
            self.assertNotIn(forbidden, output)

    def test_single_item_and_missing_data(self):
        payload = {"result":{"details":{"componentFailures":{"componentType":"PermissionSet","problem":"Insufficient access"}}}}
        self.assertIn("type=PermissionSet category=PERMISSION_OR_SECURITY",
                      module.summarize(json.dumps(payload))[0])
        self.assertEqual(module.summarize("not json"), ["INCIDENT_COMPONENT_DIAG: json_unavailable"])
        self.assertEqual(module.summarize("{}"), ["INCIDENT_COMPONENT_DIAG: result_unavailable"])


if __name__ == "__main__":
    unittest.main()
