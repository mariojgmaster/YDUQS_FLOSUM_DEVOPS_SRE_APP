"""Guard against Branch Monitor Reader lacking tab visibility again."""
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PS = ROOT / "force-app/main/default/permissionsets/DevSreBranchMonitor_Reader.permissionset-meta.xml"
NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}

class BranchMonitorReaderPermissionsTest(unittest.TestCase):
    def test_reader_grants_apex_and_tab_visibility(self):
        root = ET.fromstring(PS.read_bytes())
        classes = [
            (item.findtext("sf:apexClass", namespaces=NS),
             item.findtext("sf:enabled", namespaces=NS))
            for item in root.findall("sf:classAccesses", NS)
        ]
        tabs = [
            (item.findtext("sf:tab", namespaces=NS),
             item.findtext("sf:visibility", namespaces=NS))
            for item in root.findall("sf:tabSettings", NS)
        ]
        self.assertIn(("DevSreBranchMonitorController", "true"), classes)
        self.assertIn(("branchMonitor", "Visible"), tabs)
        self.assertEqual(1, len(tabs))

if __name__ == "__main__":
    unittest.main()
