#!/usr/bin/env python3
"""Strict owner-authored GitHub Issue intent to run a fixed sandbox dry-run.

The body is NOT a command interface. It selects no ref, manifest, org, tests,
scripts or variables. Reverify before accessing ECA/JWT credentials.
"""
import argparse
import json
import re
from pathlib import Path

OWNER_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})\Z")
TITLE = "SDOA VALIDATE DevSreFeat incident-intake"
BODY = "SDOA-INCIDENT-VALIDATE/1\noperation=validate\ntarget=DevSreFeat\npackage_id=incident-intake\n"


class IntentError(ValueError):
    pass


def check(event, owner, repository):
    if not isinstance(event, dict) or event.get("action") != "opened":
        raise IntentError("Unexpected event")
    if not isinstance(owner, str) or not OWNER_PATTERN.fullmatch(owner):
        raise IntentError("Invalid owner")
    if (not isinstance(repository, str) or repository.count("/") != 1
            or repository.split("/")[0] != owner):
        raise IntentError("Invalid repository")
    repo = event.get("repository")
    if not isinstance(repo, dict) or repo.get("full_name") != repository or repo.get("default_branch") != "master":
        raise IntentError("Repository/default branch mismatch")
    issue = event.get("issue")
    if not isinstance(issue, dict) or "pull_request" in issue:
        raise IntentError("Only newly opened Issues allowed")
    if (issue.get("state") != "open" or type(issue.get("number")) is not int
            or issue["number"] <= 0):
        raise IntentError("Invalid Issue state")
    sender = event.get("sender")
    author = issue.get("user")
    if (not isinstance(sender, dict) or sender.get("login") != owner
            or not isinstance(author, dict) or author.get("login") != owner):
        raise IntentError("Issue must originate from the repository owner")
    if issue.get("title") != TITLE or issue.get("body") not in (BODY, BODY.rstrip("\n")):
        raise IntentError("Not an exact sandbox validation intent")
    return issue["number"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, type=Path)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    try:
        if args.event.stat().st_size > 65536:
            raise IntentError("Oversized event")
        event = json.loads(args.event.read_text(encoding="utf-8"))
        issue_number = check(event, args.owner, args.repository)
        print(f"PASS: INCIDENT_CHATOPS_OWNER_INTENT issue={issue_number} target=DevSreFeat operation=validate")
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError):
        print("::error title=INCIDENT_CHATOPS_INTENT_DENIED::Issue is not an owner-authored allowlisted dry-run request.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
