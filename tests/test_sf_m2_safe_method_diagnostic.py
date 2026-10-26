import importlib.util, json, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("safe",ROOT/"scripts/ci/sf-deploy-safe-diagnostic.py")
safe=importlib.util.module_from_spec(spec);spec.loader.exec_module(safe)
TEST="DevSreComponentDescriberTest"
METHOD="boundedSearchAndTypedRelationDiscovery"

class M2SafeMethodDiagnosticTests(unittest.TestCase):
    def data(self,method):
        return json.dumps({"status":1,"result":{"status":"Failed","numberTestErrors":1,"details":{
            "runTestResult":{"failures":[{"name":TEST,"methodName":method,
                "message":"SECRET FROM Salesforce and sensitive text"}]}}}})
    def test_only_repo_checked_method_can_be_disclosed(self):
        good=safe.detailed_report(self.data(METHOD),1,"DRY_RUN",{TEST},ROOT)
        self.assertEqual(good["failures"][0]["reviewed_test_method"],METHOD)
        self.assertNotIn("SECRET",str(good))
        unlisted=safe.detailed_report(self.data("secretMethod"),1,"DRY_RUN",{TEST},ROOT)
        self.assertNotIn("reviewed_test_method",unlisted["failures"][0])
        unapproved=safe.detailed_report(self.data(METHOD),1,"DRY_RUN",{"Other"},ROOT)
        self.assertNotIn("reviewed_test_method",unapproved["failures"][0])
    def test_helper_rejects_unknown_test_sources(self):
        self.assertEqual(set(),safe._reviewed_test_methods("../../secret",ROOT))

if __name__=="__main__":unittest.main()
