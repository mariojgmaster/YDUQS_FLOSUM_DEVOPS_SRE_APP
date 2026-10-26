#!/usr/bin/env python3
"""SPEC-006 M1. Deterministic, sandbox-only dry-run: Apex + LWC + Tab + Reader + live App.
Never commits, uploads or prints original Salesforce application metadata.
Phase 1 Apex/LWC must already be installed; validates Phase 2 navigation only.\nDeploying persistently is NOT implemented by this script.
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

APP = "DevOps_SRE_Analytics"
LABEL = "DevOps & SRE Analytics"
EXPECTED_APP_SHA = "369b9822cc6c67bb3bf237056fb50a3846998e5d8454fc60ddd1f621ac5a6d4a"
TITLE = "SDOA BRANCH INTEGRATION PLAN DevSreFeat"
BODY = "SDOA-BRANCH-INTEGRATION/1\noperation=plan\ntarget=DevSreFeat\npackage=branch-monitor-m1-integration"
NS = "{http://soap.sforce.com/2006/04/metadata}"
SRC_MANIFEST = "manifest/sf-branch-monitor-m1-integration-source.xml"
SOURCE_TYPES = {
    "CustomTab": {"branchMonitor"},
    "PermissionSet": {"DevSreBranchMonitor_Reader"}
}
TARGET_TYPES = {**SOURCE_TYPES, "CustomApplication": {APP}}

class Block(Exception): pass

def verify_issue(path, owner):
    e=json.loads(Path(path).read_text("utf-8"))
    if not owner or e.get("action")!="opened" or e.get("issue",{}).get("title")!=TITLE or (
        e.get("issue",{}).get("body","").strip()!=BODY or
        e.get("issue",{}).get("user",{}).get("login")!=owner or
        e.get("sender",{}).get("login")!=owner or
        e.get("repository",{}).get("owner",{}).get("login")!=owner
    ): raise Block("Owner approval is missing")

def members(xml):
    root=ET.fromstring(xml)
    if root.tag!=NS+"Package" or root.findtext(NS+"version")!="67.0":
        raise Block("Invalid manifest")
    result={}
    for typ in root.findall(NS+"types"):
        kind=typ.findtext(NS+"name")
        names=[n.text for n in typ.findall(NS+"members")]
        if not kind or kind in result or len(names)!=len(set(names)):
            raise Block("Duplicate manifest groups")
        result[kind]=set(names)
    return result

def check_manifest(path):
    if members(Path(path).read_bytes())!=SOURCE_TYPES:
        raise Block("Source manifest drift")

def cli(arguments,cwd=None,timeout=240):
    p=subprocess.run(["sf",*arguments,"--json"],cwd=cwd,
        text=True,capture_output=True,timeout=timeout,check=False)
    if p.returncode!=0 or len(p.stdout)>4_000_000:
        raise Block("Salesforce CLI command failed")
    j=json.loads(p.stdout)
    if j.get("status")!=0: raise Block("Salesforce CLI returned error")
    return j.get("result")

def extract_app(archive_path):
    with ZipFile(archive_path) as zipf:
        found=[]
        for info in zipf.infolist():
            parts=PurePosixPath(info.filename).parts
            if ".." in parts or info.filename.startswith("/") or info.file_size>1_000_000:
                raise Block("Unsafe metadata archive")
            if info.is_dir(): continue
            if len(parts)>1 and parts[-2]=="applications" and parts[-1]==APP+".app":
                found.append(zipf.read(info))
        if len(found)!=1: raise Block("CustomApplication retrieve ambiguous")
        return found[0]

def patch_app(payload):
    if hashlib.sha256(payload).hexdigest()!=EXPECTED_APP_SHA:
        raise Block("App changed since reviewed inspection; reread before any update")
    root=ET.fromstring(payload)
    if root.tag!=NS+"CustomApplication" or root.findtext(NS+"label")!=LABEL:
        raise Block("Unexpected Salesforce application")
    children=list(root)
    before=[(el.tag,el.text,dict(el.attrib)) for el in children]
    tabs=[el.text for el in root.findall(NS+"tabs")]
    if len(tabs)!=4 or len(set(tabs))!=4 or "branchMonitor" in tabs:
        raise Block("Unexpected baseline navigation")
    pipeline=[x for x in children if x.tag==NS+"tabs" and
        (x.text or "").lower().endswith("pipelinemonitor")]
    if len(pipeline)!=1 or tabs.index(pipeline[0].text)!=1:
        raise Block("Pipeline Monitor moved since inspection")
    index=children.index(pipeline[0])
    tab=ET.Element(NS+"tabs");tab.text="branchMonitor"
    root.insert(index,tab)
    after=[(el.tag,el.text,dict(el.attrib)) for el in root]
    if after[:index]+after[index+1:]!=before:
        raise Block("Unexpected app metadata alteration")
    if [x.text for x in root.findall(NS+"tabs")]!=tabs[:1]+["branchMonitor"]+tabs[1:]:
        raise Block("App tab order rejected")
    ET.register_namespace("",NS[1:-1])
    result=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    if not result or len(result)>1_000_000:
        raise Block("Malformed application metadata")
    return result

def write_manifest(path):
    root=ET.Element(NS+"Package")
    for name,values in TARGET_TYPES.items():
        g=ET.SubElement(root,NS+"types")
        for value in sorted(values):
            ET.SubElement(g,NS+"members").text=value
        ET.SubElement(g,NS+"name").text=name
    ET.SubElement(root,NS+"version").text="67.0"
    ET.register_namespace("",NS[1:-1])
    Path(path).write_bytes(ET.tostring(root,encoding="utf-8",xml_declaration=True))
    if members(Path(path).read_bytes())!=TARGET_TYPES:
        raise Block("Staging package is out of scope")

def prepare(repo,tmp):
    check_manifest(repo/SRC_MANIFEST)
    stage=tmp/"stage"
    converted=cli(["project","convert","source","--manifest",str(repo/SRC_MANIFEST),
        "--output-dir",str(stage)],cwd=str(repo),timeout=120)
    if not (stage/"package.xml").is_file() or members((stage/"package.xml").read_bytes())!=SOURCE_TYPES:
        raise Block("Metadata conversion scope incomplete")
    for required in [
        "tabs/branchMonitor.tab",
        "permissionsets/DevSreBranchMonitor_Reader.permissionset"
    ]:
        if not (stage/required).is_file(): raise Block("Missing converted component")
    proj=tmp/"isolated"
    (proj/"empty").mkdir(parents=True)
    (proj/"sfdx-project.json").write_text(json.dumps({
        "packageDirectories":[{"path":"empty","default":True}],
        "name":"bm-m1-read-only-validate","namespace":"","sourceApiVersion":"67.0"}))
    retrieved=tmp/"retrieved";retrieved.mkdir()
    cli(["project","retrieve","start","--metadata","CustomApplication:"+APP,
        "--api-version","67.0","--target-metadata-dir",str(retrieved),
        "--target-org","devsrefeat-ci","--wait","20"],cwd=str(proj),timeout=200)
    archives=list(retrieved.glob("*.zip"))
    if len(archives)!=1: raise Block("Retrieve missing")
    updated=patch_app(extract_app(archives[0]))
    app_dir=stage/"applications";app_dir.mkdir()
    (app_dir/(APP+".app")).write_bytes(updated)
    write_manifest(stage/"package.xml")
    all_files=[f.relative_to(stage).as_posix() for f in stage.rglob("*") if f.is_file()]
    if len(all_files)>150 or any(".." in PurePosixPath(f).parts for f in all_files):
        raise Block("Unbounded staging package")
    print("BM_M1_INTEGRATION_STAGED: source_types=2 app=1 extra_tabs=1 preserved_original_tabs=4 scope_valid=true")
    return stage

def classify_failures(result):
    """Only whitelisted component types/names and fixed categories, no raw messages."""
    details=result.get("details") if isinstance(result,dict) else {}
    failures=details.get("componentFailures",[]) if isinstance(details,dict) else []
    if isinstance(failures,dict): failures=[failures]
    if not isinstance(failures,list): failures=[]
    suspects=[]
    for entry in failures[:10]:
        if not isinstance(entry,dict): continue
        member=entry.get("fullName")
        kind=entry.get("componentType")
        if kind in TARGET_TYPES and member in TARGET_TYPES[kind]:
            suspects.append(kind+":"+member)
        else:
            suspects.append("unclassified")
        problem=str(entry.get("problem","")).lower()
        category="unclassified"
        for code,tokens in [
            ("ACCESS",("insufficient access","insufficient privilege","permission")),
            ("MISSING_DEPENDENCY",("not found","does not exist","unknown")),
            ("METADATA_SCHEMA",("invalid","unexpected","not allowed","unsupported")),
            ("TAB_REFERENCE",("tab","lightning component","lwccomponent")),
        ]:
            if any(t in problem for t in tokens):
                category=code;break
        print("BM_M1_SAFE_FAILURE: component="+suspects[-1]+" category="+category)
    if not failures: print("BM_M1_SAFE_FAILURE: component=not_identified category=not_identified")

def preflight_m1_installed():
    """Confirm Phase 1 is already installed before changing app metadata."""
    output=cli(["data","query","--use-tooling-api",
        "--query","SELECT Name FROM ApexClass WHERE Name IN ('DevSreBranchMonitorController','DevSreBranchMonitorTest') LIMIT 3",
        "--target-org","devsrefeat-ci"],timeout=120)
    names={r.get("Name") for r in output.get("records",[])
           if isinstance(r,dict)} if isinstance(output,dict) else set()
    if names!={"DevSreBranchMonitorController","DevSreBranchMonitorTest"}:
        print("BM_M1_DEPENDENCY: phase1_code_deployed=false")
        raise Block("Install Phase 1 first")
    bundles=cli(["org","list","metadata","--metadata-type","LightningComponentBundle",
        "--target-org","devsrefeat-ci"],timeout=120)
    if not isinstance(bundles,list) or not any(
        isinstance(x,dict) and x.get("fullName")=="devSreBranchMonitor" for x in bundles):
        print("BM_M1_DEPENDENCY: phase1_code_deployed=false")
        raise Block("LWC not yet installed")
    print("BM_M1_DEPENDENCY: phase1_code_deployed=true")

def plan(repo):
    if os.environ.get("GITHUB_REF")!="refs/heads/master" or (
        os.environ.get("GITHUB_ACTOR")!=os.environ.get("GITHUB_REPOSITORY_OWNER")
    ) or os.environ.get("GITHUB_RUN_ATTEMPT")!="1":
        raise Block("Only trusted master owner may validate")
    preflight_m1_installed()
    with tempfile.TemporaryDirectory(prefix="bm-m1-integration-") as directory:
        stage=prepare(repo,Path(directory))
        # Sandbox dry-run only. No deploy mode. Full specified Apex test coverage.
        args=["project","deploy","start","--dry-run","--api-version","67.0",
              "--metadata-dir",str(stage),"--test-level","RunSpecifiedTests",
              "--tests","DevSreBranchMonitorTest","--target-org","devsrefeat-ci","--wait","45"]
        p=subprocess.run(["sf",*args,"--json"],cwd=str(repo),capture_output=True,
                         text=True,check=False,timeout=3100)
        try:
            j=json.loads(p.stdout)
            r=j.get("result") or {}
            tests=r.get("numberTestsCompleted",r.get("details",{}).get("runTestResult",{}).get("numTestsRun",-1))
            test_errors=r.get("numberTestErrors",r.get("details",{}).get("runTestResult",{}).get("numFailures",-1))
            components=r.get("numberComponentErrors",-1)
            status=r.get("status","unknown")
            succeeded=(p.returncode==0 and j.get("status")==0 and r.get("success")==True
                       and r.get("done")==True and status=="Succeeded"
                       and isinstance(tests,int) and tests>=6
                       and str(test_errors)=="0" and str(components)=="0")
        except (ValueError,TypeError,AttributeError):
            tests=test_errors=components="unknown";succeeded=False
        print("BM_M1_INTEGRATION_DRY_RUN: success="+str(succeeded).lower()+
              " tests="+str(tests)+" test_errors="+str(test_errors)+
              " component_errors="+str(components)+" persisted=false")
        if not succeeded:
            classify_failures(r if isinstance(r,dict) else {})
            raise Block("Salesforce integrated dry-run not proven")
    print("PASS: BM_M1_INTEGRATION_FULL_DRY_RUN")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify-issue")
    p.add_argument("--owner")
    p.add_argument("--plan",action="store_true")
    args=p.parse_args()
    try:
        if args.verify_issue:
            verify_issue(args.verify_issue,args.owner)
            print("PASS: BM_M1_INTEGRATION_OWNER_PLAN")
        elif args.plan:
            plan(Path(__file__).resolve().parents[2])
        else: raise Block("Unsupported operation")
    except (Block,OSError,ValueError,TypeError,KeyError,BadZipFile,ET.ParseError,subprocess.TimeoutExpired):
        print("::error title=BM_M1_INTEGRATION_BLOCKED::Validation incomplete; no changes persisted and source details suppressed.")
        raise SystemExit(1)

if __name__=="__main__": main()
