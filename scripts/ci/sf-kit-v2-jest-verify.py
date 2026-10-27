#!/usr/bin/env python3
"""Verify that the reviewed Jest scope was actually executed, not all repository tests.

Receives private runner-local Jest JSON. Publishes only counts and fixed markers.
"""
import argparse
import json
from pathlib import Path

MAX_BYTES = 8_000_000


class JestScopeError(ValueError):
    pass


def verify(report, selected, root):
    if not selected or len(selected) > 100 or len(selected) != len(set(selected)):
        raise JestScopeError("Invalid selected suites")
    expected = set()
    prefix = (root / "force-app/main/default/lwc").resolve()
    for item in selected:
        if not isinstance(item, str) or not item.startswith("force-app/main/default/lwc/"):
            raise JestScopeError("Selected path outside approved LWC tree")
        path = (root / item).resolve()
        if not path.is_relative_to(prefix) or not path.is_file():
            raise JestScopeError("Selected Jest suite missing")
        expected.add(path)
    if not isinstance(report, dict) or report.get("success") is not True:
        raise JestScopeError("Jest reported failure")
    suites = report.get("testResults")
    if not isinstance(suites, list) or len(suites) != len(expected):
        raise JestScopeError("Jest ran a different number of suites")
    actual = set()
    for test in suites:
        if not isinstance(test, dict) or not isinstance(test.get("name"), str):
            raise JestScopeError("Unexpected Jest report shape")
        name = Path(test["name"]).resolve()
        actual.add(name)
        if test.get("status") != "passed":
            raise JestScopeError("Jest suite did not pass")
    if actual != expected:
        raise JestScopeError("Executed Jest suites differ from reviewed manifest selection")
    if (report.get("numFailedTestSuites") != 0 or report.get("numFailedTests") != 0 or
        report.get("numPassedTestSuites") != len(expected) or
        type(report.get("numPassedTests")) is not int or report["numPassedTests"] < len(expected)):
        raise JestScopeError("Jest counters are inconsistent with approved suites")
    return len(expected), report["numPassedTests"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--json", type=Path, required=True)
    p.add_argument("--selected", type=Path, required=True)
    p.add_argument("--root", type=Path, default=Path("."))
    a = p.parse_args()
    try:
        if a.json.is_symlink() or a.json.stat().st_size > MAX_BYTES:
            raise JestScopeError("Invalid JSON report file")
        if a.selected.is_symlink() or a.selected.stat().st_size > 16000:
            raise JestScopeError("Invalid selection file")
        payload = json.loads(a.json.read_text(encoding="utf-8"))
        names = [line for line in a.selected.read_text(encoding="utf-8").splitlines() if line]
        suites, tests = verify(payload, names, a.root.resolve())
        print(f"SDOA_V2_JEST_PASSED: manifest_scoped_suites={suites} tests={tests}")
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError):
        print("::error title=SDOA_V2_JEST_SCOPE_DENIED::Jest result did not match the reviewed manifest suites.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
