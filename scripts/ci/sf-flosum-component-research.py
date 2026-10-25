#!/usr/bin/env python3
"""Safe scoped Flosum Components/History schema and link inspection.
No business record content, raw API output, field names or IDs in public logs.
Run only in approved JWT-authenticated DevSreFeat GitHub workflow.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

TITLE = "SDOA COMPONENTS DevSreFeat Flosum"
BODY = "SDOA-FLOSUM-COMPONENTS/1\noperation=component-schema\ntarget=DevSreFeat"
OBJECTS = ("Flosum__Components__c", "Flosum__Component_History__c")
TARGETS = {
    "branch": {"Flosum__Branch__c"},
    "component": {"Flosum__Components__c"},
    "history": {"Flosum__Component_History__c"},
    "log": {"Flosum__Metadata_Log__c"},
}
class Block(Exception): pass

def verify_issue(event_path, owner):
    data=json.loads(Path(event_path).read_text("utf-8"))
    if (not owner or data.get("action")!="opened" or
        data.get("issue",{}).get("title")!=TITLE or
        data.get("issue",{}).get("body","").strip()!=BODY or
        data.get("issue",{}).get("user",{}).get("login")!=owner or
        data.get("sender",{}).get("login")!=owner or
        data.get("repository",{}).get("owner",{}).get("login")!=owner):
        raise Block("Owner-only exact issue required")

def sf_describe(name):
    try:
        p=subprocess.run(["sf","sobject","describe","--sobject",name,
                          "--target-org","devsrefeat-ci","--json"],
                         text=True,capture_output=True,timeout=70,check=False)
        if p.returncode or len(p.stdout)>6_000_000: raise Block("Describe unavailable")
        obj=json.loads(p.stdout)
        if obj.get("status")!=0 or not isinstance(obj.get("result",{}).get("fields"),list):
            raise Block("Object unavailable")
        return obj["result"]
    except (OSError,ValueError,subprocess.TimeoutExpired) as e: raise Block("Describe unavailable") from e

def summarize(name, description):
    fields=description["fields"]
    if len(fields)>5000: raise Block("Object too large")
    refs={role:[] for role in TARGETS}
    for field in fields:
        if not isinstance(field,dict): continue
        if field.get("type")=="reference":
            targets=set(field.get("referenceTo") or [])
            for role,allowed in TARGETS.items():
                if targets & allowed: refs[role].append(field)
    binary=sum(1 for f in fields if f.get("type") in ("base64","textarea","encryptedstring"))
    versions=sum(1 for f in fields if any(w in (f.get("name") or "").lower()
                                     for w in ("version","revision","hash","checksum")))
    commits=sum(1 for f in fields if "commit" in (f.get("name") or "").lower())
    readable=sum(1 for f in fields if f.get("accessible",True))
    print(f"FLOSUM_COMPONENT_SCHEMA: object={name} describe=ok fields={len(fields)} readable_fields={readable}")
    print("FLOSUM_COMPONENT_RELATIONS: object="+name+
          " "+" ".join(f"{role}={len(found)}" for role,found in refs.items()))
    print(f"FLOSUM_COMPONENT_SIGNALS: object={name} body_candidates={binary} version_candidates={versions} commit_candidates={commits}")
    return refs

def inspect():
    print("FLOSUM_COMPONENT_RESEARCH: target=DevSreFeat scope=metadata_only mutating=false")
    results={}
    for name in OBJECTS:
        try:
            results[name]=summarize(name,sf_describe(name))
        except Block:
            print(f"FLOSUM_COMPONENT_SCHEMA: object={name} describe=unavailable")
    if len(results)!=2:
        print("FLOSUM_COMPONENT_VERDICT: relation_graph=unverified diff_content=not_verified")
    else:
        c,h=results[OBJECTS[0]],results[OBJECTS[1]]
        print("FLOSUM_COMPONENT_VERDICT: component_to_branch="+str(bool(c["branch"])).lower()+
              " history_to_component="+str(bool(h["component"])).lower()+
              " history_to_branch="+str(bool(h["branch"])).lower()+
              " component_to_log="+str(bool(c["log"])).lower()+
              " history_to_log="+str(bool(h["log"])).lower()+
              " diff_content=not_verified")
    print("PASS: FLOSUM_COMPONENT_SCHEMA_READ_ONLY")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify-issue")
    p.add_argument("--owner")
    p.add_argument("--inspect",action="store_true")
    a=p.parse_args()
    try:
        if a.verify_issue:
            verify_issue(a.verify_issue,a.owner)
            print("PASS: FLOSUM_COMPONENT_OWNER_INTENT")
        elif a.inspect:
            inspect()
        else:
            raise Block("Operation not recognized")
    except (Block,KeyError,ValueError,TypeError,OSError):
        print("::error title=FLOSUM_COMPONENT_INSPECT_BLOCKED::Schema inspection unavailable or unauthorized; raw values suppressed.")
        raise SystemExit(1)
if __name__=="__main__": main()
