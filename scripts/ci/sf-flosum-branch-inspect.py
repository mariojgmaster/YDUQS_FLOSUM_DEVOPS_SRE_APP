#!/usr/bin/env python3
"""Inspect one explicitly selected Flosum Branch and related Metadata Logs.

Never print source data, user inputs, IDs, field API names or Salesforce errors
into the public repository's GitHub Actions log. Read-only, bounded SOQL.
"""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

BRANCH = "Flosum__Branch__c"
LOG = "Flosum__Metadata_Log__c"
ID_RE = re.compile(r"^[A-Za-z0-9]{15}(?:[A-Za-z0-9]{3})?$")
FIELD_RE = re.compile(r"^(?:Flosum|git)__[A-Za-z][A-Za-z0-9_]{0,120}__c$")
SAMPLE_LIMIT = 8
MAX_BRANCH_LINKS = 2


class AuditError(Exception):
    pass


def sf(args):
    try:
        proc = subprocess.run(["sf", *args, "--target-org", "devsrefeat-ci", "--json"],
                              capture_output=True, text=True, timeout=75, check=False)
        if proc.returncode or len(proc.stdout) > 5_000_000:
            raise AuditError("CLI unavailable")
        payload = json.loads(proc.stdout)
        if not isinstance(payload, dict) or payload.get("status") != 0:
            raise AuditError("Salesforce returned non-success")
        return payload["result"]
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        raise AuditError("Unreadable result") from exc


def describe(object_name):
    data = sf(["sobject", "describe", "--sobject", object_name])
    if not isinstance(data, dict) or not isinstance(data.get("fields"), list):
        raise AuditError("Describe schema not found")
    fields = {}
    for field in data["fields"]:
        if not isinstance(field, dict):
            continue
        name = field.get("name")
        if name in ("Id", "CreatedDate") or isinstance(name, str) and FIELD_RE.fullmatch(name):
            fields[name] = field
    if "Id" not in fields:
        raise AuditError("Object not accessible")
    return fields


def role(name, field):
    if field.get("type") != "reference":
        return None
    targets = field.get("referenceTo") or []
    if not isinstance(targets, list):
        return None
    words = (name + " " + " ".join(str(x) for x in targets)).lower()
    for category, identifiers in (
        ("organization", ("organization", "organisation", "org__", "environment", "instance", "target_org")),
        ("branch", ("branch",)),
        ("commit", ("commit",)),
        ("release", ("release",)),
        ("pipeline", ("pipeline",)),
    ):
        if any(identifier in words for identifier in identifiers):
            return category
    return None


def log_lookups(fields):
    return [
        name for name, item in fields.items()
        if FIELD_RE.fullmatch(name)
        and item.get("type") == "reference"
        and "Flosum__Branch__c" in (item.get("referenceTo") or [])
    ]


def event_fields(fields, kinds, terms, limit):
    return sorted(
        name for name, field in fields.items()
        if FIELD_RE.fullmatch(name)
        and field.get("type") in kinds
        and re.search(terms, name, re.I)
    )[:limit]


def query(soql):
    result = sf(["data", "query", "--query", soql])
    if not isinstance(result, dict) or not isinstance(result.get("records"), list):
        raise AuditError("Query schema not found")
    return result["records"]


