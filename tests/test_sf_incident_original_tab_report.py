import importlib.util
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "scripts/ci/sf-incident-original-tab-report.py"
spec = importlib.util.spec_from_file_location("incident_tab_report", p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def make_tab(label, ref_tag=None, ref_val=None):
    ref = f"<{ref_tag}>{ref_val}</{ref_tag}>" if ref_tag else ""
    return (f'<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">'
            f'<label>{label}</label>{ref}</CustomTab>').encode()


class NavDiscoveryTests(unittest.TestCase):
    def test_matching_original_and_not_leaking_unrelated_tabs(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "meta.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr("unpackaged/tabs/ExistingOps.tab",
                                 make_tab("Incidents &amp; Rollbacks", "flexiPage", "ExistingIncidentsPage"))
                archive.writestr("unpackaged/tabs/SecretFinance.tab",
                                 make_tab("Finance Data SECRET", "lwcComponent", "SensitiveCode"))
                archive.writestr("unpackaged/tabs/DevSre_Incident_Intake.tab",
                                 make_tab("Incidentes &amp; Recuperações", "lwcComponent", "devSreIncidentIntake"))
            matches, candidates = mod.detect(path)
            output = "\n".join(mod.format_lines(matches, candidates))
            self.assertIn("api=ExistingOps flexiPage=ExistingIncidentsPage", output)
            self.assertIn("api=DevSre_Incident_Intake", output)
            self.assertNotIn("Finance", output)
            self.assertNotIn("SensitiveCode", output)
            self.assertEqual(len(matches), 2)

    def test_fallback_candidate_and_reject_sensitive_identifiers(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "meta.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr("unpackaged/tabs/IncidentOperations.tab",
                                 make_tab("Operations", "auraComponent", "Component$unsafe"))
                archive.writestr("unpackaged/tabs/Other.tab",
                                 make_tab("Other"))
            matches, candidates = mod.detect(path)
            output = "\n".join(mod.format_lines(matches, candidates))
            self.assertIn("api=IncidentOperations ref=not-in-tab-metadata", output)
            self.assertNotIn("Component$unsafe", output)
            self.assertEqual(len(matches), 0)


if __name__ == "__main__":
    unittest.main()
