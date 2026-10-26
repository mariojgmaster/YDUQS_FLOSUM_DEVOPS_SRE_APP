"""Unit tests for SPEC-006 explicit navigation deployment safeguards."""
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
from types import SimpleNamespace
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/ci/sf-branch-monitor-navigation-deploy.py"
spec=importlib.util.spec_from_file_location("bm_nav_deploy_tests",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class NavigationDeploySafety(unittest.TestCase):
  def payload(self,status="Succeeded",success=True,done=True,tests=6,failures=0,comp=0):
    return SimpleNamespace(returncode=0,stdout=json.dumps({"status":0,"result":{
      "status":status,"success":success,"done":done,"numberTestsCompleted":tests,
      "numberTestErrors":failures,"numberComponentErrors":comp,
      "details":{"runTestResult":{"codeCoverageWarnings":[]}}
    }}))
  def test_strict_salesforce_deploy_success_gate(self):
    self.assertTrue(m.deploy_status(self.payload())["success"])
    for response in [self.payload("Failed"),self.payload(tests=5),
      self.payload(failures=1),self.payload(comp=1),self.payload(done=False),
      self.payload(success=False)]:
      self.assertFalse(m.deploy_status(response)["success"])
    self.assertFalse(m.deploy_status(SimpleNamespace(returncode=1,stdout="SECRET"))["success"])
  def test_manual_owner_sha_confirmation_and_target_required(self):
    good={"GITHUB_EVENT_NAME":"workflow_dispatch","GITHUB_REF":"refs/heads/master",
      "GITHUB_RUN_ATTEMPT":"1","GITHUB_ACTOR":"owner",
      "GITHUB_REPOSITORY_OWNER":"owner","GITHUB_SHA":"a"*40,
      "SF_INSTANCE_URL":"https://yduqs--devsrefeat.sandbox.my.salesforce.com"}
    commit=SimpleNamespace(returncode=0,stdout="a"*40+"\n")
    with patch.dict(os.environ,good),patch.object(m.subprocess,"run",return_value=commit):
      with patch.object(m.bm,"check_manifest"):
        with redirect_stdout(io.StringIO()):m.check_intent(ROOT,"a"*40,m.CONFIRM)
        with self.assertRaises(m.Block):m.check_intent(ROOT,"a"*39,m.CONFIRM)
        with self.assertRaises(m.Block):m.check_intent(ROOT,"a"*40,"DEPLOY PROD")
        with patch.dict(os.environ,{"GITHUB_RUN_ATTEMPT":"2"}):
          with self.assertRaises(m.Block):m.check_intent(ROOT,"a"*40,m.CONFIRM)
        with patch.dict(os.environ,{"GITHUB_REF":"refs/heads/feature"}):
          with self.assertRaises(m.Block):m.check_intent(ROOT,"a"*40,m.CONFIRM)
  def test_second_deployment_blocked_on_failing_dry_run(self):
    with tempfile.TemporaryDirectory() as d:
      root=Path(d)
      stage=root/"stage";stage.mkdir()
      (stage/"package.xml").write_bytes(b"fixed")
      (stage/"tab.xml").write_bytes(b"fixed tab")
      with patch.object(m,"check_intent"),patch.object(m.bm,"preflight_m1_installed"),\
        patch.object(m.bm,"prepare",return_value=stage),\
        patch.object(m.bm,"members",return_value=m.bm.TARGET_TYPES),\
        patch.object(m,"call_deploy",return_value={"success":False}) as call,\
        patch.object(m,"confirm_no_drift") as drift,\
        patch.object(m,"verify_persisted") as verify:
        with redirect_stdout(io.StringIO()),self.assertRaises(m.Block):
          m.run(root,"a"*40,m.CONFIRM)
        self.assertEqual(call.call_count,1)
        drift.assert_not_called();verify.assert_not_called()
  def test_post_deploy_requires_exact_tab_order_and_both_metadata_types(self):
    root=ET.Element(m.bm.NS+"CustomApplication")
    ET.SubElement(root,m.bm.NS+"label").text=m.bm.LABEL
    for tab in ["doraCockpit","branchMonitor","pipelineMonitor","deploymentHistory","incidentsRollbacks"]:
      ET.SubElement(root,m.bm.NS+"tabs").text=tab
    payload=ET.tostring(root,encoding="utf-8")
    def cli_good(args,**kwargs):
      if "CustomTab" in args:return [{"fullName":"branchMonitor"}]
      if "PermissionSet" in args:return [{"fullName":"DevSreBranchMonitor_Reader"}]
      raise AssertionError("unexpected call")
    with patch.object(m,"retrieve_app",return_value=payload),patch.object(m.bm,"cli",side_effect=cli_good):
      with redirect_stdout(io.StringIO()):m.verify_persisted(ROOT,ROOT)
      bad=payload.replace(b"branchMonitor",b"wrongMonitor")
      with patch.object(m,"retrieve_app",return_value=bad):
        with self.assertRaises(m.Block):m.verify_persisted(ROOT,ROOT)

if __name__=="__main__":unittest.main()
