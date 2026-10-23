#!/usr/bin/env python3
"""Print bounded, privacy-safe diagnostic facts from a Salesforce CLI deploy JSON.

Only literal enumerations, booleans and bounded counts reach public Actions logs.
Never print input values, org identifiers, Apex names, stack traces or raw errors.
"""
import argparse
import json
import re
from pathlib import Path

STATUSES = {"Succeeded", "Failed", "InProgress", "Pending", "Queued", "Canceled", "Canceling"}
MAX_RESULT_BYTES = 6_000_000


def flag(value):
    return "true" if value is True else "false" if value is False else "unknown"


def bounded_count(value):
    if type(value) is int and 0 <= value <= 100000:
        return str(value)
    return "unknown"


def item_count(value):
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict) and value:
        return 1
    return None


def classify(data, result, tests, components, coverage):
    if isinstance(tests, int) and tests > 0:
        return "APEX_TEST_FAILURE"
    if isinstance(coverage, int) and coverage > 0:
        return "APEX_COVERAGE"
    if isinstance(components, int) and components > 0:
        return "METADATA_COMPONENT_FAILURE"
    hints = [data.get("message"), data.get("name"),
             result.get("errorMessage"), result.get("errorCode")]
    details = result.get("details")
    if isinstance(details, dict):
        for key in ("componentFailures", "runTestResult"):
            entry = details.get(key)
            if isinstance(entry, dict):
                hints.extend([entry.get("message"), entry.get("name")])
    text = " ".join(str(s)[:2000] for s in hints if isinstance(s, str)).lower()
    rules = (
        ("APEX_COVERAGE", r"coverage|75 percent|75%"),
        ("APEX_TEST_FAILURE", r"apex.*test|test.*fail|run specified tests"),
        ("MANAGED_PACKAGE_DEPENDENCY", r"packageversions|package version|managed package|dependent class"),
        ("SOURCE_CONFLICT", r"source tracking|source conflict|conflict detected"),
        ("AUTHORIZATION", r"insufficient access|permission|unauthorized|authentication"),
        ("TIMEOUT_OR_PENDING", r"timed out|timeout|still in progress"),
        ("INVALID_PACKAGE", r"invalid package|invalid metadata|unknown component"),
    )
    for code, pattern in rules:
        if re.search(pattern, text):
            return code
    return "UNCLASSIFIED"


def summarize(payload, cli_exit, phase):
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeDecodeError):
        return f"SDOA_M42_{phase}_DIAG: json=invalid cli_exit={cli_exit} failure_kind=CLI_OR_JSON"
    if not isinstance(data, dict):
        return f"SDOA_M42_{phase}_DIAG: json=unexpected cli_exit={cli_exit} failure_kind=CLI_OR_JSON"
    result = data.get("result")
    if not isinstance(result, dict):
        result = {}
    details = result.get("details")
    if not isinstance(details, dict):
        details = {}
    test_result = details.get("runTestResult")
    if not isinstance(test_result, dict):
        test_result = {}
    test_fails = item_count(test_result.get("failures"))
    comp_fails = item_count(details.get("componentFailures"))
    coverage_warnings = item_count(test_result.get("codeCoverageWarnings"))
    test_errors = result.get("numberTestErrors")
    component_errors = result.get("numberComponentErrors")
    if type(test_errors) is not int:
        test_errors = test_fails
    if type(component_errors) is not int:
        component_errors = comp_fails
    tests_run = result.get("numberTestsCompleted")
    if type(tests_run) is not int:
        tests_run = test_result.get("numTestsRun")
    status = result.get("status")
    status = status if status in STATUSES else "other"
    outer_status = bounded_count(data.get("status"))
    kind = classify(data, result, test_errors, component_errors, coverage_warnings)
    return (
        f"SDOA_M42_{phase}_DIAG: json=valid cli_exit={cli_exit}"
        f" cli_status={outer_status} result_status={status}"
        f" success={flag(result.get('success'))} done={flag(result.get('done'))}"
        f" tests_run={bounded_count(tests_run)}"
        f" test_errors={bounded_count(test_errors)}"
        f" component_errors={bounded_count(component_errors)}"
        f" coverage_warnings={bounded_count(coverage_warnings)}"
        f" failure_kind={kind}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--exit", type=int, required=True)
    parser.add_argument("--phase", choices=["DRY_RUN", "REAL_DEPLOY"], required=True)
    args = parser.parse_args()
    if not 0 <= args.exit <= 255:
        print(f"SDOA_M42_{args.phase}_DIAG: invalid_exit")
        return
    try:
        if args.file.stat().st_size > MAX_RESULT_BYTES:
            raise ValueError("size")
        payload = args.file.read_bytes()
        print(summarize(payload, args.exit, args.phase))
    except (OSError, ValueError, TypeError):
        print(f"SDOA_M42_{args.phase}_DIAG: json=unavailable cli_exit={args.exit} failure_kind=CLI_OR_JSON")


if __name__ == "__main__":
    main()
