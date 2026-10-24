"""Sanitized preview metadata diagnostics. Never print unknown remote content."""
import argparse
import json
from pathlib import Path

ALLOWED = {"DevSreIncidentControllerTest", "devSreIncidentsHost", "incidentsRollbacks"}
GROUPS = ("toDeploy", "conflicts", "toDelete", "ignored")


def parse(payload):
    if not isinstance(payload, dict):
        raise ValueError("invalid CLI result")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise ValueError("no result object")
    for group in GROUPS:
        if not isinstance(result.get(group), list):
            raise ValueError("missing preview list")
    messages = []
    for group in GROUPS:
        entries = result[group]
        messages.append(f"INCIDENT_NAV_PREVIEW: group={group} count={len(entries)}")
        for item in entries:
            if not isinstance(item, dict):
                continue
            # API CLI versions use slightly different keys; only allow approved identifiers.
            values = (item.get("fullName"), item.get("name"), item.get("member"),
                      item.get("componentName"), item.get("apiName"))
            for name in values:
                if name in ALLOWED:
                    messages.append(f"INCIDENT_NAV_PREVIEW_MEMBER: group={group} member={name}")
                    break
    return messages


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", type=Path, required=True)
    args = p.parse_args()
    try:
        data = args.file.read_text("utf-8")
        if len(data) > 2_000_000:
            raise ValueError("preview oversized")
        for line in parse(json.loads(data)):
            print(line)
    except (ValueError, OSError, UnicodeError, TypeError):
        print("INCIDENT_NAV_PREVIEW: schema=unavailable")

if __name__ == "__main__":
    main()
