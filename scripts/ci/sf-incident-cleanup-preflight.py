#!/usr/bin/env python3
"""Validate exact deletion scope and both real sandbox CustomTabs."""
import argparse
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, BadZipFile
N="{http://soap.sforce.com/2006/04/metadata}"

def verify_manifests(root=Path(".")):
    pkg=ET.parse(root/"manifest/incidents-cleanup/package.xml").getroot()
    deleted=ET.parse(root/"manifest/incidents-cleanup/destructiveChangesPost.xml").getroot()
    assert pkg.findtext(N+"version")=="67.0" and not pkg.findall(N+"types")
    groups=deleted.findall(N+"types")
    assert len(groups)==1 and groups[0].findtext(N+"name")=="CustomTab"
    assert [v.text for v in groups[0].findall(N+"members")]==["DevSre_Incident_Intake"]
    assert deleted.findtext(N+"version")=="67.0"

def verify_original(zip_path):
    found={}
    with ZipFile(zip_path,"r") as z:
        for p in z.infolist():
            filename=p.filename.split("/")[-1]
            name=filename.removesuffix(".tab-meta.xml").removesuffix(".tab")
            if name not in ("incidentsRollbacks","DevSre_Incident_Intake") or p.file_size>250000:
                continue
            root=ET.fromstring(z.read(p))
            found[name]=root.findtext(N+"lwcComponent")
    assert found.get("incidentsRollbacks")=="devSreIncidentsHost", "original not migrated"
    assert found.get("DevSre_Incident_Intake")=="devSreIncidentIntake", "unexpected duplicate state"

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--zip",type=Path)
    args=p.parse_args()
    try:
        verify_manifests()
        if args.zip:
            assert args.zip.stat().st_size<15000000
            verify_original(args.zip)
        print("PASS: INCIDENT_DUPLICATE_ONLY_SCOPE_AND_ORIGINAL_TAB_PRESERVED")
    except (OSError, AssertionError, ET.ParseError, BadZipFile, ValueError):
        print("::error title=INCIDENT_CLEANUP_NOT_SAFE::Only the duplicate tab may be removed after original host migrated.")
        raise SystemExit(1)
