import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('deployment',ROOT/'scripts/ci/sf-spec004-deploy.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class DeploymentGateTests(unittest.TestCase):
    def test_explicit_sha_target_actor_and_confirmation_are_mandatory(self):
        sha='a'*40
        ctx={'GITHUB_REPOSITORY_OWNER':'owner','GITHUB_ACTOR':'owner','GITHUB_REF':'refs/heads/master','GITHUB_RUN_ATTEMPT':'1','GITHUB_EVENT_NAME':'issues','GITHUB_SHA':sha}
        event={'action':'opened','sender':{'login':'owner'},'issue':{'title':m.TITLE,'body':'SDOA-SPEC004-DEPLOY/1\noperation=deploy\ntarget=DevSreFeat\ncommit_sha='+sha+'\nconfirmation=DEPLOY DevSreFeat SPEC004\n','user':{'login':'owner'}}}
        m.authorize(event,ctx)
        for key,value in [('GITHUB_SHA','b'*40),('GITHUB_ACTOR','stranger'),('GITHUB_EVENT_NAME','workflow_dispatch'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_REF','refs/heads/feature')]:
            wrong=dict(ctx);wrong[key]=value
            with self.assertRaises(m.v.Invalid):m.authorize(event,wrong)
        event['issue']['body']=event['issue']['body'].replace('confirmation=DEPLOY','confirmation=VALIDATE')
        with self.assertRaises(m.v.Invalid):m.authorize(event,ctx)

    def test_first_installation_and_successful_tests_required(self):
        result={'success':True,'done':True,'numberTestsCompleted':9,'details':{'componentSuccesses':[{'componentType':'CustomObject','created':True}]}}
        m.ready(result)
        result['numberTestsCompleted']=0
        with self.assertRaises(m.v.Invalid):m.ready(result)
        result['numberTestsCompleted']=9
        result['details']['componentSuccesses'][0]['created']=False
        with self.assertRaises(m.v.Invalid):m.ready(result)

    def test_validate_workflow_never_calls_deploy_entrypoint(self):
        y=(ROOT/'.github/workflows/sf-spec004-validate.yml').read_text()
        self.assertNotIn('sf-spec004-deploy.py',y)
        d=(ROOT/'.github/workflows/sf-spec004-deploy.yml').read_text()
        self.assertNotIn('workflow_dispatch:',d)
        self.assertIn(m.TITLE,d)
        self.assertIn('spec004-deployment.cms',d)


if __name__=='__main__':unittest.main()
