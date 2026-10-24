#!/usr/bin/env python3
"""Strict owner-authored GitHub Issue intent for PLAN or explicitly requested DEPLOY.

The Issue supplies identifiers only, never shell fragments. Real deploy requires
the exact confirmation phrase plus the HEAD commit SHA at issue creation.
All checks are repeated in the privileged runner before authentication.
"""
import argparse
import json
import re
from pathlib import Path

ID = r"[A-Za-z][A-Za-z0-9_-]{0,59}"
SHA = r"[0-9a-f]{40}"
OWNER = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})\Z")
PLAN = re.compile(rf"SDOA-CHATOPS/1\noperation=plan\ntarget=({ID})\npackage_id=({ID})\n?\Z")
READ = re.compile(rf"SDOA-CHATOPS/3\noperation=(retrieve|compare)\ntarget=({ID})\npackage_id=({ID})\n?\Z")
DEPLOY = re.compile(
    rf"SDOA-CHATOPS/2\noperation=deploy\ntarget=({ID})\npackage_id=({ID})"
    rf"\ncommit_sha=({SHA})\nconfirmation=DEPLOY ({ID}) ({ID})\n?\Z"
)


class IntentError(ValueError):
    pass


def check(event, owner, repository, expected_target=None, expected_package=None,
          expected_sha=None, expected_operation=None):
    if not isinstance(event, dict) or event.get("action") != "opened":
        raise IntentError("Only newly opened Issues")
    if not isinstance(owner, str) or not OWNER.fullmatch(owner):
        raise IntentError("Invalid owner")
    if not isinstance(repository, str) or repository.count("/") != 1 or repository.split("/")[0] != owner:
        raise IntentError("Invalid repository")
    repo = event.get("repository")
    if not isinstance(repo, dict) or repo.get("full_name") != repository or repo.get("default_branch") != "master":
        raise IntentError("Unapproved repo or branch")
    issue = event.get("issue")
    if not isinstance(issue, dict) or issue.get("pull_request") is not None:
        raise IntentError("Not a newly opened Issue")
    if not isinstance(issue.get("user"), dict) or issue["user"].get("login") != owner:
        raise IntentError("Author is not owner")
    if not isinstance(event.get("sender"), dict) or event["sender"].get("login") != owner:
        raise IntentError("Event sender is not owner")
    if issue.get("state") != "open" or type(issue.get("number")) is not int or issue["number"] <= 0:
        raise IntentError("Issue invalid")
    body = issue.get("body")
    if not isinstance(body, str) or len(body) > 360:
        raise IntentError("Body not a bounded string")
    parsed = PLAN.fullmatch(body)
    if parsed:
        operation = "plan"
        target, package = parsed.groups()
        sha = ""
        confirmation = ""
    else:
        read = READ.fullmatch(body)
        if read:
            operation, target, package = read.groups()
            sha = ""
            confirmation = ""
        else:
            parsed = DEPLOY.fullmatch(body)
            if not parsed:
                raise IntentError("Intent not exact")
            operation = "deploy"
            target, package, sha, confirming_target, confirming_package = parsed.groups()
            if (target, package) != (confirming_target, confirming_package):
                raise IntentError("Deploy confirmation mismatch")
            confirmation = f"DEPLOY {target} {package}"
            if expected_sha is None or sha != expected_sha:
                raise IntentError("Deploy commit SHA mismatch")
    if issue.get("title") != f"SDOA {operation.upper()} {target} {package}":
        raise IntentError("Title mismatch")
    if expected_operation is not None and operation != expected_operation:
        raise IntentError("Operation changed")
    if expected_target is not None and target != expected_target:
        raise IntentError("Target changed")
    if expected_package is not None and package != expected_package:
        raise IntentError("Package changed")
    return {
        "operation": operation, "target": target, "package_id": package,
        "issue_number": str(issue["number"]), "commit_sha": sha,
        "confirmation": confirmation
    }


def load(path):
    if path.stat().st_size > 65536:
        raise IntentError("Event too large")
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--output-file", type=Path)
    parser.add_argument("--target")
    parser.add_argument("--package")
    parser.add_argument("--commit-sha")
    parser.add_argument("--operation")
    args = parser.parse_args()
    try:
        values = check(load(args.event), args.owner, args.repository,
                       args.target, args.package, args.commit_sha, args.operation)
        if args.output_file:
            with args.output_file.open("a", encoding="utf-8") as out:
                for key in ("operation", "target", "package_id", "issue_number", "commit_sha", "confirmation"):
                    out.write(f"{key}={values[key]}\n")
        print(f"SDOA_M5_INTENT_VERIFIED: issue={values['issue_number']} "
              f"operation={values['operation']} authorized_owner=true "
              f"pinned_sha={'true' if values['operation']=='deploy' else 'not_required'}")
        if values["operation"] == "plan":
            print(f"SDOA_M5_PLAN_INTENT_VERIFIED: issue={values['issue_number']} authorized_owner=true operation=plan")
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError):
        print("::error title=SDOA_M5_INTENT_DENIED::Issue did not match authorized exact operation.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
