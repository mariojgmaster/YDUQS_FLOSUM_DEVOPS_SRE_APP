import importlib.util,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
P=Path(__file__).resolve().parents[1]/"scripts/ci/sf-branch-monitor-reader-verify.py"
s=importlib.util.spec_from_file_location("reader",P)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
NS="http://soap.sforce.com/2006/04/metadata"
def xml(tab="Visible",apex="true",extra=""):
    return ('<?xml version="1.0"?><PermissionSet xmlns="'+NS+'">'
        '<label>DevOps SRE - Leitura Branch Monitor</label>'
        '<classAccesses><apexClass>DevSreBranchMonitorController</apexClass><enabled>'+apex+'</enabled></classAccesses>'
        '<tabSettings><tab>branchMonitor</tab><visibility>'+tab+'</visibility></tabSettings>'
        +extra+'</PermissionSet>').encode()
class ReaderReadbackTests(unittest.TestCase):
    def test_scoped_readback_accepts_extra_metadata_without_leaking(self):
        doc=xml(extra='<userPermissions><enabled>true</enabled><name>ViewSetup</name></userPermissions>')
        result=m.parse_permission_set(doc)
        self.assertTrue(result["tab_visible"])
        self.assertTrue(result["apex_enabled"])
        self.assertNotIn("ViewSetup",str(result))
    def test_hidden_and_inactive_are_not_verified(self):
        self.assertFalse(m.parse_permission_set(xml(tab="Hidden"))["tab_visible"])
        self.assertFalse(m.parse_permission_set(xml(apex="false"))["apex_enabled"])
        with self.assertRaises(m.Block):m.parse_permission_set(xml(extra='<tabSettings><tab>branchMonitor</tab><visibility>Hidden</visibility></tabSettings>'))
    def test_archive_member_must_be_unambiguous(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"result.zip"
            with ZipFile(f,"w") as z:z.writestr("unpackaged/permissionsets/DevSreBranchMonitor_Reader.permissionset",xml())
            self.assertTrue(m.parse_archive(f)["tab_visible"])
            with ZipFile(f,"a") as z:z.writestr("unpackaged/permissionsets/DevSreBranchMonitor_Reader.permissionset-meta.xml",xml())
            with self.assertRaises(m.Block):m.parse_archive(f)
    def test_exact_owner_authentication(self):
        e={"action":"opened","issue":{"title":m.TITLE,"body":m.BODY,"user":{"login":"owner"}},
           "sender":{"login":"owner"},"repository":{"owner":{"login":"owner"}}}
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"issue.json";p.write_text(json.dumps(e));m.verify_issue(p,"owner")
            e["sender"]["login"]="attacker";p.write_text(json.dumps(e))
            with self.assertRaises(m.Block):m.verify_issue(p,"owner")
if __name__=="__main__":unittest.main()
