#!/usr/bin/env python3
"""Read-only, privacy-limited discovery of Flosum schema in DevSreFeat.

No business records, org IDs, users, object API names or field API names are
ever printed. The CLI's raw stdout/stderr exists only in subprocess memory.
Owner-only immutable Issue intent is verified before authentication.
"""
import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ISSUE_TITLE = "SDOA INVENTORY DevSreFeat Flosum"
ISSUE_BODY = "SDOA-FLOSUM-SCHEMA/1\noperation=inventory\ntarget=DevSreFeat"
NAMESPACE = re.compile(r"^(?:Flosum|git)__[A-Za-z][A-Za-z0-9_]{0,100}__c$")
ROLE_WORDS = {
    "deployment": ("deploy", "promotion", "execution"),
    "release": ("release",),
    "commit": ("commit",),
    "environment": ("environment", "target_org", "sandbox"),
    "change": ("pull_request", "change_request", "change_set"),
    "branch": ("branch",),
}
MAX_PER_ROLE = 6
MAX_OBJECTS = 36


class DiscoveryError(Exception):
    pass


def verify_issue(path, owner):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if (not owner or data.get("action") != "opened"
            or data.get("issue", {}).get("title") != ISSUE_TITLE
            or data.get("issue", {}).get("body", "").strip() != ISSUE_BODY
            or data.get("issue", {}).get("user", {}).get("login") != owner
            or data.get("sender", {}).get("login") != owner
            or data.get("repository", {}).get("owner", {}).get("login") != owner):
        raise DiscoveryError("Issue authorization or exact intent mismatch")
    return True


def role_for(name):
    if not isinstance(name, str) or not NAMESPACE.fullmatch(name):
        return None
    value = name.casefold()
    for role, signals in ROLE_WORDS.items():
        if any(signal in value for signal in signals):
            return role
    return None


def select_candidates(payload):
    if not isinstance(payload, dict) or payload.get("status") != 0:
        raise DiscoveryError("Untrusted object list")
    records = payload.get("result")
    if not isinstance(records, list):
        raise DiscoveryError("Unexpected Salesforce object list schema")
    grouped = {role: [] for role in ROLE_WORDS}
    for item in records:
        name = item if isinstance(item, str) else item.get("name") if isinstance(item, dict) else None
        role = role_for(name)
        if role is not None:
            grouped[role].append(name)
    full = {role: len(set(values)) for role, values in grouped.items()}
    limited = []
    for role, names in grouped.items():
        for name in sorted(set(names))[:MAX_PER_ROLE]:
            limited.append((role, name))
    return full, limited[:MAX_OBJECTS]


def signals_for_describe(payload):
    if not isinstance(payload, dict) or payload.get("status") != 0:
        raise DiscoveryError("Describe failed or permission denied")
    result = payload.get("result")
    if not isinstance(result, dict) or not isinstance(result.get("fields"), list):
        raise DiscoveryError("Unexpected describe result")
    fields = result["fields"]
    if len(fields) > 5000:
        raise DiscoveryError("Unbounded field count")
    names = [f.get("name", "").casefold() for f in fields if isinstance(f, dict)]
    # Presence means only schema potential, never proof of an execution event.
    return {
        "lifecycle": any(re.search(r"status|state|result|outcome", f) for f in names),
        "target": any(re.search(r"environment|target|org__|production|instance", f) for f in names),
        "time": any(re.search(r"deploy|complet|execut|finish|end_date|start_date|promot", f)
                    and re.search(r"date|time|at__c|start|end|finish|complet", f)
                    for f in names if f not in ("createddate", "lastmodifieddate")),
        "commit_link": any("commit" in f for f in names),
        "release_link": any("release" in f for f in names),
    }


def cli_json(args):
    try:
        process = subprocess.run(["sf", *args, "--target-org", "devsrefeat-ci", "--json"],
                                 capture_output=True, text=True, timeout=75, check=False)
        if process.returncode or len(process.stdout) > 6_000_000:
            raise DiscoveryError("CLI command failed or exceeded safe bounds")
        return json.loads(process.stdout)
    except (subprocess.TimeoutExpired, OSError, ValueError) as exc:
        raise DiscoveryError("CLI result inaccessible") from exc


def inventory(list_payload, fetch):
    counts, selected = select_candidates(list_payload)
    print("FLOSUM_SCHEMA_DISCOVERY: scope=metadata_only org=DevSreFeat")
    for role in ROLE_WORDS:
        print(f"FLOSUM_SCHEMA_ROLE: role={role} candidates={counts[role]} inspected={sum(1 for r,_ in selected if r==role)}")
    failures = 0
    successes = 0
    for role in ROLE_WORDS:
        names = [name for rr, name in selected if rr == role]
        for index, name in enumerate(names, 1):
            try:
                flags = signals_for_describe(fetch(name))
            except DiscoveryError:
                failures += 1
                print(f"FLOSUM_SCHEMA_CANDIDATE: role={role} slot={index:02d} describe=unavailable")
                continue
            successes += 1
            summary = " ".join(f"{flag}={int(found)}" for flag, found in flags.items())
            print(f"FLOSUM_SCHEMA_CANDIDATE: role={role} slot={index:02d} describe=ok {summary}")
    if not selected:
        print("FLOSUM_SCHEMA_VERDICT: no_verified_candidates; metric_status=NOT_MEASURABLE")
    elif successes == 0:
        raise DiscoveryError("None of the candidate schemas could be inspected")
    else:
        print(f"FLOSUM_SCHEMA_VERDICT: inspected={successes} unavailable={failures} metric_status=NOT_MEASURABLE")
    return counts, successes, failures


def main():
    p = argparse.ArgumentParser()
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--verify-issue")
    group.add_argument("--inventory", action="store_true")
    p.add_argument("--owner")
    args = p.parse_args()
    try:
        if args.verify_issue:
            verify_issue(args.verify_issue, args.owner)
            print("PASS: FLOSUM_SCHEMA_OWNER_ISSUE_INTENT")
            return
        payload = cli_json(["sobject", "list", "--sobject", "custom"])
        inventory(payload, lambda name: cli_json(["sobject", "describe", "--sobject", name]))
        print("PASS: FLOSUM_SCHEMA_READ_ONLY_INVENTORY")
    except (DiscoveryError, OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        print("::error title=FLOSUM_SCHEMA_DISCOVERY_DENIED::Could not verify authorized, bounded schema discovery; no records queried.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
