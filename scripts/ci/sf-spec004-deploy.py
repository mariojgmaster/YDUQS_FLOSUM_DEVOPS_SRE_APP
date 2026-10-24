#!/usr/bin/env python3
"""First installation only, exact owner/SHA confirmation + fresh dry-run.

This entry point must only be invoked after explicit user deployment approval.
The validation workflow remains read-only and never calls this script.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('validation',ROOT/'scripts/ci/sf-spec004-validate.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
TITLE='SDOA DEPLOY DevSreFeat SPEC004'


def authorize(event,ctx):
    owner=ctx.get('GITHUB_REPOSITORY_OWNER');sha=ctx.get('GITHUB_SHA','')
    issue=event.get('issue',{})
    expected='SDOA-SPEC004-DEPLOY/1\noperation=deploy\ntarget=DevSreFeat\ncommit_sha='+sha+'\nconfirmation=DEPLOY DevSreFeat SPEC004'
    if not re.fullmatch(r'[0-9a-f]{40}',sha) or not owner or ctx.get('GITHUB_ACTOR')!=owner or ctx.get('GITHUB_REF')!='refs/heads/master' or ctx.get('GITHUB_RUN_ATTEMPT')!='1' or ctx.get('GITHUB_EVENT_NAME')!='issues' or event.get('action')!='opened' or issue.get('title')!=TITLE or issue.get('body','').rstrip('\r\n')!=expected or issue.get('user',{}).get('login')!=owner or event.get('sender',{}).get('login')!=owner:
        raise v.Invalid('explicit deployment intent required')


def ready(result):
    if not isinstance(result,dict) or result.get('success') is not True or result.get('done') is not True or result.get('numberComponentErrors',0)!=0 or result.get('numberTestErrors',0)!=0 or result.get('numberTestsCompleted',0)<9:
        raise v.Invalid('dry-run or tests not confirmed')
    # Refuse to overwrite resources installed by another actor in the meantime.
    # Layout is created during object processing; tab is deliberately migrated.
    rows=result.get('details',{}).get('componentSuccesses',[])
    if not rows:raise v.Invalid('component evidence missing')
    for row in rows:
        if row.get('componentType') not in ('Layout','CustomTab','') and row.get('created') is not True:
            raise v.Invalid('unexpected existing component; reconcile before write')


def run_deploy(converted,evidence):
    args=['sf','project','deploy','start','--metadata-dir',str(converted),
          '--test-level','RunSpecifiedTests','--tests','DevSreEnvironmentTest','--tests','DevSreDeploymentTest',
          '--target-org','spec004-ci','--wait','20','--json']
    p=subprocess.run(args,capture_output=True,timeout=1800,check=False)
    try:data=json.loads(p.stdout)
    except (ValueError,TypeError):data={'unreadable':True}
    evidence['phases']['real_deploy']={'exit_code':p.returncode,'response':data}
    r=data.get('result',{})
    if p.returncode or data.get('status')!=0 or r.get('success') is not True or r.get('done') is not True or r.get('numberComponentErrors',0)!=0 or r.get('numberTestErrors',0)!=0:
        raise v.Invalid('deployment outcome requires reconciliation; do not retry')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    evidence={'operation':'deploy','target':'DevSreFeat','git_sha':os.environ.get('GITHUB_SHA'),'run_id':os.environ.get('GITHUB_RUN_ID'),'phases':{}}
    status=0
    try:
        event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        authorize(event,os.environ)
        if args.verify_only:print('PASS: SPEC004_EXPLICIT_DEPLOY_INTENT');return
        config=v.package_policy()
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp);converted=work/'candidate'
            v.cli(['project','retrieve','start','--metadata','CustomTab:pipelineMonitor','--target-org','spec004-ci','--target-metadata-dir',str(work),'--zip-file-name','tabs.zip','--wait','10'],'navigation',evidence)
            v.check_navigation(work/'tabs.zip')
            v.cli(['project','convert','source','--manifest',config['manifest'],'--output-dir',str(converted)],'convert',evidence)
            v.converted_policy(converted,config)
            result=v.cli(['project','deploy','start','--dry-run','--metadata-dir',str(converted),'--test-level','RunSpecifiedTests','--tests','DevSreEnvironmentTest','--tests','DevSreDeploymentTest','--target-org','spec004-ci','--wait','20'],'dry_run',evidence)
            ready(result)
            authorize(event,os.environ)
            actual=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
            if actual!=os.environ['GITHUB_SHA']:raise v.Invalid('checkout changed')
            print('PASS: SPEC004_FRESH_DRY_RUN_AND_EXPLICIT_SHA_INTENT')
            run_deploy(converted,evidence)
            print('PASS: SPEC004_REAL_DEPLOY_CONFIRMED')
    except (v.Invalid,OSError,ValueError,KeyError,subprocess.SubprocessError):
        status=1;print('::error::SPEC004_DEPLOY_UNCONFIRMED: inspect encrypted evidence and reconcile the Salesforce job before any new write')
    finally:
        if not args.verify_only:
            spec=importlib.util.spec_from_file_location('seal',ROOT/'scripts/ci/sf-flosum-integral-evidence.py')
            m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
            m.seal(evidence,ROOT/'config/salesforce-devops/flosum-collector-cert.pem',Path(os.environ['RUNNER_TEMP'])/'spec004-deployment.cms')
    sys.exit(status)


if __name__=='__main__':main()
