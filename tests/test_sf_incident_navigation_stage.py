import importlib.util,json,tempfile,unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("stager",R/"scripts/ci/sf-incident-navigation-stage.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
NS="http://soap.sforce.com/2006/04/metadata"
def tab(ref):
    return f'<CustomTab xmlns="{NS}"><label>Incidents &amp; Rollbacks</label><lwcComponent>{ref}</lwcComponent><motif>Custom20: Cup</motif></CustomTab>'
class Tests(unittest.TestCase):
    def test_preview_expected_conflicts(self):
        m.check_preview({"status":0,"result":{"toDeploy":[{"apiName":"devSreIncidentsHost"}],"conflicts":[{"apiName":"incidentsRollbacks"},{"apiName":"DevSreIncidentControllerTest"}],"toDelete":[],"ignored":[]}})
    def test_preview_without_status_cli_exit_checked_in_workflows(self):
        m.check_preview({"result":{"toDeploy":[{"name":"devSreIncidentsHost"}],"conflicts":[{"name":"incidentsRollbacks"},{"name":"DevSreIncidentControllerTest"}],"toDelete":[],"ignored":[]}})
        # CLI exit code and scoped member list are authoritative; status may
        # report source tracking conflicts, not metadata deployment failure.
        m.check_preview({"status":1,"result":{"toDeploy":[{"name":"devSreIncidentsHost"}],"conflicts":[{"name":"incidentsRollbacks"},{"name":"DevSreIncidentControllerTest"}],"toDelete":[],"ignored":[]}})

    def test_preview_refuses_extra_conflicts(self):
        with self.assertRaises(AssertionError):
            m.check_preview({"status":0,"result":{"toDeploy":[{"apiName":"devSreIncidentsHost"}],"conflicts":[{"apiName":"Secret"}],"toDelete":[],"ignored":[]}})
    def test_original_fields_survive(self):
        cls=(R/"force-app/main/default/classes/DevSreIncidentControllerTest.cls").read_text("utf-8")
        a=cls.index(m.START);b=cls.index(m.END,a);old=cls[:a]+m.OLD+cls[b:]
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); t=base/"tabs.zip";c=base/"class.zip";d=base/"candidate"
            (d/"tabs").mkdir(parents=True);(d/"classes").mkdir()
            (d/"lwc/devSreIncidentsHost").mkdir(parents=True)
            (d/"package.xml").write_text(f'<Package xmlns="{NS}"><types><members>DevSreIncidentControllerTest</members><name>ApexClass</name></types><types><members>devSreIncidentsHost</members><name>LightningComponentBundle</name></types><types><members>incidentsRollbacks</members><name>CustomTab</name></types></Package>')
            (d/"tabs/incidentsRollbacks.tab").write_text(tab("devSreIncidentsHost"))
            (d/"classes/DevSreIncidentControllerTest.cls").write_text(cls)
            (d/"classes/DevSreIncidentControllerTest.cls-meta.xml").write_text("")
            (d/"lwc/devSreIncidentsHost/devSreIncidentsHost.js-meta.xml").write_text("")
            with ZipFile(t,"w") as z:z.writestr("unpackaged/tabs/incidentsRollbacks.tab",tab("incidentsRollbacks"))
            with ZipFile(c,"w") as z:z.writestr("unpackaged/classes/DevSreIncidentControllerTest.cls",old)
            v=base/"preview.json";v.write_text(json.dumps({"status":0,"result":{"toDeploy":[{"name":"devSreIncidentsHost"}],"conflicts":[{"name":"incidentsRollbacks"},{"name":"DevSreIncidentControllerTest"}],"toDelete":[],"ignored":[]}}))
            m.stage(str(t),str(c),str(d),str(v))
            root=ET.parse(d/"tabs/incidentsRollbacks.tab").getroot()
            self.assertEqual(root.findtext("{"+NS+"}motif"),"Custom20: Cup")
            self.assertEqual(root.findtext("{"+NS+"}lwcComponent"),"devSreIncidentsHost")
if __name__=="__main__":unittest.main()
