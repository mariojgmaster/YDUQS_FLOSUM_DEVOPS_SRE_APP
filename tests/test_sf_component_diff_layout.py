"""Contract for aligned Branch Monitor Diff: one Y scroll, independent X.
Static guard complements Jest; browser visual approval is still required.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LWC = ROOT / "force-app/main/default/lwc/devSreComponentDescriber"


class ComponentDiffLayoutTests(unittest.TestCase):
    def test_one_vertical_scroll_and_no_two_pane_mirroring(self):
        html = (LWC / "devSreComponentDescriber.html").read_text("utf-8")
        js = (LWC / "devSreComponentDescriber.js").read_text("utf-8")
        self.assertEqual(html.count('class="cd-diff-viewport"'), 1)
        self.assertEqual(html.count('class="cd-diff-pane"'), 2)
        self.assertNotIn("handleDiffPaneScroll", html)
        self.assertNotIn("handleDiffPaneScroll", js)
        self.assertIn('querySelector(".cd-diff-viewport")', js)

    def test_exact_row_geometry_for_both_panes_including_empty_cells(self):
        css = (LWC / "devSreComponentDescriber.css").read_text("utf-8")
        self.assertRegex(css, r"(?s)\.cd-diff-viewport\s*\{[^}]*overflow-y:\s*auto\s*;")
        self.assertRegex(css, r"(?s)\.cd-diff-viewport\s+\.cd-diff-pane\s*\{[^}]*overflow-x:\s*auto\s*;[^}]*overflow-y:\s*hidden\s*;")
        self.assertRegex(css, r"(?s)\.cd-diff-viewport\s+\.cd-diff-pane-lines\s+\.cd-diff-cell\s*\{[^}]*height:\s*1\.75rem\s*;")
        self.assertRegex(css, r"(?s)\.cd-diff-viewport\s+\.cd-diff-pane-lines\s+pre\s*\{[^}]*height:\s*1\.6875rem\s*;")
        html = (LWC / "devSreComponentDescriber.html").read_text("utf-8")
        self.assertEqual(
            html.count('class="cd-diff-col"') +
            html.count('class={mobileBasePaneClass}') +
            html.count('class={mobileTargetPaneClass}'), 2
        )
        self.assertIn('class={mobileBasePaneClass}', html)
        self.assertIn('class={mobileTargetPaneClass}', html)
        self.assertEqual(html.count('class="cd-diff-pane-title"'), 2)
        self.assertIn("for:each={diffBaseRows}", html)
        self.assertIn("for:each={diffTargetRows}", html)


if __name__ == "__main__":
    unittest.main()
