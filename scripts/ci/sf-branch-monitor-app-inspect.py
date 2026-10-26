#!/usr/bin/env python3
"""SPEC-006. Owner-only readonly Lightning App navigation inspection on DevSreFeat.
Retrieves CustomApplication metadata into isolated disposable directory.
Never prints XML, tokens, other app names, custom tabs, org IDs, or data values.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile, BadZipFile

TITLE = "SDOA APP NAVIGATION DevSreFeat Branch Monitor"
BODY = "SDOA-BRANCH-NAV/1\noperation=inspect-app-navigation\ntarget=DevSreFeat"
LABEL = "DevOps & SRE Analytics"
KNOWN_PIPELINE = "pipelineMonitor"
APP_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,100}$")
METADATA_NS = "{http://soap.sforce.com/2006/04/metadata}"

class Block(Exception):
    pass

def verify_issue(path, owner):
    event=json.loads(Path(path).read_text("utf-8"))
    if (not owner or event.get("action")!="opened" or
        event.get("issue",{}).get("title")!=TITLE or
        event.get("issue",{}).get("body","").strip()!=BODY or
        event.get("issue",{}).get("user",{}).get("login")!=owner or
        event.get("sender",{}).get("login")!=owner or
        event.get("repository",{}).get("owner",{}).get("login")!=owner):
        raise Block("Invalid intent")

def run_sf(arguments, cwd=None):
    command=["sf",*arguments,"--target-org","devsrefeat-ci","--json"]
    try:
        p=subprocess.run(command,cwd=cwd,text=True,capture_output=True,
                         timeout=120,check=False)
        if p.returncode!=0 or len(p.stdout)>3_000_000:
            raise Block("Salesforce read not permitted")
        parsed=json.loads(p.stdout)
        if parsed.get("status")!=0 or not isinstance(parsed.get("result"),(list,dict)):
            raise Block("Salesforce read invalid")
        return parsed["result"]
    except (OSError,subprocess.TimeoutExpired,ValueError,TypeError) as exc:
        raise Block("Salesforce read failed") from exc

def candidates(entries):
    if not isinstance(entries,list) or len(entries)>2000:
        raise Block("Invalid app inventory")
    matches=[]
    for item in entries:
        if not isinstance(item,dict):
            continue
        value=item.get("fullName")
        if not isinstance(value,str) or not APP_PATTERN.fullmatch(value):
            continue
        normalized=value.lower()
        if "devops" in normalized or "sre" in normalized or "analytics" in normalized:
            matches.append(value)
    matches=sorted(set(matches))
    if not matches or len(matches)>12:
        raise Block("Ambiguous app candidates")
    return matches

def read_target_application(zip_path, expected):
    found=[]
    with ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            parts=PurePosixPath(info.filename).parts
            if ".." in parts or info.filename.startswith("/") or info.file_size>1_000_000:
                raise Block("Unsafe metadata archive")
            if len(parts)<2 or parts[-2]!="applications":
                continue
            file_name=parts[-1]
            if not file_name.endswith((".app",".app-meta.xml")):
                continue
            full_name=file_name.replace(".app-meta.xml","").replace(".app","")
            if full_name not in expected:
                raise Block("Unexpected app metadata")
            payload=archive.read(info)
            root=ET.fromstring(payload)
            if root.tag!=METADATA_NS+"CustomApplication":
                raise Block("Unexpected XML root")
            label=root.findtext(METADATA_NS+"label")
            tab_nodes=root.findall(METADATA_NS+"tabs")
            tabs=[x.text or "" for x in tab_nodes]
            if label==LABEL or (any(x.lower().endswith(KNOWN_PIPELINE.lower()) for x in tabs)
                                and any(x.lower().endswith("incidentsrollbacks") for x in tabs)):
                found.append((full_name,label,tabs,payload))
    if len(found)!=1:
        raise Block("App match is missing or ambiguous")
    return found[0]

def inspection_report(full_name,label,tabs,payload):
    if not APP_PATTERN.fullmatch(full_name) or len(tabs)>100:
        raise Block("Unexpected application structure")
    pipeline_indexes=[i for i,x in enumerate(tabs)
                      if x.lower().endswith(KNOWN_PIPELINE.lower())]
    if len(pipeline_indexes)!=1:
        raise Block("Pipeline Monitor tab not uniquely identified")
    branch_indexes=[i for i,x in enumerate(tabs)
                    if x.lower().endswith("branchmonitor")]
    if len(branch_indexes)>1:
        raise Block("Duplicate Branch Monitor")
    if len(set(tabs))!=len(tabs):
        raise Block("Duplicate existing app tabs")
    return {
        "application_api_name":full_name,
        "label_confirmed":label==LABEL,
        "tab_count":len(tabs),
        "pipeline_index_1_based":pipeline_indexes[0]+1,
        "branch_monitor_already_present":bool(branch_indexes),
        "branch_index_1_based":branch_indexes[0]+1 if branch_indexes else 0,
        "xml_sha256":hashlib.sha256(payload).hexdigest()
    }

def inspect():
    print("BM_NAV_INSPECTION: target=DevSreFeat readonly=true temporary_metadata_only=true")
    listed=run_sf(["org","list","metadata","--metadata-type","CustomApplication"])
    names=candidates(listed)
    with tempfile.TemporaryDirectory(prefix="bm-nav-") as tmp:
        project=Path(tmp)/"isolated"; project.mkdir()
        (project/"empty").mkdir()
        (project/"sfdx-project.json").write_text(json.dumps({
            "packageDirectories":[{"path":"empty","default":True}],
            "name":"bm-navigation-research","namespace":"","sourceApiVersion":"67.0"
        }))
        retrieved=Path(tmp)/"mdapi"; retrieved.mkdir()
        args=["project","retrieve","start","--api-version","67.0",
              "--target-metadata-dir",str(retrieved),"--wait","20"]
        for name in names:
            args+=["--metadata", "CustomApplication:"+name]
        run_sf(args,cwd=str(project))
        archives=list(retrieved.glob("*.zip"))
        if len(archives)!=1:
            raise Block("Expected exactly one Metadata API zip")
        fullname,label,tabs,payload=read_target_application(archives[0],set(names))
        result=inspection_report(fullname,label,tabs,payload)
        # Print only the explicitly scoped application's public identifier, validated structure and digest.
        for key,value in result.items():
            print("BM_NAV_RESULT: "+key+"="+str(value).lower() if isinstance(value,bool)
                  else "BM_NAV_RESULT: "+key+"="+str(value))
    print("PASS: BM_NAV_READONLY_RETRIEVAL")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--verify-issue")
    parser.add_argument("--owner")
    parser.add_argument("--inspect",action="store_true")
    args=parser.parse_args()
    try:
        if args.verify_issue:
            verify_issue(args.verify_issue,args.owner)
            print("PASS: BM_NAV_OWNER_INTENT")
        elif args.inspect: inspect()
        else: raise Block("Unrecognized operation")
    except (Block,OSError,ValueError,TypeError,KeyError,ET.ParseError,BadZipFile):
        print("::error title=BM_NAV_INSPECTION_BLOCKED::Could not uniquely verify Lightning App metadata; no raw output disclosed.")
        raise SystemExit(1)

if __name__=="__main__":
    main()
