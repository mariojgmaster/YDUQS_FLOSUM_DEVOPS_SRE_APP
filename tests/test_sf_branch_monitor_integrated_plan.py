import hashlib,importlib.util,json,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location("bm_integrated",
    Path(__file__).resolve().parents[1]/"scripts/ci/sf-branch-monitor-integrated-plan.py")
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)
ROOT=Path(__file__).resolve().parents[1]

class BranchIntegratedPlanTest(unittest.TestCase):
    def app(self,tabs=None):
        root=ET.Element(m.NS+"CustomApplication")
        ET.SubElement(root,m.NS+"label").text=m.LABEL
        ET.SubElement(root,m.NS+"description").text="Do not overwrite this setting"
        for name in tabs or ["doraCockpit","pipelineMonitor","leadTimeTracker","incidentsRollbacks"]:
            ET.SubElement(root,m.NS+"tabs").text=name
        ET.SubElement(root,m.NS+"formFactors").text="Large"
        return ET.tostring(root,encoding="utf-8")
    def test_exact_owner_issue_no_mutation(self):
        e={"action":"opened","issue":{"title":m.TITLE,"body":m.BODY,
            "user":{"login":"owner"}},"sender":{"login":"owner"},
            "repository":{"owner":{"login":"owner"}}}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"e.json";p.write_text(json.dumps(e))
            m.verify_issue(p,"owner")
            e["issue"]["body"]+="\noperation=deploy";p.write_text(json.dumps(e))
            with self.assertRaises(m.Block):m.verify_issue(p,"owner")
    def test_patch_inserts_only_branch_and_preserves_unrelated_app_settings(self):
        raw=self.app();sha=hashlib.sha256(raw).hexdigest()
        with patch.object(m,"EXPECTED_APP_SHA",sha):
            modified=m.patch_app(raw)
        before=ET.fromstring(raw);after=ET.fromstring(modified)
        self.assertEqual([e.text for e in after.findall(m.NS+"tabs")],
            ["doraCockpit","branchMonitor","pipelineMonitor","leadTimeTracker","incidentsRollbacks"])
        self.assertEqual(before.findtext(m.NS+"description"),after.findtext(m.NS+"description"))
        self.assertEqual(before.findtext(m.NS+"formFactors"),after.findtext(m.NS+"formFactors"))
    def test_app_drift_and_invalid_order_blocked(self):
        raw=self.app()
        with self.assertRaises(m.Block):m.patch_app(raw)
        with patch.object(m,"EXPECTED_APP_SHA",hashlib.sha256(raw).hexdigest()):
            with self.assertRaises(m.Block):m.patch_app(raw+b" ")
        already=self.app(["doraCockpit","branchMonitor","pipelineMonitor","incidentsRollbacks"])
        with patch.object(m,"EXPECTED_APP_SHA",hashlib.sha256(already).hexdigest()):
            with self.assertRaises(m.Block):m.patch_app(already)
    def test_manifests_are_closed_and_staging_not_expansible(self):
        m.check_manifest(ROOT/m.SRC_MANIFEST)
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"package.xml";m.write_manifest(out)
            self.assertEqual(m.members(out.read_bytes()),m.TARGET_TYPES)
            rogue=out.read_bytes().replace(b"branchMonitor",b"accountExplorer")
            self.assertNotEqual(m.members(rogue),m.TARGET_TYPES)
    def test_app_only_exact_metadata_shape(self):
        with tempfile.TemporaryDirectory() as d:
            from zipfile import ZipFile
            p=Path(d)/"app.zip"
            with ZipFile(p,"w") as z:z.writestr("unpackaged/applications/"+m.APP+".app",self.app())
            self.assertTrue(m.extract_app(p))
            with ZipFile(p,"a") as z:z.writestr("unpackaged/applications/"+m.APP+".app",self.app())
            with self.assertRaises(m.Block):m.extract_app(p)

if __name__=="__main__":unittest.main()
