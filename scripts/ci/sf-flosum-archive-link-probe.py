#!/usr/bin/env python3
"""Owner-authorized, bounded read-only Attachment / Salesforce Files link discovery.

Reports only numeric aggregate counts; never exposes file names, IDs, contents
or URLs in public GitHub Actions logs. No attachment payload is downloaded.
"""
import argparse,json,re,subprocess
from pathlib import Path

TITLE="SDOA ARCHIVES DevSreFeat Flosum"
BODY="SDOA-FLOSUM-ARCHIVES/1\noperation=archive-link-probe\ntarget=DevSreFeat"
MAX_HISTORIES=30
ID=re.compile(r"^[0-9A-Za-z]{15}(?:[0-9A-Za-z]{3})?$")
class Block(Exception): pass

def verify(path,owner):
    e=json.loads(Path(path).read_text("utf-8"))
    if not owner or e.get("action")!="opened" or e.get("issue",{}).get("title")!=TITLE or e.get("issue",{}).get("body","").strip()!=BODY or e.get("issue",{}).get("user",{}).get("login")!=owner or e.get("sender",{}).get("login")!=owner or e.get("repository",{}).get("owner",{}).get("login")!=owner:
        raise Block("Untrusted intent")

def rows(soql,limit):
    proc=subprocess.run(["sf","data","query","--query",soql,"--target-org","devsrefeat-ci","--json"],capture_output=True,text=True,timeout=75,check=False)
    if proc.returncode or len(proc.stdout)>1_000_000:raise Block("Query failure")
    raw=json.loads(proc.stdout)
    result=raw.get("result")
    if raw.get("status")!=0 or not isinstance(result,dict) or not isinstance(result.get("records"),list) or len(result["records"])>limit or result.get("done") is False:
        raise Block("Invalid query result")
    return result["records"]

def probe(read=rows):
    hs=read("SELECT Id FROM Flosum__Component_History__c ORDER BY CreatedDate DESC LIMIT 30",30)
    ids=[h.get("Id") for h in hs]
    if any(not isinstance(x,str) or not ID.fullmatch(x) for x in ids):raise Block("Untrusted IDs")
    print("ARCHIVE_HISTORY_SAMPLE: records="+str(len(ids))+" truncated="+str(len(ids)==MAX_HISTORIES).lower())
    if not ids:return {"histories":0,"attachment_count":0,"attachment_zip_count":0,"files_count":0}
    values=",".join("'"+x+"'" for x in ids)
    result={"histories":len(ids)}
    try:
        attach=read("SELECT Id, Name, BodyLength FROM Attachment WHERE ParentId IN ("+values+") LIMIT 51",51)
        result["attachment_count"]=len(attach)
        result["attachment_zip_count"]=sum(
            1 for a in attach if isinstance(a.get("Name"),str) and a["Name"].lower().endswith(".zip"))
        result["attachment_small_zip_count"]=sum(
            1 for a in attach if isinstance(a.get("Name"),str) and a["Name"].lower().endswith(".zip")
            and isinstance(a.get("BodyLength"),int) and a["BodyLength"]<=1048576)
        result["attachment_sample_truncated"]=len(attach)==51
    except Block:
        result["attachment_count"]="unavailable"
    try:
        links=read("SELECT Id FROM ContentDocumentLink WHERE LinkedEntityId IN ("+values+") LIMIT 51",51)
        result["files_count"]=len(links)
        result["files_sample_truncated"]=len(links)==51
    except Block:
        result["files_count"]="unavailable"
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify-issue");p.add_argument("--owner");p.add_argument("--inspect",action="store_true")
    a=p.parse_args()
    try:
        if a.verify_issue:
            verify(a.verify_issue,a.owner)
            print("PASS: ARCHIVE_PROBE_OWNER_INTENT")
        elif a.inspect:
            result=probe()
            for k,v in result.items():
                print("ARCHIVE_LINK_PROFILE: "+k+"="+str(v).lower())
            print("PASS: ARCHIVE_LINK_METADATA_ONLY")
        else:raise Block("Unsupported")
    except (Block,ValueError,TypeError,KeyError,OSError,subprocess.TimeoutExpired):
        print("::error title=ARCHIVE_PROBE_DENIED::No raw file data or metadata exposed")
        raise SystemExit(1)
if __name__=="__main__":main()
