#!/usr/bin/env python3
"""SPEC-006 M1 navigation: deliberate, one-shot sandbox deployment, fail-closed.

This module performs a fresh dry-run and actual deploy of the IDENTICAL staged
CustomTab + PermissionSet + live App package. It never prints Salesforce raw
responses, private metadata, identifiers of users, tokens or metadata contents.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

PLAN_PATH=Path(__file__).with_name("sf-branch-monitor-integrated-plan.py")
spec=importlib.util.spec_from_file_location("bm_plan",PLAN_PATH)
bm=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bm)

CONFIRM="DEPLOY DevSreFeat branch-monitor-m1-navigation"
HEX40=re.compile(r"^[0-9a-f]{40}$")

class Block(Exception): pass

def check_intent(root,sha,confirmation):
    if any((
      os.environ.get("GITHUB_EVENT_NAME")!="workflow_dispatch",
      os.environ.get("GITHUB_REF")!="refs/heads/master",
      os.environ.get("GITHUB_RUN_ATTEMPT")!="1",
      os.environ.get("GITHUB_ACTOR")!=os.environ.get("GITHUB_REPOSITORY_OWNER"),
      confirmation!=CONFIRM,
      not HEX40.fullmatch(sha),
      sha!=os.environ.get("GITHUB_SHA")
    )):
      raise Block("Explicit trusted manual approval not demonstrated")
    actual=subprocess.run(["git","rev-parse","HEAD"],cwd=root,text=True,
        capture_output=True,timeout=20,check=False)
    if actual.returncode!=0 or actual.stdout.strip()!=sha:
      raise Block("Checked-out commit differs from pinned approval")
    if os.environ.get("SF_INSTANCE_URL")!="https://yduqs--devsrefeat.sandbox.my.salesforce.com":
      raise Block("Sandbox target not on allowlist")
    bm.check_manifest(root/bm.SRC_MANIFEST)
    print("BM_NAV_DEPLOY_INTENT: owner=true master=true pinned_sha=true target=DevSreFeat manual=true")

def deploy_status(p):
    try:
      if not p.stdout or len(p.stdout)>4_000_000:return {"success":False}
      obj=json.loads(p.stdout)
      r=obj.get("result") or {}
      tests=r.get("numberTestsCompleted", (r.get("details") or {}).get("runTestResult",{}).get("numTestsRun"))
      failures=r.get("numberTestErrors",(r.get("details") or {}).get("runTestResult",{}).get("numFailures"))
      components=r.get("numberComponentErrors")
      coverage=(r.get("details") or {}).get("runTestResult",{}).get("codeCoverageWarnings",[])
      success=(
        p.returncode==0 and obj.get("status")==0 and
        r.get("success") is True and r.get("done") is True and r.get("status")=="Succeeded" and
        isinstance(tests,int) and tests>=6 and str(failures)=="0" and str(components)=="0" and
        (not coverage)
      )
      return {"success":success,"tests":tests,"failures":failures,"component_errors":components,"coverage_warnings":len(coverage or [])}
    except (ValueError,TypeError,AttributeError):
      return {"success":False}

def call_deploy(stage,root,dry):
    args=["sf","project","deploy","start"]
    if dry:args+=["--dry-run"]
    args+=["--api-version","67.0","--metadata-dir",str(stage),
           "--test-level","RunSpecifiedTests","--tests","DevSreBranchMonitorTest",
           "--target-org","devsrefeat-ci","--wait","45","--json"]
    p=subprocess.run(args,cwd=root,text=True,capture_output=True,
                     timeout=3200,check=False)
    return deploy_status(p)

def retrieve_app(repo,directory):
    directory=Path(tempfile.mkdtemp(prefix="bm-retrieve-",dir=str(directory)))
    isolated=directory/"org-preview"
    (isolated/"empty").mkdir(parents=True)
    (isolated/"sfdx-project.json").write_text(json.dumps({
      "packageDirectories":[{"path":"empty","default":True}],
      "name":"branch-monitor-verification","namespace":"","sourceApiVersion":"67.0"}))
    target=directory/"org-retrieve"
    target.mkdir()
    bm.cli(["project","retrieve","start","--metadata","CustomApplication:"+bm.APP,
       "--api-version","67.0","--target-metadata-dir",str(target),
       "--target-org","devsrefeat-ci","--wait","20"],cwd=str(isolated),timeout=200)
    zips=list(target.glob("*.zip"))
    if len(zips)!=1:raise Block("App post-read unavailable")
    return bm.extract_app(zips[0])

def confirm_no_drift(repo,directory):
    if hashlib.sha256(retrieve_app(repo,directory)).hexdigest()!=bm.EXPECTED_APP_SHA:
      raise Block("App changed after staging, before publish")
    print("BM_NAV_DEPLOY_DRIFT: unchanged=true")

def verify_persisted(repo,directory):
    payload=retrieve_app(repo,directory)
    root=ET.fromstring(payload)
    if root.tag!=bm.NS+"CustomApplication" or root.findtext(bm.NS+"label")!=bm.LABEL:
      raise Block("App post-deploy identity mismatch")
    tabs=[e.text for e in root.findall(bm.NS+"tabs")]
    if len(tabs)!=5 or len(set(tabs))!=5 or tabs[1:3]!=["branchMonitor","pipelineMonitor"]:
      raise Block("App navigation order not confirmed")
    tab_list=bm.cli(["org","list","metadata","--metadata-type","CustomTab",
       "--target-org","devsrefeat-ci"],timeout=120)
    ps_list=bm.cli(["org","list","metadata","--metadata-type","PermissionSet",
       "--target-org","devsrefeat-ci"],timeout=120)
    if not isinstance(tab_list,list) or not any(
      isinstance(e,dict) and e.get("fullName")=="branchMonitor" for e in tab_list):
      raise Block("Published tab not confirmed")
    if not isinstance(ps_list,list) or not any(
      isinstance(e,dict) and e.get("fullName")=="DevSreBranchMonitor_Reader" for e in ps_list):
      raise Block("Published PermissionSet not confirmed")
    print("BM_NAV_DEPLOY_VERIFIED: app_tabs=5 branch_before_pipeline=true tab_present=true reader_permission_set_present=true")

def run(root,sha,confirmation):
    check_intent(root,sha,confirmation)
    bm.preflight_m1_installed()
    with tempfile.TemporaryDirectory(prefix="bm-nav-deploy-") as d:
      tmp=Path(d)
      stage=bm.prepare(root,tmp)
      expected_files={f.relative_to(stage).as_posix():hashlib.sha256(f.read_bytes()).digest()
        for f in stage.rglob("*") if f.is_file()}
      if bm.members((stage/"package.xml").read_bytes())!=bm.TARGET_TYPES:
        raise Block("Scope mismatch")
      dry=call_deploy(stage,root,True)
      print("BM_NAV_DEPLOY_DRY_RUN: success="+str(dry.get("success",False)).lower()+
        " tests="+str(dry.get("tests","unknown"))+
        " test_errors="+str(dry.get("failures","unknown"))+
        " component_errors="+str(dry.get("component_errors","unknown"))+
        " coverage_warnings="+str(dry.get("coverage_warnings","unknown")))
      if not dry.get("success"):raise Block("Dry-run not approved")
      if expected_files!={f.relative_to(stage).as_posix():hashlib.sha256(f.read_bytes()).digest()
           for f in stage.rglob("*") if f.is_file()}:
        raise Block("Staged package changed during validation")
      confirm_no_drift(root,tmp)
      print("BM_NAV_DEPLOY_REAL_START: authorized=true phase=2 only")
      real=call_deploy(stage,root,False)
      print("BM_NAV_DEPLOY_REAL_RESULT: success="+str(real.get("success",False)).lower()+
        " tests="+str(real.get("tests","unknown"))+
        " test_errors="+str(real.get("failures","unknown"))+
        " component_errors="+str(real.get("component_errors","unknown"))+
        " coverage_warnings="+str(real.get("coverage_warnings","unknown")))
      if not real.get("success"):
        raise Block("Real deployment not verified; inspect Salesforce Deployment Status before retry")
      verify_persisted(root,tmp)
      print("PASS: BM_NAV_REAL_DEPLOY_SUCCEEDED")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sha",required=True)
    p.add_argument("--confirmation",required=True)
    a=p.parse_args()
    try:run(Path(__file__).resolve().parents[2],a.sha,a.confirmation)
    except (Block,bm.Block,OSError,ValueError,TypeError,KeyError,ET.ParseError,subprocess.TimeoutExpired):
      print("::error title=BM_NAV_DEPLOY_BLOCKED::Deployment incomplete or unverified; see safe diagnostics only. Never retry without status check.")
      raise SystemExit(1)

if __name__=="__main__":main()
