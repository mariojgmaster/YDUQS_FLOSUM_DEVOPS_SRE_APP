"""Safe, finite error classifications for M2 LWC deploy diagnostics."""
import importlib.util
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("safe_diag", ROOT / "scripts/ci/sf-deploy-safe-diagnostic.py")
diag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diag)

class ComponentProblemCodeTests(unittest.TestCase):
    def test_known_categories_hide_salesforce_payload(self):
        org_private = "company@corp.test 00D000000000ABC private-password"
        cases = [
            ("No MODULE named markup://c:devSreComponentDescriber " + org_private, "MISSING_LWC_MODULE"),
            ("LWC1010: Compilation failed " + org_private, "LWC_COMPILATION"),
            ("Invalid directive " + org_private, "INVALID_DIRECTIVE"),
            ("Dependency failed: " + org_private, "DEPLOY_DEPENDENCY"),
            ("Unexpected failure " + org_private, "UNCLASSIFIED_COMPONENT"),
        ]
        for problem, expected in cases:
            with self.subTest(expected=expected):
                payload = {"result": {"status": "Failed", "details": {"componentFailures": {
                    "fullName": "devSreBranchMonitor", "problem": problem, "problemType": "Error"
                }}}}
                report = diag.detailed_report(json.dumps(payload).encode(), 1, "DRY_RUN", {"devSreBranchMonitor"})
                self.assertEqual(expected, report["failures"][0]["problem_code"])
                self.assertNotIn(org_private, json.dumps(report))
                self.assertNotIn(problem, json.dumps(report))
    def test_non_text_and_unlisted_component(self):
        payload={"result":{"details":{"componentFailures":{"fullName":"PrivateOrgComponent","problem":123}}}}
        report=diag.detailed_report(json.dumps(payload).encode(),1,"DRY_RUN",set())
        self.assertEqual("<unlisted>",report["failures"][0]["reviewed_component_or_test_class"])
        self.assertEqual("NO_MESSAGE",report["failures"][0]["problem_code"])

if __name__ == "__main__":
    unittest.main()
