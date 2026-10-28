"""Regression guard for the Branch Monitor V3.4 mobile responsive layout.

CSS pixel geometry must still be manually verified in Salesforce at 360/390/768px.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LWC = ROOT / "force-app/main/default/lwc/devSreComponentDescriber"


class ComponentMobileLayoutTests(unittest.TestCase):
    def test_mobile_inventory_cards_keep_semantic_table_and_headings(self):
        html = (LWC / "devSreComponentDescriber.html").read_text("utf-8")
        css = (LWC / "devSreComponentDescriber.css").read_text("utf-8")
        self.assertIn("<table class=\"cd-table\">", html)
        self.assertEqual(html.count('class="cd-mobile-field-label"'), 5)
        self.assertIn(".cd-table tbody tr{display:grid", css)
        self.assertIn(".cd-table thead{position:absolute", css)
        self.assertIn("@media (max-width:48rem)", css)

    def test_mobile_diff_switch_preserves_the_single_vertical_scroll(self):
        html = (LWC / "devSreComponentDescriber.html").read_text("utf-8")
        css = (LWC / "devSreComponentDescriber.css").read_text("utf-8")
        js = (LWC / "devSreComponentDescriber.js").read_text("utf-8")
        self.assertEqual(html.count('class="cd-diff-viewport"'), 1)
        self.assertEqual(html.count('class="cd-diff-pane"'), 2)
        self.assertIn('class={mobileBasePaneClass}', html)
        self.assertIn('class={mobileTargetPaneClass}', html)
        self.assertIn('aria-pressed={mobileBaseSelected}', html)
        self.assertIn('aria-pressed={mobileTargetSelected}', html)
        self.assertIn(".cd-diff-viewport .cd-diff-col_mobile-hidden{display:none}", css)
        self.assertIn("overflow-y:hidden", css)
        self.assertNotIn("handleDiffPaneScroll", js)

    def test_mobile_breakpoint_and_reduced_motion_remain_operational(self):
        css = (LWC / "devSreComponentDescriber.css").read_text("utf-8")
        js = (LWC / "devSreComponentDescriber.js").read_text("utf-8")
        self.assertIn('window.matchMedia("(max-width: 48rem)")', js)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn(".cd-archive-preview,.cd-layout_focus .cd-archive-preview", css)
        self.assertIn(".cd-workspace-nav{display:grid", css)


if __name__ == "__main__":
    unittest.main()
