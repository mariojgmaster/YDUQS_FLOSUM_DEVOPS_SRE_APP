"""Focused source-integrity regression for ClonePipelineController, without an org."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "force-app/main/default/classes/ClonePipelineController.cls").read_text(encoding="utf-8")


class ClonePipelineApexIntegrityTests(unittest.TestCase):
    def test_suffix_regex_is_complete_and_bounded_to_end_of_name(self):
        self.assertIn(
            "Pattern copySuffix = Pattern.compile('(?i) - Cópia(?: [0-9]{1,4})?$');",
            SRC,
        )
        self.assertIn("Matcher suffixMatcher = copySuffix.matcher(baseName);", SRC)
        pattern = re.compile(r"(?i) - Cópia(?: [0-9]{1,4})?$")
        self.assertTrue(pattern.search("Pipeline A - Cópia 02"))
        self.assertTrue(pattern.search("Pipeline A - Cópia"))
        self.assertFalse(pattern.search("Pipeline A - Cópia XYZ"))
        self.assertFalse(pattern.search("Pipeline A - Cópia 12345"))

    def test_single_exception_handler_and_no_interrupted_method(self):
        self.assertEqual(
            SRC.count("private static AuraHandledException toHandledException("),
            1,
        )
        a = SRC.index("private static String buildSuggestedName(")
        b = SRC.index("private static AuraHandledException toHandledException(", a)
        segment = SRC[a:b]
        self.assertEqual(segment.count("Pattern.compile("), 1)
        self.assertIn("return copyPrefix + ' ' + ordinal;", segment)
        self.assertIn("  }\n\n", segment[-15:])

    def test_preview_avoids_reserved_apex_number_identifier(self):
        # Apex reserves "number": protect the DTO and its consumers against regression.
        self.assertNotRegex(SRC, r"\b(?:Decimal|Integer)\s+number\s*\{")
        self.assertIn("public Decimal stepNumber { get; set; }", SRC)
        self.assertIn("step.stepNumber = readableFields.contains", SRC)
        apex_tests = (
            ROOT / "force-app/main/default/classes/ClonePipelineControllerTest.cls"
        ).read_text(encoding="utf-8")
        lwc = (
            ROOT / "force-app/main/default/lwc/clonePipelineAction/clonePipelineAction.js"
        ).read_text(encoding="utf-8")
        self.assertIn("preview.steps[0].stepNumber", apex_tests)
        self.assertIn("step.stepNumber == null", lwc)

    def test_apex_body_has_balanced_blocks_after_removing_string_literals(self):
        # Lightweight structural sanity check only; Salesforce validates Apex syntax.
        clean = re.sub(r"'(?:\\.|[^'\\])*'", "''", SRC)
        clean = re.sub(r"//[^\n]*", "", clean)
        depth = 0
        for char in clean:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                self.assertGreaterEqual(depth, 0)
        self.assertEqual(depth, 0)


if __name__ == "__main__":
    unittest.main()
