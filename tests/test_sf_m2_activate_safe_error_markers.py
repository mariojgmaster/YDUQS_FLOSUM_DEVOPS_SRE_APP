"""Public-safe diagnostic markers never return untrusted Salesforce values."""
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("diag",ROOT/"scripts/ci/sf-deploy-safe-diagnostic.py")
diag=importlib.util.module_from_spec(s);s.loader.exec_module(diag)
class MarkerTests(unittest.TestCase):
    def test_fixed_dictionary_and_no_identifiers(self):
        problem="Custom markUp file failed to update MyPrivateComponent company@corp.example 00D000000000001 token_secret"
        out=diag._safe_component_problem_markers(problem)
        self.assertIn("markup",out)
        self.assertIn("update",out)
        self.assertIn("failed",out)
        self.assertNotIn("myprivatecomponent",out)
        for private in ("corp","example","secret","token","00D000000000001"):
            self.assertNotIn(private,json.dumps(out))
    def test_integration_and_malformed(self):
        payload={"result":{"details":{"componentFailures":{"fullName":"devSreBranchMonitor","message":"Invalid markup and unknown Lightning property privateOrgValue"}}}}
        x=diag.detailed_report(json.dumps(payload).encode(),1,"DRY_RUN",{"devSreBranchMonitor"})
        f=x["failures"][0]
        self.assertEqual("message",f["message_source"])
        self.assertIn("invalid",f["problem_markers"])
        self.assertIn("markup",f["problem_markers"])
        self.assertNotIn("privateOrgValue",json.dumps(x))
        self.assertEqual([],diag._safe_component_problem_markers(7))
if __name__=="__main__":unittest.main()
