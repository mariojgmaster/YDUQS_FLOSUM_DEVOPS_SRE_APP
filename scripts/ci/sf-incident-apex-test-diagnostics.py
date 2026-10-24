#!/usr/bin/env python3
"""Bounded failure diagnostics for Apex test results in Salesforce Metadata API.

Never print raw failures, method names, exception messages, record identifiers,
stack trace, org URL, class body, JWT material, or user data to public logs.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

CATEGORIES = (
    ("CRUD_FLS_DENIED", re.compile(r"insufficient.*access|insufficient privileges|access.*denied|no access|securityexception|no such column.*entity|sobject type.*not supported|read access|user.mode", re.I)),
    ("FIELD_VALIDATION", re.compile(r"FIELD_CUSTOM_VALIDATION_EXCEPTION|validation rule|validation failed", re.I)),
    ("REQUIRED_FIELD_MISSING", re.compile(r"REQUIRED_FIELD_MISSING|missing required field|Required fields are missing", re.I)),
    ("INVALID_PICKLIST", re.compile(r"INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST|bad value for restricted picklist", re.I)),
    ("MIXED_DML", re.compile(r"MIXED_DML_OPERATION|mixed dml", re.I)),
    ("QUERY_NO_ROWS", re.compile(r"List has no rows for assignment to SObject", re.I)),
    ("ASSERTION", re.compile(r"System.AssertException|Assertion Failed|Assert.areEqual|Assert.isFalse|Assert.isTrue", re.I)),
    ("DML_EXCEPTION", re.compile(r"System.DmlException|DmlException", re.I)),
    ("QUERY_EXCEPTION", re.compile(r"System.QueryException|QueryException", re.I)),
    ("NULL_POINTER", re.compile(r"System.NullPointerException|NullPointerException", re.I)),
    ("OTHER_APEX_EXCEPTION", re.compile(r"System\.[A-Za-z]+Exception", re.I)),
)


KNOWN_DML_CODES = frozenset((
    "FIELD_CUSTOM_VALIDATION_EXCEPTION", "REQUIRED_FIELD_MISSING",
    "INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST", "FIELD_INTEGRITY_EXCEPTION",
    "INVALID_FIELD_FOR_INSERT_UPDATE", "INVALID_TYPE_ON_FIELD_IN_RECORD",
    "INVALID_CROSS_REFERENCE_KEY", "INSUFFICIENT_ACCESS_OR_READONLY",
    "INSUFFICIENT_ACCESS_ON_CROSS_REFERENCE_ENTITY", "MIXED_DML_OPERATION",
    "DUPLICATE_VALUE", "DUPLICATES_DETECTED", "CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY",
    "UNKNOWN_EXCEPTION", "INVALID_OPERATION", "FIELD_FILTER_VALIDATION_EXCEPTION",
    "STRING_TOO_LONG", "INVALID_FIELD", "ENTITY_IS_DELETED", "DATA_STORAGE_LIMIT_EXCEEDED",
    "INVALID_ID_FIELD", "INVALID_USER_FOR_OPERATION", "UNABLE_TO_LOCK_ROW",
    "UNABLE_TO_OBTAIN_EXCLUSIVE_ACCESS", "CANNOT_EXECUTE_FLOW_TRIGGER",
))


def dml_status(message):
    """Return only an explicitly approved Salesforce enum, never raw message."""
    if not isinstance(message, str):
        return "UNAVAILABLE"
    match = re.search(r"first error:\s*([A-Z][A-Z_]+)", message[:8000], re.I)
    if not match:
        return "UNAVAILABLE"
    code = match.group(1).upper()
    return code if code in KNOWN_DML_CODES else "OTHER"


# Only names already present in the public test source are exposed. Never print
# arbitrary Apex class/method names from the org, messages or stack traces.
KNOWN_TEST_METHODS = frozenset((
    "listsOnlySelectedIncidentsActions",
    "listsRealIncidentsWithSearch",
    "refusesPrematureDeploymentCausality",
    "rejectsOtherObjectIdAndLongSearch",
    "validatesRestorationTimeline",
))
SAFE_EXCEPTION_TYPES = {
    "AuraHandledException": "AURA_HANDLED",
    "SObjectException": "SOBJECT",
    "SecurityException": "SECURITY",
    "QueryException": "QUERY",
    "DmlException": "DML",
    "NullPointerException": "NULL_POINTER",
    "AssertException": "ASSERT",
    "UnexpectedException": "UNEXPECTED",
    "TypeException": "TYPE",
    "StringException": "STRING",
    "LimitException": "LIMIT",
    "NoAccessException": "NO_ACCESS",
}
def safe_exception_type(kind, message):
    sample = (kind if isinstance(kind, str) else "") + " " + (message if isinstance(message, str) else "")
    found = re.search(r"(?:System[.])?([A-Za-z]+Exception)\\b", sample[:3500])
    if not found:
        return "UNKNOWN"
    return SAFE_EXCEPTION_TYPES.get(found.group(1), "OTHER")



def summarize(payload):
    try:
        data = json.loads(payload)
    except (ValueError, TypeError):
        return ["INCIDENT_APEX_TEST_DIAG: json_unavailable"]
    if not isinstance(data, dict):
        return ["INCIDENT_APEX_TEST_DIAG: json_unavailable"]
    result = data.get("result")
    if not isinstance(result, dict):
        return ["INCIDENT_APEX_TEST_DIAG: results_unavailable"]
    details = result.get("details")
    if not isinstance(details, dict):
        return ["INCIDENT_APEX_TEST_DIAG: tests_details_unavailable"]
    tested = details.get("runTestResult")
    if not isinstance(tested, dict):
        return ["INCIDENT_APEX_TEST_DIAG: test_result_unavailable"]
    failures = tested.get("failures")
    if isinstance(failures, dict):
        failures = [failures]
    if not isinstance(failures, list):
        return ["INCIDENT_APEX_TEST_DIAG: failure_details_unavailable"]
    categories = Counter()
    dml_codes = Counter()
    public_method_failures = Counter()
    setup_mentions = 0
    for failure in failures[:200]:
        if not isinstance(failure, dict):
            categories["UNCLASSIFIED"] += 1
            continue
        message = failure.get("message") if isinstance(failure.get("message"), str) else ""
        stack = failure.get("stackTrace") if isinstance(failure.get("stackTrace"), str) else ""
        kind = failure.get("type") if isinstance(failure.get("type"), str) else ""
        combined = (kind + " " + message + " " + stack)[:8000]
        if "@TestSetup" in combined or "testsetup" in combined.lower():
            setup_mentions += 1
        label = "UNCLASSIFIED"
        for category, regex in CATEGORIES:
            if regex.search(combined):
                label = category
                break
        categories[label] += 1
        method_name = failure.get("methodName")
        safe_method_name = method_name if method_name in KNOWN_TEST_METHODS else "UNLISTED"
        public_method_failures[(safe_method_name, safe_exception_type(kind, message))] += 1
        if label in ("DML_EXCEPTION", "FIELD_VALIDATION", "REQUIRED_FIELD_MISSING", "INVALID_PICKLIST"):
            dml_codes[dml_status(message)] += 1
    out = [f"INCIDENT_APEX_TEST_DIAG: failures_reported={min(len(failures), 200)} setup_mentions={setup_mentions}"]
    out += [f"INCIDENT_APEX_TEST_DIAG: category={category} count={count}"
            for category, count in sorted(categories.items())]
    out += [f"INCIDENT_APEX_TEST_DIAG: dml_code={code} count={count}"
            for code, count in sorted(dml_codes.items())]
    out += [f"INCIDENT_APEX_TEST_DIAG: method={method} exception={exception} count={count}"
            for (method, exception), count in sorted(public_method_failures.items())]
    if len(failures) > 200:
        out += ["INCIDENT_APEX_TEST_DIAG: entries_truncated=true"]
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.file.stat().st_size > 6_000_000:
            raise ValueError("too large")
        for line in summarize(args.file.read_text("utf-8")):
            print(line)
    except (OSError, UnicodeError, ValueError):
        print("INCIDENT_APEX_TEST_DIAG: unavailable")


if __name__ == "__main__":
    main()
