#!/usr/bin/env python3
"""Print bounded facts plus safe enumerated failure records from a Salesforce CLI JSON.

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



def _items(entry):
    """Salesforce may encode a single failure as a dict, or many as a list."""
    if isinstance(entry, list):
        return [x for x in entry if isinstance(x, dict)]
    if isinstance(entry, dict):
        return [entry]
    return []


def _positive_integer(entry):
    return entry if type(entry) is int and 0 <= entry <= 1000000 else None


def _safe_enum(value, allowed):
    return value if isinstance(value, str) and value in allowed else "unspecified"


def _allowed_names(package, catalog_path, manifest_base):
    """Only source-controlled package members/test classes may appear by name."""
    import xml.etree.ElementTree as ET
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        config = catalog["packages"][package]
        tests = set(config["tests"])
        manifest = manifest_base / config["manifest"]
        root = ET.parse(manifest).getroot()
        members = set()
        for node in root.iter():
            if node.tag.endswith("members") and node.text and "*" not in node.text:
                members.add(node.text.strip())
        return members | tests
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError):
        return set()


def _reviewed_test_methods(test_class, root):
    """Report only method identifiers that literally exist in a reviewed Apex test."""
    if not isinstance(test_class,str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*Test",test_class):
        return set()
    source = root / "force-app" / "main" / "default" / "classes" / (test_class+".cls")
    try:
        body = source.read_text(encoding="utf-8")
        if len(body)>200_000: return set()
        return set(re.findall(r"@IsTest\s+static\s+void\s+([A-Za-z][A-Za-z0-9_]*)\s*\(", body))
    except (OSError,ValueError):
        return set()



def _safe_component_problem_code(problem):
    """Return a fixed public-safe error category without logging org-origin text."""
    if not isinstance(problem, str):
        return "NO_MESSAGE"
    checks = (
        ("MISSING_LWC_MODULE", r"no module named|cannot find module|failed to resolve.*module|unable to resolve.*module|module.*not found"),
        ("MISSING_COMPONENT_REFERENCE", r"(component|bundle|reference).*(not found|does not exist|unknown|missing)|cannot find.*component"),
        ("LWC_COMPILATION", r"\\blwc[0-9]{3,5}\\b|compil(e|ation|er)|syntax error|parsing error|parse error"),
        ("INVALID_TEMPLATE", r"invalid.*template|template.*invalid|markup.*invalid|unexpected.*tag"),
        ("INVALID_DIRECTIVE", r"invalid.*directive|unsupported.*directive|directive.*not supported"),
        ("DEPLOY_DEPENDENCY", r"dependenc(y|ies)|dependent|cannot resolve|unresolved"),
        ("API_VERSION", r"api.?version|api level"),
        ("ACCESS_OR_VISIBILITY", r"insufficient.*access|permission|not authorized|not visible|not accessible"),
        ("INVALID_COMPONENT", r"invalid component|invalid attribute|unknown property|not a valid component"),
    )
    for label, pattern in checks:
        if re.search(pattern, problem, flags=re.IGNORECASE):
            return label
    return "UNCLASSIFIED_COMPONENT"


def detailed_report(payload, cli_exit, phase, allowed_names, method_root=None):
    """Full *enumeration* of failure records, not full raw org data.

    No messages, stack traces, org URLs, IDs, arbitrary names, file paths,
    Apex source, tokens, record values, or unreviewed component names survive.
    """
    report = {
        "schema": "SDOA-SAFE-DIAG/1", "phase": phase,
        "cli_exit": cli_exit, "status": "unknown",
        "summary": summarize(payload, cli_exit, phase),
        "failures": [], "coverage_warning_count": 0,
        "raw_salesforce_payload_included": False,
    }
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeDecodeError):
        report["status"] = "invalid-json"
        return report
    if not isinstance(data, dict):
        report["status"] = "unexpected-json"
        return report
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    report["status"] = _safe_enum(result.get("status"), STATUSES)
    details = result.get("details") if isinstance(result.get("details"), dict) else {}
    tests = details.get("runTestResult") if isinstance(details.get("runTestResult"), dict) else {}
    warnings = _items(tests.get("codeCoverageWarnings"))
    report["coverage_warning_count"] = len(warnings)
    kinds = [
        ("component", _items(details.get("componentFailures"))),
        ("apex_test", _items(tests.get("failures"))),
    ]
    for kind, failures in kinds:
        for index, item in enumerate(failures, 1):
            # The "problem" and "message" strings are never copied to any report.
            original = item.get("fullName") if kind == "component" else item.get("name")
            if not isinstance(original, str):
                original = ""
            candidate = original.strip()
            if candidate not in allowed_names:
                candidate = "<unlisted>"
            record = {
                "category": kind, "ordinal": index,
                "reviewed_component_or_test_class": candidate,
                "line": _positive_integer(item.get("lineNumber")),
                "column": _positive_integer(item.get("columnNumber")),
            }
            if kind == "apex_test" and method_root is not None:
                test_class = item.get("name")
                method = item.get("methodName")
                if not isinstance(method,str):
                    method = item.get("method")
                if test_class in allowed_names and isinstance(method,str) and (
                        method in _reviewed_test_methods(test_class,method_root)):
                    record["reviewed_test_method"] = method
            if kind == "component":
                record["problem_type"] = _safe_enum(
                    item.get("problemType"), {"Error", "Warning", "error", "warning"}
                )
                record["problem_code"] = _safe_component_problem_code(
                    item.get("problem") if isinstance(item.get("problem"), str)
                    else item.get("message")
                )
            report["failures"].append(record)
    report["enumerated_failures"] = len(report["failures"])
    report["component_error_count"] = _positive_integer(result.get("numberComponentErrors"))
    report["test_error_count"] = _positive_integer(result.get("numberTestErrors"))
    report["tests_completed"] = _positive_integer(result.get("numberTestsCompleted"))
    return report


def write_report(payload, cli_exit, phase, output_path, package, catalog, root):
    allowed = _allowed_names(package, catalog, root)
    report = detailed_report(payload, cli_exit, phase, allowed, method_root=root)
    # No append to arbitrary paths; caller places report in RUNNER_TEMP.
    output_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"SDOA_M53_DETAIL_REPORT: phase={phase} enumerated_failures="
          f"{report.get('enumerated_failures', 0)} report_format=SDOA-SAFE-DIAG/1 "
          "raw_payload_included=false")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--exit", type=int, required=True)
    parser.add_argument("--phase", choices=["DRY_RUN", "REAL_DEPLOY"], required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--package")
    parser.add_argument("--catalog", type=Path, default=Path("config/salesforce-devops/catalog.json"))
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    if not 0 <= args.exit <= 255:
        print(f"SDOA_M42_{args.phase}_DIAG: invalid_exit")
        return
    try:
        if args.file.stat().st_size > MAX_RESULT_BYTES:
            raise ValueError("size")
        payload = args.file.read_bytes()
        print(summarize(payload, args.exit, args.phase))
        if args.report and args.package:
            write_report(payload, args.exit, args.phase, args.report, args.package, args.catalog, args.root)
    except (OSError, ValueError, TypeError):
        print(f"SDOA_M42_{args.phase}_DIAG: json=unavailable cli_exit={args.exit} failure_kind=CLI_OR_JSON")


if __name__ == "__main__":
    main()
