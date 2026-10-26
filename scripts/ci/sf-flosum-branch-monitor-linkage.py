#!/usr/bin/env python3
"""Owner-only, bounded, read-only proof of Flosum History→Component→Branch linkage.

No component names, field API names, source body, IDs, credentials or raw sf JSON
are emitted in logs. This is a sample, never a global completeness assertion.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

TITLE = "SDOA COMPONENT LINKS DevSreFeat Flosum"
BODY = "SDOA-FLOSUM-LINKS/1\noperation=linkage-sample\ntarget=DevSreFeat"
COMPONENT = "Flosum__Component__c"
HISTORY = "Flosum__Component_History__c"
BRANCH = "Flosum__Branch__c"
ID = re.compile(r"^[A-Za-z0-9]{15}(?:[A-Za-z0-9]{3})?$")
FIELD = re.compile(r"^Flosum__[A-Za-z][A-Za-z0-9_]*__c$")
SAMPLE_LIMIT = 100

class Block(Exception):
    pass

def verify_issue(event_path, owner):
    e=json.loads(Path(event_path).read_text(encoding="utf-8"))
    if (not owner or e.get("action") != "opened" or
        e.get("issue",{}).get("title") != TITLE or
        e.get("issue",{}).get("body","").strip() != BODY or
        e.get("issue",{}).get("user",{}).get("login") != owner or
        e.get("sender",{}).get("login") != owner or
        e.get("repository",{}).get("owner",{}).get("login") != owner):
        raise Block("Unauthorized issue")

def sf_read(args):
    # Strict allowlist: read-only CLI commands, no shell and no arbitrary object input.
    if args[:2] not in (["sobject","describe"], ["data","query"]):
        raise Block("Command denied")
    p=subprocess.run(["sf",*args,"--target-org","devsrefeat-ci","--json"],
        text=True,capture_output=True,check=False,timeout=90)
    if p.returncode or len(p.stdout)>2_000_000:
        raise Block("Read unavailable")
    try: data=json.loads(p.stdout)
    except (ValueError,TypeError) as exc: raise Block("Malformed read") from exc
    if data.get("status")!=0 or not isinstance(data.get("result"),dict):
        raise Block("Read denied")
    return data["result"]

def describe(name):
    if name not in (COMPONENT,HISTORY):
        raise Block("Object denied")
    result=sf_read(["sobject","describe","--sobject",name])
    if not isinstance(result.get("fields"),list):
        raise Block("Describe unavailable")
    return result

def foreign_key(schema,target):
    candidates=[f.get("name") for f in schema["fields"]
       if isinstance(f,dict) and f.get("type")=="reference"
       and target in (f.get("referenceTo") or [])
       and isinstance(f.get("name"),str) and FIELD.fullmatch(f["name"])]
    if len(candidates)!=1:
        raise Block("Foreign key ambiguous or missing")
    return candidates[0]

def rows(query):
    result=sf_read(["data","query","--query",query])
    records=result.get("records")
    if not isinstance(records,list) or result.get("done") is False or len(records)>SAMPLE_LIMIT+1:
        raise Block("Unbounded or incomplete read")
    # Refuse records not returned in a complete CLI response.
    if int(result.get("totalSize",len(records)))>len(records):
        raise Block("Query pagination not supported")
    return records

def validate_ids(values):
    values=list(values)
    if len(values)>SAMPLE_LIMIT or any(not isinstance(x,str) or not ID.fullmatch(x) for x in values):
        raise Block("Invalid reference sample")
    return values

def evaluate(component_fk, history_fk, query_reader=rows):
    if not FIELD.fullmatch(component_fk) or not FIELD.fullmatch(history_fk):
        raise Block("Untrusted schema names")
    comp=query_reader(
        f"SELECT Id,{component_fk} FROM {COMPONENT} WHERE {component_fk} != null "
        f"ORDER BY CreatedDate DESC, Id DESC LIMIT {SAMPLE_LIMIT+1}")
    hist=query_reader(
        f"SELECT Id,{history_fk} FROM {HISTORY} WHERE {history_fk} != null "
        f"ORDER BY CreatedDate DESC, Id DESC LIMIT {SAMPLE_LIMIT+1}")
    comp_more=len(comp)>SAMPLE_LIMIT
    hist_more=len(hist)>SAMPLE_LIMIT
    comp=comp[:SAMPLE_LIMIT];hist=hist[:SAMPLE_LIMIT]
    branch_bound=sum(1 for c in comp if isinstance(c.get(component_fk),str) and ID.fullmatch(c[component_fk]))
    referenced=validate_ids(sorted({h.get(history_fk) for h in hist if h.get(history_fk)}))
    linked=[]
    if referenced:
        quoted=",".join("'"+x+"'" for x in referenced)
        linked=query_reader(
            f"SELECT Id,{component_fk} FROM {COMPONENT} WHERE Id IN ({quoted}) LIMIT {SAMPLE_LIMIT+1}")
        if len(linked)>SAMPLE_LIMIT: raise Block("Linked result exceeded scope")
    linked_with_branch=sum(1 for c in linked
        if isinstance(c.get(component_fk),str) and ID.fullmatch(c[component_fk]))
    return {
        "component_sample":len(comp), "component_sample_more":comp_more,
        "component_with_branch":branch_bound,
        "history_sample":len(hist), "history_sample_more":hist_more,
        "history_distinct_component_refs":len(referenced),
        "history_refs_resolved_to_accessible_component":len(linked),
        "history_component_refs_with_branch":linked_with_branch,
        "link_quality":"positive_sample_only" if linked_with_branch else "not_demonstrated"
    }

def inspect():
    print("FLOSUM_LINKAGE_RESEARCH: target=DevSreFeat readonly=true scope=bounded_ids_only")
    component_fk=foreign_key(describe(COMPONENT),BRANCH)
    history_fk=foreign_key(describe(HISTORY),COMPONENT)
    print("PASS: FLOSUM_LINKAGE_SCHEMA_COMPONENT_TO_BRANCH")
    print("PASS: FLOSUM_LINKAGE_SCHEMA_HISTORY_TO_COMPONENT")
    info=evaluate(component_fk,history_fk)
    for k,v in info.items():
        value=str(v).lower() if isinstance(v,bool) else str(v)
        print("FLOSUM_LINKAGE_SAMPLE: "+k+"="+value)
    print("PASS: FLOSUM_LINKAGE_BOUNDED_READ_ONLY")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify-issue")
    p.add_argument("--owner")
    p.add_argument("--inspect",action="store_true")
    a=p.parse_args()
    try:
        if a.verify_issue:
            verify_issue(a.verify_issue,a.owner)
            print("PASS: FLOSUM_LINKAGE_OWNER_INTENT")
        elif a.inspect:
            inspect()
        else: raise Block("Invalid operation")
    except (Block,OSError,ValueError,TypeError,KeyError,subprocess.TimeoutExpired):
        print("::error title=FLOSUM_LINKAGE_BLOCKED::Read denied or inconclusive; no raw data shown.")
        raise SystemExit(1)
if __name__=="__main__": main()
