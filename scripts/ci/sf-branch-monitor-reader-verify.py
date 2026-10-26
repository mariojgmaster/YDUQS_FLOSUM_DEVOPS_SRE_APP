#!/usr/bin/env python3
"""Owner-only readback of two non-sensitive, reviewed PermissionSet settings.

No content of org-managed permissions, raw Salesforce JSON, record IDs, or XML is published.
"""
import argparse
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, BadZipFile

TITLE="SDOA VERIFY READER DevSreFeat Branch Monitor"
BODY="SDOA-BRANCH-READER/1\noperation=verify\ntarget=DevSreFeat"
NAME="DevSreBranchMonitor_Reader"
NS="{http://soap.sforce.com/2006/04/metadata}"

class Block(Exception):pass

def verify_issue(path,owner):
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    if (not owner or obj.get("action")!="opened" or
        obj.get("issue",{}).get("title")!=TITLE or
        obj.get("issue",{}).get("body","").strip()!=BODY or
        obj.get("issue",{}).get("user",{}).get("login")!=owner or
        obj.get("sender",{}).get("login")!=owner or
        obj.get("repository",{}).get("owner",{}).get("login")!=owner):
        raise Block("Owner-only exact readback request required")

def parse_permission_set(raw):
    if len(raw)>1_000_000:raise Block("PermissionSet XML too large")
    root=ET.fromstring(raw)
    if root.tag!=NS+"PermissionSet":raise Block("Unexpected Salesforce metadata")
    tabs=[n for n in root.findall(NS+"tabSettings")
          if n.findtext(NS+"tab")=="branchMonitor"]
    classes=[n for n in root.findall(NS+"classAccesses")
             if n.findtext(NS+"apexClass")=="DevSreBranchMonitorController"]
    if len(tabs)>1 or len(classes)>1:raise Block("Duplicate security grants")
    tab= tabs[0].findtext(NS+"visibility") if tabs else "NotFound"
    apex=classes[0].findtext(NS+"enabled") if classes else "NotFound"
    return {"tab_visible":tab=="Visible","apex_enabled":apex=="true",
            "tab_setting_present":bool(tabs),"apex_access_present":bool(classes)}

def parse_archive(path):
    found=[]
    with ZipFile(path) as z:
        for entry in z.infolist():
            if entry.is_dir():continue
            parts=PurePosixPath(entry.filename).parts
            if ".." in parts or entry.filename.startswith("/") or entry.file_size>1_000_000:
                raise Block("Unsafe retrieve response")
            if len(parts)>=2 and parts[-2]=="permissionsets" and parts[-1] in (
                 NAME+".permissionset",NAME+".permissionset-meta.xml"):
                found.append(z.read(entry))
    if len(found)!=1:raise Block("Readback metadata missing or duplicated")
    return parse_permission_set(found[0])

def inspect():
    with tempfile.TemporaryDirectory(prefix="bm-reader-verify-") as directory:
        target=Path(directory)/"retrieved";target.mkdir()
        args=["sf","project","retrieve","start","--metadata","PermissionSet:"+NAME,
              "--api-version","67.0","--target-metadata-dir",str(target),
              "--target-org","devsrefeat-ci","--wait","20","--json"]
        command=subprocess.run(args,text=True,capture_output=True,timeout=180,check=False)
        if command.returncode or len(command.stdout)>2_000_000:
            raise Block("Salesforce retrieval not confirmed")
        r=json.loads(command.stdout)
        if r.get("status")!=0:raise Block("Salesforce retrieval rejected")
        archives=list(target.glob("*.zip"))
        if len(archives)!=1:raise Block("Missing Metadata API archive")
        result=parse_archive(archives[0])
        print("BM_READER_VERIFY: target=DevSreFeat source=MetadataAPI")
        print("BM_READER_VERIFY: reader_tab_visible="+str(result["tab_visible"]).lower()+
              " apex_controller_enabled="+str(result["apex_enabled"]).lower()+
              " matched_tab_present="+str(result["tab_setting_present"]).lower())
        if not result["tab_visible"] or not result["apex_enabled"]:
            raise Block("Expected Reader permissions not confirmed by remote")
        print("PASS: BM_READER_VISIBILITY_CONFIRMED_IN_SALESFORCE")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--verify-issue")
    a.add_argument("--owner")
    a.add_argument("--inspect",action="store_true")
    args=a.parse_args()
    try:
        if args.verify_issue:
            verify_issue(args.verify_issue,args.owner)
            print("PASS: BM_READER_VERIFY_OWNER_INTENT")
        elif args.inspect:inspect()
        else:raise Block("Invalid read-only operation")
    except (Block,OSError,ValueError,TypeError,KeyError,BadZipFile,ET.ParseError,subprocess.TimeoutExpired):
        print("::error title=BM_READER_VERIFY_BLOCKED::Could not verify published tab visibility; no raw Salesforce metadata exposed.")
        raise SystemExit(1)

if __name__=="__main__":main()