def inspect(branch_id, schema=None, fetch=None):
    if not isinstance(branch_id, str) or not ID_RE.fullmatch(branch_id):
        raise AuditError("Invalid Branch ID")
    describe_obj = schema or describe
    fetch_rows = fetch or query
    bfields = describe_obj(BRANCH)
    mfields = describe_obj(LOG)
    refs = {r: [] for r in ("organization", "branch", "commit", "release", "pipeline")}
    for name, field in bfields.items():
        r = role(name, field)
        if r in refs and FIELD_RE.fullmatch(name):
            refs[r].append(name)
    print("FLOSUM_BRANCH_AUDIT: scope=one_branch org=DevSreFeat no_mutation=true")
    for r, fields in refs.items():
        print(f"FLOSUM_BRANCH_SCHEMA: category={r} references={len(fields)}")

    chosen = ["Id"] + [f for r in refs for f in sorted(refs[r])[:2]]
    chosen = list(dict.fromkeys(chosen))[:12]
    records = fetch_rows(f"SELECT {', '.join(chosen)} FROM {BRANCH} WHERE Id = '{branch_id}' LIMIT 1")
    if len(records) != 1 or records[0].get("Id") != branch_id:
        raise AuditError("Branch not found or inaccessible")
    for r, fields in refs.items():
        selected = [f for f in fields if f in chosen]
        present = sum(records[0].get(f) is not None for f in selected)
        print(f"FLOSUM_BRANCH_RECORD: category={r} populated={present} checked={len(selected)}")

    links = sorted(log_lookups(mfields))
    log_orgs = sorted(name for name, field in mfields.items()
                      if FIELD_RE.fullmatch(name) and role(name, field) == "organization")
    statuses = event_fields(mfields, {"picklist", "string", "boolean"}, r"status|state|result|outcome|success|operation", 4)
    times = event_fields(mfields, {"date", "datetime"}, r"deploy|complet|execut|finish|end|start|time|date", 5)
    print(f"FLOSUM_METADATA_LOG_SCHEMA: branch_lookups={len(links)} lifecycle_candidates={len(statuses)} event_time_candidates={len(times)}")
    print(f"FLOSUM_METADATA_LOG_SCHEMA: organization_references={len(log_orgs)}")
    if not links or len(links) > MAX_BRANCH_LINKS:
        print(f"FLOSUM_METADATA_LOG_LINK: verified=false reason={'no_direct_reference' if not links else 'link_limit_exceeded'}")
    else:
        # Each schema-proven relationship is sampled independently, never chosen
        # as the canonical deployment link merely because it has records.
        cols = list(dict.fromkeys(["Id", "CreatedDate"] + statuses + times + log_orgs[:2]))
        sampled_ids = set()
        overlap = 0
        for index, join in enumerate(links, 1):
            rows = fetch_rows(
                f"SELECT {', '.join(cols)} FROM {LOG} "
                f"WHERE {join} = '{branch_id}' ORDER BY CreatedDate DESC, Id DESC LIMIT {SAMPLE_LIMIT}"
            )
            if len(rows) > SAMPLE_LIMIT:
                raise AuditError("Unbounded records")
            if any(not isinstance(x, dict) or not isinstance(x.get("Id"), str) or not x["Id"] for x in rows):
                raise AuditError("Invalid sample rows")
            ids = {x["Id"] for x in rows}
            overlap += len(ids & sampled_ids)
            sampled_ids.update(ids)
            status_populated = sum(any(x.get(s) is not None for x in rows) for s in statuses)
            times_populated = sum(any(x.get(t) is not None for x in rows) for t in times)
            print(f"FLOSUM_METADATA_LOG_LINK: verified=true slot={index}")
            print(f"FLOSUM_METADATA_LOG_SAMPLE: slot={index} rows={len(rows)} "
                  f"lifecycle_populated={status_populated} "
                  f"time_populated={times_populated} "
                  f"organization_checked={min(len(log_orgs), 2)} "
                  f"organization_populated={sum(any(x.get(f) is not None for f in log_orgs[:2]) for x in rows)} "
                  f"created_date_rows={sum(x.get('CreatedDate') is not None for x in rows)} "
                  f"may_be_truncated={int(len(rows) == SAMPLE_LIMIT)}")
        print(f"FLOSUM_METADATA_LOG_COMPARISON: unique_sample_rows={len(sampled_ids)} overlap_sample_rows={overlap} canonical_link_verified=false")
    print("FLOSUM_DORA: metric_status=NOT_CERTIFIED pending=prod_mapping_timestamp_and_outcome_semantics")


def event_branch_id():
    """Read input inside Python so runner step env/command logs cannot echo it."""
    try:
        event_path = Path(os.environ["GITHUB_EVENT_PATH"])
        if event_path.stat().st_size > 1_000_000:
            raise AuditError("Event too large")
        event = json.loads(event_path.read_text("utf-8"))
        value = event["inputs"]["branch_id"]
        if not isinstance(value, str) or not ID_RE.fullmatch(value):
            raise AuditError("Invalid Branch ID")
        return value
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise AuditError("Invalid workflow input") from exc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch-id")
    args = parser.parse_args()
    try:
        inspect(args.branch_id if args.branch_id is not None else event_branch_id())
        print("PASS: FLOSUM_BRANCH_METADATA_LOG_READ_ONLY")
    except (AuditError, KeyError, TypeError, ValueError):
        print("::error title=FLOSUM_BRANCH_AUDIT_UNAVAILABLE::Branch or log schema/record could not be verified. Details suppressed.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
