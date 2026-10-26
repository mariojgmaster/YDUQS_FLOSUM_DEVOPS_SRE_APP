#!/usr/bin/env python3
"""Owner-only read-only Component Type schema probe. No record values/field APIs in logs."""
import argparse,json,re,subprocess
from pathlib import Path
TITLE="SDOA COMPONENT TYPE DevSreFeat Flosum"
BODY="SDOA-FLOSUM-COMPONENT-TYPE/1\noperation=component-type-probe\ntarget=DevSreFeat"
COMPONENT="Flosum__Component__c"
class Block(Exception): pass

def verify(path,owner):
    e=json.loads(Path(path).read_text("utf-8"))
    if not owner or e.get("action")!="opened" or e.get("repository",{}).get("owner",{}).get("login")!=owner or e.get("sender",{}).get("login")!=owner or e.get("issue",{}).get("user",{}).get("login")!=owner or e.get("issue",{}).get("title")!=TITLE or e.get("issue",{}).get("body","").strip()!=BODY:
        raise Block("Intent not approved")
def cli(args):
    if args[:2] not in (["sobject","describe"],["data","query"]):raise Block("Only read-only allowed")
    p=subprocess.run(["sf",*args,"--target-org","devsrefeat-ci","--json"],capture_output=True,text=True,timeout=70,check=False)
    if p.returncode or len(p.stdout)>6000000:raise Block("CLI failed")
    result=json.loads(p.stdout)
    if result.get("status")!=0 or not isinstance(result.get("result"),dict):raise Block("CLI response invalid")
    return result["result"]

def analyze(fields):
    if not isinstance(fields,list) or len(fields)>5000:raise Block("Schema invalid")
    candidates=[]
    for f in fields:
        if not isinstance(f,dict):continue
        name=f.get("name") or "";label=f.get("label") or ""
        kind=f.get("type")
        if not (isinstance(name,str) and isinstance(label,str) and kind in ("reference","picklist")):continue
        if "type" not in name.lower() and "type" not in label.lower():continue
        targets=f.get("referenceTo") or []
        if not isinstance(targets,list):targets=[]
        candidates.append({
            "kind":kind,
            "name_token":bool(re.search(r"component.{0,3}type|type.{0,3}component",name,re.I)),
            "label_token":bool(re.search(r"component.{0,3}type|type.{0,3}component",label,re.I)),
            "readable":f.get("accessible") is not False,
            "target_count":len(targets),
            "target_fl_namespace":len(targets)==1 and str(targets[0]).startswith("Flosum__"),
            "picklist_values":len(f.get("picklistValues") or []) if kind=="picklist" else 0,
        })
    return candidates

def inspect():
    x=cli(["sobject","describe","--sobject",COMPONENT])
    result=analyze(x.get("fields"))
    print("COMPONENT_TYPE_SCHEMA: object=Flosum__Component__c candidates="+str(len(result))+" names_and_values=redacted")
    for i,c in enumerate(result,1):
        print("COMPONENT_TYPE_CANDIDATE: ordinal="+str(i)+" "+ " ".join(k+"="+str(v).lower() for k,v in c.items()))
    try:
        d=cli(["data","query","--query","SELECT Id FROM Flosum__Component__c ORDER BY CreatedDate DESC LIMIT 26"])
        records=d.get("records")
        if not isinstance(records,list) or len(records)>26:raise Block("Unbounded component list")
        print("COMPONENT_TYPE_SAMPLE: component_rows="+str(len(records))+" sample_truncated="+str(len(records)==26).lower())
    except Block:
        print("COMPONENT_TYPE_SAMPLE: component_rows=unavailable")
    print("PASS: COMPONENT_TYPE_READ_ONLY_PROBE")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify-issue");ap.add_argument("--owner");ap.add_argument("--inspect",action="store_true")
    a=ap.parse_args()
    try:
        if a.verify_issue:verify(a.verify_issue,a.owner);print("PASS: COMPONENT_TYPE_OWNER_INTENT")
        elif a.inspect:inspect()
        else:raise Block("Invalid operation")
    except (Block,ValueError,TypeError,OSError,KeyError,subprocess.TimeoutExpired):
        print("::error title=COMPONENT_TYPE_PROBE_BLOCKED::No unreviewed data exposed")
        raise SystemExit(1)
if __name__=="__main__":main()
