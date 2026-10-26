import importlib.util,io,json,tempfile,unittest
from pathlib import Path
from contextlib import redirect_stdout
from zipfile import ZipFile
SPEC=importlib.util.spec_from_file_location("app_inspection",
    Path(__file__).resolve().parents[1]/"scripts/ci/sf-branch-monitor-app-inspect.py")
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)
NS="http://soap.sforce.com/2006/04/metadata"

class BranchMonitorAppInspectionTest(unittest.TestCase):
    def test_exact_owner_only(self):
        good={"action":"opened","issue":{"title":m.TITLE,"body":m.BODY,"user":{"login":"owner"}},
              "sender":{"login":"owner"},"repository":{"owner":{"login":"owner"}}}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"issue.json"
            p.write_text(json.dumps(good));m.verify_issue(p,"owner")
            good["sender"]["login"]="attacker";p.write_text(json.dumps(good))
            with self.assertRaises(m.Block):m.verify_issue(p,"owner")
            good["sender"]["login"]="owner";good["issue"]["body"]+="\noperation=deploy"
            p.write_text(json.dumps(good))
            with self.assertRaises(m.Block):m.verify_issue(p,"owner")
    def test_narrow_candidates_and_ambiguous_rejection(self):
        self.assertEqual(m.candidates([{"fullName":"irrelevant"},
            {"fullName":"DevOps_SRE_Analytics"}]),["DevOps_SRE_Analytics"])
        with self.assertRaises(m.Block):m.candidates([{"fullName":"foo"}])
        with self.assertRaises(m.Block):m.candidates([{"fullName":"analytics;" }])
    def test_real_app_selected_without_disclosing_other_xml(self):
        def payload(label,tabs):
            parts="".join("<tabs>"+x+"</tabs>" for x in tabs)
            return ('<?xml version="1.0"?><CustomApplication xmlns="'+NS+'"><label>'+
                label+'</label>'+parts+'</CustomApplication>').encode()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"apps.zip"
            with ZipFile(p,"w") as z:
                z.writestr("unpackaged/applications/DevOps_SRE_Analytics.app",
                    payload("DevOps &amp; SRE Analytics",["DORA_Cockpit","pipelineMonitor","incidentsRollbacks"]))
                z.writestr("unpackaged/applications/Other_Analytics.app",
                    payload("Other",["something"]))
            name,label,tabs,raw=m.read_target_application(p,{"DevOps_SRE_Analytics","Other_Analytics"})
            r=m.inspection_report(name,label,tabs,raw)
            self.assertEqual(r["pipeline_index_1_based"],2)
            self.assertFalse(r["branch_monitor_already_present"])
            self.assertEqual(r["tab_count"],3)
            self.assertTrue(r["label_confirmed"])
    def test_duplicates_and_missing_pipeline_fail(self):
        with self.assertRaises(m.Block):m.inspection_report("DevOps_SRE_Analytics","x",["no"],b"x")
        with self.assertRaises(m.Block):m.inspection_report("DevOps_SRE_Analytics","x",["pipelineMonitor","pipelineMonitor"],b"x")

if __name__=="__main__":unittest.main()
