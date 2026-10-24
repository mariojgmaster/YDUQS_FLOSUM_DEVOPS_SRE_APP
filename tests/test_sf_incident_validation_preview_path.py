"""Prevent mismatched preview JSON paths between CLI and metadata stager."""
from pathlib import Path
import re
import unittest

SCRIPT = (Path(__file__).resolve().parents[1] /
          "scripts/ci/sf-incident-sandbox-validate.sh").read_text("utf-8")

class NavigationPreviewPathTests(unittest.TestCase):
    def test_diagnostic_and_stage_share_same_preview(self):
        saved = re.findall(r'>\s*"\$work_dir/(nav-preview\.json)"', SCRIPT)
        self.assertEqual(saved, ["nav-preview.json"])
        self.assertIn('sf-incident-navigation-preview-report.py --file "$work_dir/nav-preview.json"', SCRIPT)
        self.assertIn('--candidate "$WORK/mdapi" --preview "$WORK/nav-preview.json"', SCRIPT)
        self.assertNotIn('--preview "$WORK/preview.json"', SCRIPT)

    def test_cli_exit_and_scope_checks_precede_stage(self):
        self.assertIn('if [[ "$nav_exit" -ne 0 ]]; then', SCRIPT)
        a=SCRIPT.index('if [[ "$nav_exit" -ne 0 ]]; then')
        b=SCRIPT.index('sf-incident-navigation-stage.py')
        self.assertLess(a,b)
        self.assertIn('sf-incident-navigation-stage.py', SCRIPT)

if __name__ == "__main__":
    unittest.main()
