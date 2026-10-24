import importlib.util
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"scripts/ci/sf-incident-navigation-preview-report.py"
s=importlib.util.spec_from_file_location("preview",P)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
  def test_allowed_members_and_counts(self):
    result={"result":{"toDeploy":[{"name":"devSreIncidentsHost"}],"conflicts":[{"name":"incidentsRollbacks"},{"name":"OtherSecret"}],"ignored":[],"toDelete":[]}}
    output="\n".join(m.parse(result))
    self.assertIn("group=conflicts count=2",output)
    self.assertIn("member=incidentsRollbacks",output)
    self.assertNotIn("OtherSecret",output)
  def test_invalid_preview_fails(self):
    with self.assertRaises(ValueError): m.parse({"result":{"toDeploy":[]}})
if __name__=="__main__":unittest.main()
