#!/usr/bin/env python3
"""Read-only Flosum evidence. Raw evidence is emitted ONLY as CMS ciphertext."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
BRANCH = 'Flosum__Branch__c'
LOG = 'Flosum__Metadata_Log__c'
NAME = re.compile(r'^(?:Flosum|git)__[A-Za-z][A-Za-z0-9_]*__c$')
ID = re.compile(r'^[A-Za-z0-9]{15}(?:[A-Za-z0-9]{3})?$')
TITLE = 'SDOA COLLECT DevSreFeat Flosum evidence'
BODY = 'SDOA-FLOSUM-EVIDENCE/1\noperation=collect\ntarget=DevSreFeat'
FIELDS = ['Flosum__Branch__c', 'Flosum__Organisation__c',
          'Flosum__Process_Type__c', 'Flosum__Status__c',
          'Flosum__Job_Completed__c', 'Flosum__Result__c',
          'Flosum__Deployment_Date__c', 'Flosum__Async_Request_Id__c',
          'Flosum__Patch__c', 'Flosum__Succeed__c', 'Flosum__Is_Error__c',
          'Flosum__Parent_Log__c', 'Flosum__Automation_Completed__c']


class EvidenceError(Exception):
    pass


def authorize(event, context):
    owner = context.get('GITHUB_REPOSITORY_OWNER')
    if not owner or context.get('GITHUB_ACTOR') != owner or context.get('GITHUB_REF') != 'refs/heads/master' or context.get('GITHUB_RUN_ATTEMPT') != '1':
        raise EvidenceError('unauthorized context')
    if context.get('GITHUB_EVENT_NAME') == 'workflow_dispatch':
        return
    issue = event.get('issue', {})
    if context.get('GITHUB_EVENT_NAME') != 'issues' or event.get('action') != 'opened' or issue.get('title') != TITLE or issue.get('body', '').rstrip('\r\n') != BODY or issue.get('user', {}).get('login') != owner or event.get('sender', {}).get('login') != owner:
        raise EvidenceError('unauthorized request')


def sf(args):
    """No auth display, no stdout/stderr forwarding, no mutation commands."""
    allowed = (args[:2] == ['sobject', 'describe'] or args[:2] == ['data', 'query'])
    if not allowed:
        raise EvidenceError('command denied')
    try:
        p = subprocess.run(['sf', *args, '--target-org', 'devsrefeat-ci', '--json'],
                           capture_output=True, timeout=120, check=False)
        if p.returncode or len(p.stdout) > 40_000_000:
            raise EvidenceError('query unavailable')
        data = json.loads(p.stdout)
        if data.get('status') != 0:
            raise EvidenceError('query rejected')
        return data['result']
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        raise EvidenceError('unreadable response') from exc


def describe(obj):
    if not NAME.fullmatch(obj):
        raise EvidenceError('object denied')
    result = sf(['sobject', 'describe', '--sobject', obj])
    if not isinstance(result, dict) or not isinstance(result.get('fields'), list):
        raise EvidenceError('schema unavailable')
    return result


def rows(sql, tooling=False):
    result = sf(['data', 'query', '--query', sql] + (['--use-tooling-api'] if tooling else []))
    if not isinstance(result, dict) or not isinstance(result.get('records'), list):
        raise EvidenceError('records unavailable')
    if result.get('done') is False or result.get('totalSize', len(result['records'])) > len(result['records']):
        raise EvidenceError('incomplete query')
    return result['records']


def fieldmap(schema):
    return {x['name']: x for x in schema['fields'] if isinstance(x, dict) and isinstance(x.get('name'), str)}


def readable_columns(schema, requested):
    fields = fieldmap(schema)
    return [x for x in dict.fromkeys(requested) if x in fields and (x in ('Id', 'Name', 'CreatedDate', 'LastModifiedDate') or NAME.fullmatch(x)) and fields[x].get('type') not in ('base64', 'address', 'location')]


def collect(scope, reader=rows, schema_reader=describe):
    evidence = {'schema_version': 1, 'collected_at': datetime.now(timezone.utc).isoformat(),
                'source': 'DevSreFeat', 'git_sha': os.environ.get('GITHUB_SHA'),
                'run_id': os.environ.get('GITHUB_RUN_ID'), 'mutation': False,
                'schemas': {}, 'records': {}, 'tooling': {}, 'gaps': [],
                'completion_timestamp_certified': False}
    for obj in (BRANCH, LOG):
        evidence['schemas'][obj] = schema_reader(obj)
    branch_index = reader(f'SELECT Id FROM {BRANCH} LIMIT 10001')
    if len(branch_index) > 10000:
        raise EvidenceError('branch scope requires narrower selector')
    candidates = [x['Id'] for x in branch_index if isinstance(x.get('Id'), str) and ID.fullmatch(x['Id']) and hashlib.sha256(x['Id'].encode()).hexdigest() == scope['branch_id_sha256']]
    if len(candidates) != 1:
        raise EvidenceError('branch scope not unique')
    branch_id = candidates[0]
    bfields = fieldmap(evidence['schemas'][BRANCH])
    branch_cols = readable_columns(evidence['schemas'][BRANCH], ['Id', 'Name', 'CreatedDate', 'LastModifiedDate', 'Flosum__Last_Commit__c'] + [x for x, f in bfields.items() if f.get('type') in ('reference', 'date', 'datetime')])
    evidence['records'][BRANCH] = reader(f"SELECT {', '.join(branch_cols)} FROM {BRANCH} WHERE Id = '{branch_id}' LIMIT 1")
    mfields = fieldmap(evidence['schemas'][LOG])
    links = sorted(x for x, f in mfields.items() if NAME.fullmatch(x) and f.get('type') == 'reference' and BRANCH in (f.get('referenceTo') or []))
    if not links or len(links) > 4:
        raise EvidenceError('branch references outside reviewed bound')
    cols = readable_columns(evidence['schemas'][LOG], ['Id', 'Name', 'CreatedDate', 'LastModifiedDate'] + FIELDS + links + [x for x, f in mfields.items() if f.get('type') in ('date', 'datetime') or (f.get('type') == 'reference' and re.search(r'organi[sz]ation|commit|release', x, re.I))])
    evidence['selected_log_fields'] = cols
    evidence['missing_expected_fields'] = sorted(set(FIELDS) - set(cols))
    if evidence['missing_expected_fields']:
        evidence['gaps'].append('expected_log_fields_missing')
    condition = ' OR '.join(f"{x} = '{branch_id}'" for x in links)
    logs = reader(f"SELECT {', '.join(cols)} FROM {LOG} WHERE ({condition}) ORDER BY CreatedDate DESC, Id DESC LIMIT 1001")
    if len(logs) > 1000:
        raise EvidenceError('log scope exceeds reviewed bound; no truncation allowed')
    evidence['records'][LOG] = logs
    evidence['branch_links'] = links
    # Read organization identity only. Never fetch org credential/configuration values.
    for name, f in mfields.items():
        if name not in cols or f.get('type') != 'reference' or not re.search(r'organi[sz]ation', name, re.I):
            continue
        targets = f.get('referenceTo') or []
        if len(targets) != 1 or not NAME.fullmatch(targets[0]):
            evidence['gaps'].append('organization_target_unresolved')
            continue
        obj = targets[0]
        ids = sorted({x[name] for x in logs if isinstance(x.get(name), str) and ID.fullmatch(x[name])})
        evidence['schemas'][obj] = schema_reader(obj)
        org_cols = readable_columns(evidence['schemas'][obj], ['Id', 'Name'])
        if ids:
            values = ', '.join("'"+x+"'" for x in ids)
            evidence['records'][obj] = reader(f"SELECT {', '.join(org_cols)} FROM {obj} WHERE Id IN ({values}) LIMIT 1001")
    # Tooling field definitions supplement full REST describe, including formulas
    # when the package exposes them. Failure is explicit, never treated as empty.
    for obj in (BRANCH, LOG):
        try:
            evidence['tooling'][obj] = reader("SELECT DurableId, QualifiedApiName, Label, DataType FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = '"+obj+"'", tooling=True)
        except EvidenceError:
            evidence['gaps'].append('tooling_field_definition_unavailable:' + obj)
    evidence['scope_complete'] = True
    evidence['records_count'] = {k: len(v) for k, v in evidence['records'].items()}
    return evidence


def seal(evidence, cert, output):
    payload = json.dumps(evidence, ensure_ascii=False, separators=(',', ':')).encode()
    p = subprocess.run(['openssl', 'cms', '-encrypt', '-binary', '-aes-256-gcm',
                        '-outform', 'DER', '-in', '/dev/stdin', '-out', str(output), str(cert)],
                       input=payload, capture_output=True, check=False)
    if p.returncode:
        raise EvidenceError('encryption failed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    try:
        authorize(json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()), os.environ)
        if args.verify_only:
            print('PASS: FLOSUM_EVIDENCE_OWNER_INTENT')
            return
        scope = json.loads((ROOT/'config/salesforce-devops/flosum-evidence-scope.json').read_text())
        evidence = collect(scope)
        output = Path(os.environ['RUNNER_TEMP'])/'flosum-integral-evidence.cms'
        seal(evidence, ROOT/'config/salesforce-devops/flosum-collector-cert.pem', output)
        print('PASS: FLOSUM_EVIDENCE_ENCRYPTED_READ_ONLY')
        print('FLOSUM_EVIDENCE: raw_output=encrypted completeness=selected_branch_scope temporal_semantics=unverified')
    except (EvidenceError, OSError, ValueError, KeyError, TypeError):
        print('::error::FLOSUM_EVIDENCE_UNAVAILABLE: no raw details disclosed; inspect reviewed scope and permissions')
        sys.exit(1)


if __name__ == '__main__':
    main()
