#!/usr/bin/env python3
"""Read-only metadata ZIP report: find original Incident navigation tab.

Only exact-known incident labels or explicitly incident-related API names are
printed. Does not print user or org identifiers, source markup or secrets.
"""
import argparse
import re
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from xml.etree import ElementTree as ET

N = "{http://soap.sforce.com/2006/04/metadata}"
SAFE_API = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,119}$")
RELEVANT = re.compile(r"incident|rollback", re.I)
LABELS = {"incidents & rollbacks", "incidentes & rollbacks",
          "incidentes e recuperações", "incidentes & recuperações"}
REF_TAGS = ("auraComponent", "lwcComponent", "flexiPage", "scontrol", "url")
MAX_MATCHES = 12


def detect(zip_path):
    matches = []
    candidates = []
    with ZipFile(zip_path, "r") as archive:
        for item in archive.infolist():
            if not (item.filename.endswith(".tab") or item.filename.endswith(".tab-meta.xml")):
                continue
            if item.file_size > 256_000:
                continue
            filename = item.filename.split("/")[-1]
            tab_api = filename.removesuffix(".tab-meta.xml").removesuffix(".tab")
            if not SAFE_API.fullmatch(tab_api):
                continue
            try:
                root = ET.fromstring(archive.read(item))
            except (ET.ParseError, BadZipFile, ValueError):
                continue
            label = (root.findtext(N + "label") or "").strip()
            direct_match = label.casefold() in LABELS
            named_match = bool(RELEVANT.search(tab_api))
            if not (direct_match or named_match):
                continue
            refs = []
            for tag in REF_TAGS:
                value = (root.findtext(N + tag) or "").strip()
                if value and SAFE_API.fullmatch(value):
                    refs.append((tag, value))
            record = (tab_api, label if label.casefold() in LABELS else "", refs)
            if direct_match:
                matches.append(record)
            else:
                candidates.append(record)
    return matches[:MAX_MATCHES], candidates[:MAX_MATCHES]


def format_lines(matches, candidates):
    lines = []
    for api, label, refs in matches:
        detail = " ".join(f"{t}={v}" for t, v in refs) if refs else "ref=not-in-tab-metadata"
        lines.append(f"INCIDENT_EXISTING_TAB_MATCH: api={api} {detail}")
    if not matches:
        lines.append("INCIDENT_EXISTING_TAB_MATCH: none")
    for api, _, refs in candidates[:MAX_MATCHES]:
        detail = " ".join(f"{t}={v}" for t, v in refs) if refs else "ref=not-in-tab-metadata"
        lines.append(f"INCIDENT_TAB_CANDIDATE: api={api} {detail}")
    return lines


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--zip", required=True, type=Path)
    args = p.parse_args()
    try:
        if args.zip.stat().st_size > 15_000_000:
            raise ValueError("oversized metadata")
        matches, candidates = detect(args.zip)
        for line in format_lines(matches, candidates):
            print(line)
        print("PASS: INCIDENT_ORIGINAL_TAB_READ_ONLY_DISCOVERY")
    except (BadZipFile, OSError, ValueError, ET.ParseError):
        print("::error title=INCIDENT_TAB_DISCOVERY_UNAVAILABLE::CustomTab metadata was not parseable.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
