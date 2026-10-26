"""SPEC-006: protect the existing Lightning Component Tab target during M2 upgrades."""
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {"md": "http://soap.sforce.com/2006/04/metadata"}
COMPONENT = ROOT / "force-app/main/default/lwc/devSreBranchMonitor/devSreBranchMonitor.js-meta.xml"
MANIFEST = ROOT / "manifest/sf-branch-monitor-m2-activate.xml"

class BranchMonitorTabTargetRegression(unittest.TestCase):
    def test_existing_tab_and_app_page_targets_remain_exposed(self):
        root = ET.parse(COMPONENT).getroot()
        self.assertEqual("{http://soap.sforce.com/2006/04/metadata}LightningComponentBundle", root.tag)
        self.assertEqual("true", root.findtext("md:isExposed", namespaces=NS))
        self.assertEqual(
            {"lightning__Tab", "lightning__AppPage"},
            {node.text for node in root.findall("md:targets/md:target", NS)}
        )

    def test_activation_manifest_only_contains_existing_lwc_shell(self):
        root = ET.parse(MANIFEST).getroot()
        types = root.findall("md:types", NS)
        self.assertEqual(1, len(types))
        self.assertEqual("LightningComponentBundle", types[0].findtext("md:name", namespaces=NS))
        self.assertEqual(["devSreBranchMonitor"],
                         [m.text for m in types[0].findall("md:members", NS)])
        self.assertEqual("67.0", root.findtext("md:version", namespaces=NS))

if __name__ == "__main__":
    unittest.main()
