import importlib.util
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
R=Path(__file__).resolve().parents[1]
p=R/"scripts/ci/sf-incident-cleanup-preflight.py"
spec=importlib.util.spec_from_file_location("cleanup",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def x(v):
    return ('<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">'
            f'<lwcComponent>{v}</lwcComponent></CustomTab>')
def inspect(original="devSreIncidentsHost",dup="devSreIncidentIntake"):
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/"tabs.zip"
        with ZipFile(path,"w") as z:
            z.writestr("unpackaged/tabs/incidentsRollbacks.tab",x(original))
            z.writestr("unpackaged/tabs/DevSre_Incident_Intake.tab",x(dup))
        m.verify_original(path)
class Tests(unittest.TestCase):
    def test_exact_scope(self):
        m.verify_manifests(R)
    def test_after_migration(self):
        inspect()
    def test_not_before_migration(self):
        with self.assertRaises(AssertionError):
            inspect(original="incidentsRollbacks")
    def test_unexpected_duplicate(self):
        with self.assertRaises(AssertionError):
            inspect(dup="SomethingElse")
if __name__=="__main__": unittest.main()
