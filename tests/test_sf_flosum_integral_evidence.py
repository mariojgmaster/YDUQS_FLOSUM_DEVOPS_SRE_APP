import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('collector',ROOT/'scripts/ci/sf-flosum-integral-evidence.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
BRANCH_ID='a0B000000000001AAA'
ORG_ID='a0O000000000001AAA'


def schema(obj):
    fields=[{'name':x,'type':'string'} for x in ('Id','Name','CreatedDate','LastModifiedDate')]
    if obj==m.LOG:
        fields += [{'name':x,'type':'string'} for x in m.FIELDS]
        for field in fields:
            if field['name']=='Flosum__Branch__c':
                field.update(type='reference',referenceTo=[m.BRANCH])
            if field['name']=='Flosum__Organisation__c':
                field.update(type='reference',referenceTo=['Flosum__Organisation__c'])
            if field['name']=='Flosum__Result__c':
                field.update(calculated=True,calculatedFormula='IF(private_condition, "Success", "Failed")')
        fields.append({'name':'Flosum__Related_Branch__c','type':'reference','referenceTo':[m.BRANCH]})
    return {'name':obj,'fields':fields,'childRelationships':[{'private':'schema-detail'}]}


class EvidenceTests(unittest.TestCase):
    def context(self):
        return {'GITHUB_REPOSITORY_OWNER':'owner','GITHUB_ACTOR':'owner','GITHUB_REF':'refs/heads/master','GITHUB_RUN_ATTEMPT':'1','GITHUB_EVENT_NAME':'issues'}

    def event(self):
        return {'action':'opened','sender':{'login':'owner'},'issue':{'title':m.TITLE,'body':m.BODY+'\n','user':{'login':'owner'}}}

    def test_authorization_and_spoof_rejection(self):
        m.authorize(self.event(),self.context())
        for key,value in [('GITHUB_ACTOR','stranger'),('GITHUB_REF','refs/heads/pr'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','push')]:
            ctx=self.context();ctx[key]=value
            with self.assertRaises(m.EvidenceError):m.authorize(self.event(),ctx)
        for key,value in [('title',m.TITLE+' '),('body',m.BODY+'\ncommand=arbitrary')]:
            event=self.event();event['issue'][key]=value
            with self.assertRaises(m.EvidenceError):m.authorize(event,self.context())

    def test_complete_schema_and_raw_values_survive_without_public_stdout(self):
        statements=[]
        def reader(sql,tooling=False):
            statements.append(sql)
            if tooling:return [{'QualifiedApiName':'field','DataType':'Text'}]
            if sql==f'SELECT Id FROM {m.BRANCH} LIMIT 10001':return [{'Id':BRANCH_ID}]
            if f'FROM {m.LOG}' in sql:return [{'Id':'private-log','Flosum__Organisation__c':ORG_ID,'Flosum__Result__c':'<img alt="Success"/>','Flosum__Status__c':'Completed'}]
            if 'FROM Flosum__Organisation__c' in sql:return [{'Id':ORG_ID,'Name':'PRIVATE_ORG_NAME'}]
            return [{'Id':BRANCH_ID}]
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            evidence=m.collect({'branch_id_sha256':hashlib.sha256(BRANCH_ID.encode()).hexdigest()},reader,schema)
        self.assertEqual(output.getvalue(),'')
        self.assertEqual(evidence['records'][m.LOG][0]['Flosum__Result__c'],'<img alt="Success"/>')
        self.assertTrue(evidence['scope_complete'])
        self.assertFalse(evidence['completion_timestamp_certified'])
        self.assertEqual(len(evidence['branch_links']),2)
        self.assertTrue(any(' OR ' in x for x in statements))
        self.assertIn('calculatedFormula',json.dumps(evidence['schemas']))
        self.assertIn('private_condition',json.dumps(evidence['schemas']))
        org_queries=[x for x in statements if 'FROM Flosum__Organisation__c' in x]
        self.assertTrue(all(x.startswith('SELECT Id, Name FROM') for x in org_queries))

    def test_limits_do_not_silently_truncate(self):
        for many_branches in (True,False):
            def reader(sql,tooling=False):
                if sql==f'SELECT Id FROM {m.BRANCH} LIMIT 10001':
                    return [{'Id':BRANCH_ID}] * (10001 if many_branches else 1)
                if f'FROM {m.LOG}' in sql:return [{'Id':'private'}]*1001
                return [{'Id':BRANCH_ID}]
            with self.assertRaises(m.EvidenceError):
                m.collect({'branch_id_sha256':hashlib.sha256(BRANCH_ID.encode()).hexdigest()},reader,schema)

    def test_bad_selector_fails_without_log_queries(self):
        with self.assertRaises(m.EvidenceError):
            m.collect({'branch_id_sha256':'invalid'},lambda *a,**kw:[{'Id':BRANCH_ID}],schema)

    def test_write_commands_denied(self):
        for args in (['project','deploy','start'],['data','create','record'],['apex','run']):
            with self.assertRaises(m.EvidenceError):m.sf(args)

    def test_ciphertext_roundtrip_and_no_plaintext_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);key=root/'key.pem';cert=root/'cert.pem';sealed=root/'evidence.cms';out=root/'report.json'
            subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-keyout',str(key),'-out',str(cert),'-nodes','-days','1','-subj','/CN=test/'],capture_output=True,check=True)
            data={'private_record':'SENSITIVE_SENTINEL','all_values':[None,False,1,'Complete']}
            m.seal(data,cert,sealed)
            self.assertNotIn(b'SENSITIVE_SENTINEL',sealed.read_bytes())
            subprocess.run(['openssl','cms','-decrypt','-binary','-inform','DER','-in',str(sealed),'-inkey',str(key),'-out',str(out)],capture_output=True,check=True)
            self.assertEqual(json.loads(out.read_text()),data)

    def test_workflow_has_no_plaintext_artifact_or_input_shell_expansion(self):
        y=(ROOT/'.github/workflows/sf-flosum-integral-evidence.yml').read_text()
        self.assertNotIn('pull_request_target',y)
        self.assertNotIn('github.event.issue.body }}',y)
        self.assertIn('retention-days: 1',y)
        self.assertIn('flosum-integral-evidence.cms',y)
        self.assertNotIn('path: ${{ runner.temp }}\n',y)
        self.assertIn('persist-credentials: false',y)
        self.assertNotIn('BEGIN PRIVATE KEY',(ROOT/'config/salesforce-devops/flosum-collector-cert.pem').read_text())


if __name__=='__main__':unittest.main()
