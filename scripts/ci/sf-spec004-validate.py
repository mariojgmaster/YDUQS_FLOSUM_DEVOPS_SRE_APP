#!/usr/bin/env python3
"""Exact SPEC-004 checkOnly validation. No real deploy operation exists here."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[2]
NS={'m':'http://soap.sforce.com/2006/04/metadata'}
TITLE='SDOA VALIDATE DevSreFeat SPEC004'
BODY='SDOA-SPEC004/1\noperation=validate\ntarget=DevSreFeat'


class Invalid(Exception):pass


def verify_event(event,ctx):
    owner=ctx.get('GITHUB_REPOSITORY_OWNER')
    if not owner or ctx.get('GITHUB_ACTOR')!=owner or ctx.get('GITHUB_REF')!='refs/heads/master' or ctx.get('GITHUB_RUN_ATTEMPT')!='1':raise Invalid('context')
    if ctx.get('GITHUB_EVENT_NAME')=='workflow_dispatch':return
    issue=event.get('issue',{})
    if ctx.get('GITHUB_EVENT_NAME')!='issues' or event.get('action')!='opened' or issue.get('title')!=TITLE or issue.get('body','').rstrip('\r\n')!=BODY or issue.get('user',{}).get('login')!=owner or event.get('sender',{}).get('login')!=owner:raise Invalid('intent')


def package_policy():
    config=json.loads((ROOT/'config/spec004/package.json').read_text())
    manifest=ET.parse(ROOT/config['manifest']).getroot()
    actual={}
    for group in manifest.findall('m:types',NS):
        typ=group.findtext('m:name',namespaces=NS)
        if typ in actual:raise Invalid('duplicate type')
        actual[typ]=[x.text for x in group.findall('m:members',NS)]
    if actual!=config['members'] or manifest.findtext('m:version',namespaces=NS)!='67.0':raise Invalid('scope')
    if config['target']!='DevSreFeat' or config['tests']!=['DevSreEnvironmentTest','DevSreDeploymentTest']:raise Invalid('target/test')
    if any('*' in item for names in actual.values() for item in names):raise Invalid('wildcard')
    return config


def canonical(raw):
    root=ET.fromstring(raw)
    for node in root.iter():
        if node.text is not None and not node.text.strip():node.text=None
        if node.tail is not None and not node.tail.strip():node.tail=None
    return ET.tostring(root)


def check_navigation(archive):
    with zipfile.ZipFile(archive) as z:
        names=[n for n in z.namelist() if n.endswith('/tabs/pipelineMonitor.tab') or n=='tabs/pipelineMonitor.tab']
        if len(names)!=1:raise Invalid('tab unavailable')
        remote=canonical(z.read(names[0]))
    before=canonical((ROOT/'config/spec004/pipelineMonitor.original.xml').read_bytes())
    after=canonical((ROOT/'force-app/main/default/tabs/pipelineMonitor.tab-meta.xml').read_bytes())
    if remote not in (before,after):raise Invalid('navigation drift')
    expected=ET.fromstring(before)
    expected.find('m:lwcComponent',NS).text='devSreDeliveryHub'
    if canonical(ET.tostring(expected))!=after:raise Invalid('unexpected tab change')


def converted_policy(folder,config):
    allowed={
        'classes':{n+s for n in config['members']['ApexClass'] for s in ('.cls','.cls-meta.xml')},
        'triggers':{'DevSreEnvironmentMapping.trigger','DevSreEnvironmentMapping.trigger-meta.xml'},
        'objects':{'DevSre_EnvironmentMapping__c.object'},
        'permissionsets':{n+'.permissionset' for n in config['members']['PermissionSet']},
        'customPermissions':{'DevSre_ManageEnvironments.customPermission'},
        'tabs':{'pipelineMonitor.tab'},
        'layouts':{'DevSre_EnvironmentMapping__c-Environment Mapping.layout'},
    }
    seen=[]
    for p in folder.rglob('*'):
        if p.is_symlink():raise Invalid('symlink')
        if not p.is_file():continue
        rel=p.relative_to(folder).parts
        if rel==('package.xml',):continue
        ok=(len(rel)==2 and rel[0] in allowed and rel[1] in allowed[rel[0]]) or (len(rel)==3 and rel[0]=='lwc' and rel[1] in config['members']['LightningComponentBundle'] and rel[2] in {rel[1]+s for s in ('.js','.html','.css','.js-meta.xml')})
        if not ok:raise Invalid('converted member outside scope')
        seen.append('/'.join(rel))
    for directory,names in allowed.items():
        if any(directory+'/'+name not in seen for name in names):raise Invalid('converted member missing')
    for name in config['members']['LightningComponentBundle']:
        if 'lwc/'+name+'/'+name+'.js-meta.xml' not in seen:raise Invalid('missing bundle')
    return len(seen)


def cli(args,phase,evidence):
    # Exact callers below use retrieve/convert or --dry-run only.
    if args[:3]==['project','deploy','start'] and '--dry-run' not in args:raise Invalid('real deploy forbidden')
    p=subprocess.run(['sf',*args,'--json'],capture_output=True,timeout=1800,check=False)
    try:data=json.loads(p.stdout)
    except (ValueError,TypeError):data={'unreadable':True}
    evidence['phases'][phase]={'exit_code':p.returncode,'response':data}
    if p.returncode or data.get('status')!=0:raise Invalid(phase)
    return data.get('result')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--policy-only',action='store_true');parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    evidence={'git_sha':os.environ.get('GITHUB_SHA'),'run_id':os.environ.get('GITHUB_RUN_ID'),'operation':'validate','target':'DevSreFeat','real_deploy':False,'phases':{}}
    status=0
    try:
        config=package_policy()
        if args.policy_only:print('PASS: SPEC004_EXACT_PACKAGE');return
        verify_event(json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()),os.environ)
        if args.verify_only:print('PASS: SPEC004_OWNER_VALIDATE_INTENT');return
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp);converted=work/'candidate'
            cli(['project','retrieve','start','--metadata','CustomTab:pipelineMonitor','--target-org','spec004-ci','--target-metadata-dir',str(work),'--zip-file-name','tabs.zip','--wait','10'],'navigation',evidence)
            check_navigation(work/'tabs.zip')
            cli(['project','convert','source','--manifest',config['manifest'],'--output-dir',str(converted)],'convert',evidence)
            evidence['candidate_files']=converted_policy(converted,config)
            result=cli(['project','deploy','start','--dry-run','--metadata-dir',str(converted),'--test-level','RunSpecifiedTests','--tests','DevSreEnvironmentTest','--tests','DevSreDeploymentTest','--target-org','spec004-ci','--wait','20'],'dry_run',evidence)
            if not isinstance(result,dict) or result.get('success') is not True or result.get('done') is not True or result.get('numberComponentErrors',0)!=0 or result.get('numberTestErrors',0)!=0:raise Invalid('unconfirmed validation')
            print('PASS: SPEC004_SALESFORCE_DRY_RUN')
            print('SPEC004_TESTS: completed='+str(result.get('numberTestsCompleted',0))+' errors='+str(result.get('numberTestErrors',0)))
    except (Invalid,OSError,ValueError,KeyError,subprocess.TimeoutExpired,ET.ParseError,zipfile.BadZipFile):
        status=1;print('::error::SPEC004_VALIDATION_FAILED: inspect encrypted report; no real deployment attempted')
    finally:
        if not args.policy_only and not args.verify_only:
            spec=importlib.util.spec_from_file_location('seal',ROOT/'scripts/ci/sf-flosum-integral-evidence.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            module.seal(evidence,ROOT/'config/salesforce-devops/flosum-collector-cert.pem',Path(os.environ['RUNNER_TEMP'])/'spec004-validation.cms')
    sys.exit(status)


if __name__=='__main__':main()
