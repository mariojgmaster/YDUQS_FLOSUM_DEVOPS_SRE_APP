#!/usr/bin/env python3
"""Validate an explicitly authored, strict GitHub Issue ChatOps PLAN intent.

Never execute instructions from issue content. Emit only allowlisted fields.
No tokens, URLs, arbitrary text, command strings or shell expressions are passed on.
"""
import argparse
import json
import re
from pathlib import Path

IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,59}\Z")
OWNER = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})\Z")
HEADER = "SDOA-CHATOPS/1"
TEMPLATE = re.compile(
    r"SDOA-CHATOPS/1\noperation=plan\ntarget=([A-Za-z][A-Za-z0-9_-]{0,59})"
    r"\npackage_id=([A-Za-z][A-Za-z0-9_-]{0,59})\n?\Z"
)


class IntentError(ValueError):
    pass


def check(event, owner, repository, expected_target=None, expected_package=None):
    if not isinstance(event, dict) or event.get("action") != "opened":
        raise IntentError("Event is not an Issue opened event")
    if not isinstance(owner, str) or not OWNER.fullmatch(owner):
        raise IntentError("Invalid repo owner")
    if repository != f"{owner}/{repository.split('/')[-1]}" or repository.count("/") != 1:
        raise IntentError("Repository mismatch")
    repo = event.get("repository")
    if not isinstance(repo, dict) or repo.get("full_name") != repository or repo.get("default_branch") != "master":
        raise IntentError("Unapproved repository or default branch")
    issue = event.get("issue")
    if not isinstance(issue, dict) or issue.get("pull_request") is not None:
        raise IntentError("Only new Issues are supported")
    user = issue.get("user")
    sender = event.get("sender")
    if not isinstance(user, dict) or user.get("login") != owner:
        raise IntentError("Issue must be authored by repository owner")
    if not isinstance(sender, dict) or sender.get("login") != owner:
        raise IntentError("Issue event sender must be repository owner")
    if issue.get("state") != "open" or type(issue.get("number")) is not int or issue["number"] <= 0:
        raise IntentError("Issue is not newly open")
    body = issue.get("body")
    if not isinstance(body, str) or len(body) > 300:
        raise IntentError("Invalid Issue body")
    match = TEMPLATE.fullmatch(body)
    if not match:
        raise IntentError("Issue body is not an exact ChatOps PLAN intent")
    target, package = match.groups()
    if issue.get("title") != f"SDOA PLAN {target} {package}":
        raise IntentError("Issue title does not match strict PLAN intent")
    if expected_target is not None and target != expected_target:
        raise IntentError("Target changed since resolve")
    if expected_package is not None and package != expected_package:
        raise IntentError("Package changed since resolve")
    return {"operation": "plan", "target": target, "package_id": package,
            "issue_number": str(issue["number"])}


def load(path):
    if path.stat().st_size > 65536:
        raise IntentError("Event payload too large")
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--output-file", type=Path)
    parser.add_argument("--target")
    parser.add_argument("--package")
    args = parser.parse_args()
    try:
        values = check(load(args.event), args.owner, args.repository,
                       args.target, args.package)
        if args.output_file:
            # GitHub outputs are a fixed, non-executable allowlist only.
            with args.output_file.open("a", encoding="utf-8") as out:
                for key in ("operation", "target", "package_id", "issue_number"):
                    out.write(f"{key}={values[key]}\n")
        print(f"SDOA_M5_PLAN_INTENT_VERIFIED: issue={values['issue_number']} authorized_owner=true operation=plan")
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        print("::error title=SDOA_M5_INTENT_DENIED::Issue does not match owner-authored exact PLAN schema.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
