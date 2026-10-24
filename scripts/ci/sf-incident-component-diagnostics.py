#!/usr/bin/env python3
"""Only whitelisted aggregate metadata failure categories are printed.

This file processes sensitive Salesforce CLI JSON in an ephemeral runner.
Never emit raw Salesforce messages, component names, identifiers or stack traces.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

ALLOWED_TYPES = frozenset((
    "ApexClass", "CustomObject", "CustomField", "ValidationRule", "PermissionSet",
    "CustomPermission", "Group", "SharingRules", "CustomTab",
    "LightningComponentBundle"
))
CATEGORIES = (
    ("FIELD_OR_REFERENCE", re.compile(r"invalid field|no such column|does not exist|not found|unknown field|unknown.*reference|invalid.*reference|invalid cross reference|cannot resolve", re.I)),
    ("PERMISSION_OR_SECURITY", re.compile(r"insufficient.*access|permission|not authorized|not allowed|security", re.I)),
    ("VALIDATION_FORMULA", re.compile(r"formula|syntax error|unexpected token|invalid expression|validation rule", re.I)),
    ("DEPENDENCY_OR_PACKAGE", re.compile(r"dependent|dependency|package|namespace|missing component|cannot find|cannot reference", re.I)),
    ("DUPLICATE_OR_CONFLICT", re.compile(r"duplicate|already exists|conflict", re.I)),
    ("REQUIRED_VALUE", re.compile(r"required|must specify|missing value", re.I)),
)


def summarize(text):
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return ["INCIDENT_COMPONENT_DIAG: json_unavailable"]
    if not isinstance(data, dict) or not isinstance(data.get("result"), dict):
        return ["INCIDENT_COMPONENT_DIAG: result_unavailable"]
    details = data["result"].get("details")
    if not isinstance(details, dict):
        return ["INCIDENT_COMPONENT_DIAG: metadata_details_unavailable"]
    failures = details.get("componentFailures")
    if isinstance(failures, dict):
        failures = [failures]
    if not isinstance(failures, list):
        return ["INCIDENT_COMPONENT_DIAG: component_failures_unavailable"]
    counts = Counter()
    for item in failures[:250]:
        if not isinstance(item, dict):
            counts[("Other", "UNCLASSIFIED")] += 1
            continue
        component_type = item.get("componentType")
        if component_type not in ALLOWED_TYPES:
            component_type = "Other"
        problem = item.get("problem")
        if not isinstance(problem, str):
            problem = item.get("message") if isinstance(item.get("message"), str) else ""
        reason = "UNCLASSIFIED"
        for code, pattern in CATEGORIES:
            if pattern.search(problem[:4000]):
                reason = code
                break
        counts[(component_type, reason)] += 1
    if not counts:
        return ["INCIDENT_COMPONENT_DIAG: metadata_component_errors=0_or_unknown"]
    rows = [f"INCIDENT_COMPONENT_DIAG: type={t} category={c} count={n}"
            for (t, c), n in sorted(counts.items())]
    if len(failures) > 250:
        rows.append("INCIDENT_COMPONENT_DIAG: entries_truncated=true")
    return rows[:35]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.file.stat().st_size > 6000000:
            raise ValueError("too large")
        for line in summarize(args.file.read_text("utf-8")):
            print(line)
    except (OSError, UnicodeError, ValueError):
        print("INCIDENT_COMPONENT_DIAG: unavailable")


if __name__ == "__main__":
    main()
