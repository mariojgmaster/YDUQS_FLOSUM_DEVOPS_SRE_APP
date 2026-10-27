"""Offline regression tests for the universal Salesforce DevOps kit v2.

Does not authenticate, deploy or use network; legacy v1 paths are untouched.
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sdoa_v2", ROOT / "scripts/ci/sf-kit-v2-policy.py")
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)
WORKFLOW = (ROOT / ".github/workflows/sf-m5-chatops-plan.yml").read_text("utf8")
RUNNER = (ROOT / "scripts/ci/sf-kit-v2-execute.sh").read_text("utf8")


class UniversalKitV2Tests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.candidate = self.base / "candidate"
        self.candidate.mkdir()

    def test_reviewed_real_metadata_types_not_only_apex_lwc(self):
        tab, tab_names = v2.verify_config("branch-monitor-tab-v2")
        self.assertEqual(tab["effective_test_level"], "NoTestRun")
        self.assertEqual(tab_names, {"CustomTab": ["branchMonitor"]})
        field, field_names = v2.verify_config("environment-reason-field-v2")
        self.assertEqual(field["effective_test_level"], "RunSpecifiedTests")
        self.assertEqual(field["tests"], ["DevSreEnvironmentTest"])
        self.assertEqual(field_names["CustomField"], ["DevSre_EnvironmentMapping__c.Reason__c"])
        trigger, trigger_names = v2.verify_config("environment-trigger-v2")
        self.assertEqual(trigger["effective_test_level"], "RunLocalTests")
        self.assertEqual(trigger_names, {"ApexTrigger": ["DevSreEnvironmentMapping"]})

    def test_manifest_wildcards_and_traversal_rejected(self):
        for member in ("*", "../secret", "Account.*", "A/../../B", "/etc/passwd", "A\\B"):
            path = self.base / "manifest.xml"
            path.write_text(
                '<Package xmlns="http://soap.sforce.com/2006/04/metadata">'
                f'<types><members>{member}</members><name>CustomField</name></types>'
                '<version>67.0</version></Package>', encoding="utf-8")
            with self.subTest(member=member), self.assertRaises(v2.PolicyError):
                v2.manifest(path)

    def test_sensitive_permissions_require_explicit_review(self):
        original = v2.CATALOG
        try:
            data = v2.catalog()
            data["packages"]["unreviewed-permission"] = {
                "policy_version": 2, "reviewed": True,
                "manifest": "manifest/sf-v2-branch-monitor-tab.xml",
                "allowed_types": ["PermissionSet"], "test_level": "auto", "tests": []}
            path = self.base / "catalog.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            v2.CATALOG = path
            with self.assertRaises(v2.PolicyError):
                v2.get_package("unreviewed-permission")
            data["packages"]["unreviewed-permission"]["sensitive_change_reviewed"] = True
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(v2.get_package("unreviewed-permission")["effective_test_level"], "NoTestRun")
        finally:
            v2.CATALOG = original

    def test_apex_impact_cannot_skip_tests(self):
        original = v2.CATALOG
        try:
            data = v2.catalog()
            data["packages"]["unsafe-trigger"] = {
                "policy_version": 2, "reviewed": True,
                "manifest": "manifest/sf-v2-environment-trigger.xml",
                "allowed_types": ["ApexTrigger"], "test_level": "NoTestRun", "tests": []}
            path = self.base / "catalog.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            v2.CATALOG = path
            with self.assertRaises(v2.PolicyError):
                v2.get_package("unsafe-trigger")
        finally:
            v2.CATALOG = original

    def test_candidate_and_remote_must_match_manifest_members(self):
        content = {
            "package.xml": (b'<Package xmlns="http://soap.sforce.com/2006/04/metadata">'
                            b'<types><members>branchMonitor</members><name>CustomTab</name></types>'
                            b'<version>67.0</version></Package>'),
            "tabs/branchMonitor.tab": b'<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata"/>'
        }
        for name, raw in content.items():
            item = self.candidate / name
            item.parent.mkdir(exist_ok=True)
            item.write_bytes(raw)
        self.assertTrue(v2.verify_payload(v2.from_dir(self.candidate), {"CustomTab": ["branchMonitor"]}))
        remote = self.base / "remote.zip"
        with ZipFile(remote, "w") as zipfile:
            for name, raw in content.items():
                zipfile.writestr("unpackaged/" + name, raw)
        self.assertEqual(v2.report("compare", "branch-monitor-tab-v2", remote, self.candidate)["result"], "equal")
        content["tabs/branchMonitor.tab"] = b'<CustomTab><secret>dont print</secret></CustomTab>'
        with ZipFile(remote, "w") as zipfile:
            for name, raw in content.items():
                zipfile.writestr("unpackaged/" + name, raw)
        result = v2.report("compare", "branch-monitor-tab-v2", remote, self.candidate)
        self.assertEqual(result["differing_files"], 1)
        self.assertNotIn("dont print", json.dumps(result))
        with ZipFile(remote, "w") as zipfile:
            zipfile.writestr("unpackaged/package.xml", content["package.xml"].replace(b"branchMonitor", b"unapproved"))
            zipfile.writestr("unpackaged/tabs/branchMonitor.tab", content["tabs/branchMonitor.tab"])
        with self.assertRaises(v2.PolicyError):
            v2.report("retrieve", "branch-monitor-tab-v2", remote)

    def test_zip_path_traversal_and_destructive_changes_denied(self):
        for path in ("unpackaged/../exfiltrate", "unpackaged/destructiveChangesPre.xml"):
            archive = self.base / "bad.zip"
            with ZipFile(archive, "w") as zipfile:
                zipfile.writestr("unpackaged/package.xml", b"<Package/>")
                zipfile.writestr(path, b"bad")
            with self.subTest(path=path), self.assertRaises(v2.PolicyError):
                v2.from_zip(archive)

    def test_v2_also_verifies_owner_sha_confirmation_and_secrets(self):
        for required in ("sf-m5-chatops-intent.py", "GITHUB_REPOSITORY_OWNER", "GITHUB_RUN_ATTEMPT",
                         "git rev-parse HEAD", "DEPLOY $TARGET $PACKAGE_ID",
                         "sf project deploy start --dry-run", "SDOA_REAL_DEPLOY_SUCCEEDED",
                         "SDOA_V2_DEPLOY_UNCONFIRMED", "sf project retrieve start",
                         "SDOA_EXPORT_RAW", "GITHUB_EVENT_REPOSITORY_PRIVATE"):
            self.assertIn(required, RUNNER)
        self.assertNotIn("set -x", RUNNER)
        self.assertIn("sf-kit-v2-policy.py resolve", WORKFLOW)
        self.assertIn("sf-kit-v2-execute.sh", WORKFLOW)
        self.assertIn("bash scripts/ci/sf-general-deploy.sh", WORKFLOW)
        self.assertIn("bash scripts/ci/sf-kit-read.sh", WORKFLOW)
        self.assertNotIn("pull_request_target:", WORKFLOW)


    def test_per_member_diff_maps_only_reviewed_metadata(self):
        members = {"ApexClass": ["Reviewed"], "LightningComponentBundle": ["included"],
                   "CustomTab": ["branchMonitor"]}
        self.assertEqual(v2.reviewed_owners("classes/Reviewed.cls", members), ["ApexClass:Reviewed"])
        self.assertEqual(v2.reviewed_owners("classes/Reviewed.cls-meta.xml", members), ["ApexClass:Reviewed"])
        self.assertEqual(v2.reviewed_owners("lwc/included/included.js", members),
                         ["LightningComponentBundle:included"])
        self.assertEqual(v2.reviewed_owners("tabs/branchMonitor.tab", members), ["CustomTab:branchMonitor"])
        self.assertEqual(v2.reviewed_owners("classes/Unreviewed.cls", members), [])
        self.assertEqual(v2.reviewed_owners("lwc/other/other.js", members), [])

    def test_custom_field_aggregate_diff_must_be_reported_as_ambiguous(self):
        pkg = (b'<Package xmlns="http://soap.sforce.com/2006/04/metadata">'
               b'<types><members>DevSre_EnvironmentMapping__c.Reason__c</members>'
               b'<name>CustomField</name></types><version>67.0</version></Package>')
        path = "objects/DevSre_EnvironmentMapping__c.object"
        self.assertEqual(v2.reviewed_owners(path, {"CustomField":
            ["DevSre_EnvironmentMapping__c.Reason__c"]}),
            ["CustomField:DevSre_EnvironmentMapping__c.Reason__c"])
        data = {"package.xml": pkg, path: b"<CustomObject><label>safe</label></CustomObject>"}
        for name, content in data.items():
            f = self.candidate / name
            f.parent.mkdir(exist_ok=True)
            f.write_bytes(content)
        remote = self.base / "remote-aggregate.zip"
        with ZipFile(remote, "w") as zipfile:
            zipfile.writestr("unpackaged/package.xml", pkg)
            zipfile.writestr("unpackaged/" + path,
                            b"<CustomObject><label>private changed</label></CustomObject>")
        response = v2.report("compare", "environment-reason-field-v2", remote, self.candidate)
        self.assertEqual(response["differing_files"], 1)
        self.assertEqual(response["differing_members"], [])
        self.assertEqual(response["ambiguous_candidates"],
                         ["CustomField:DevSre_EnvironmentMapping__c.Reason__c"])
        self.assertFalse(response["attribution_complete"])
        self.assertNotIn("private changed", json.dumps(response))

    def test_unreviewed_extra_payload_files_denied_even_with_valid_manifest(self):
        pkg = (b'<Package xmlns="http://soap.sforce.com/2006/04/metadata">'
               b'<types><members>branchMonitor</members><name>CustomTab</name></types>'
               b'<version>67.0</version></Package>')
        payload = {"package.xml": pkg, "tabs/branchMonitor.tab": b"original",
                   "tabs/Unreviewed.tab": b"org-private"}
        with self.assertRaises(v2.PolicyError):
            v2.verify_payload(payload, {"CustomTab": ["branchMonitor"]})

    def test_v2_jest_selects_exact_reviewed_lwc_suites(self):
        info, groups = v2.verify_config("branch-monitor-lwc-v2")
        self.assertEqual(groups, {"LightningComponentBundle": ["devSreBranchMonitor"]})
        self.assertEqual(info["effective_test_level"], "RunSpecifiedTests")
        files = v2.jest_files("branch-monitor-lwc-v2")
        self.assertEqual(files, [
            "force-app/main/default/lwc/devSreBranchMonitor/__tests__/devSreBranchMonitor.test.js"
        ])
        from unittest.mock import patch
        with patch.object(v2, "verify_config", return_value=({}, {
            "LightningComponentBundle": ["cleandatatable"]
        })):
            with self.assertRaises(v2.PolicyError):
                v2.jest_files("missing-jest-suite")

    def test_workflow_caches_pinned_cli_and_scopes_jest(self):
        for text in ("actions/cache@v4", "2.154.4",
                     "sf-kit-v2-policy.py jest-files", "sf-kit-v2-jest-verify.py",
                     "SDOA_V2_SF_CLI_PIN_VERIFIED", "Run only v2 manifest-scoped LWC Jest suites"):
            self.assertIn(text, WORKFLOW)
        self.assertIn("needs.resolve.outputs.policy_version != '2'", WORKFLOW)
        self.assertIn("steps.registry.outputs.has_lwc == 'true'", WORKFLOW)



    def test_jest_result_gate_rejects_non_scoped_suite_even_when_all_pass(self):
        from unittest.mock import patch
        spec = importlib.util.spec_from_file_location(
            "sdoa_jest_verify", ROOT / "scripts/ci/sf-kit-v2-jest-verify.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite = ROOT / "force-app/main/default/lwc/devSreBranchMonitor/__tests__/devSreBranchMonitor.test.js"
        wrong = ROOT / "force-app/main/default/lwc/clonePipelineAction/__tests__/clonePipelineAction.test.js"
        expected = "force-app/main/default/lwc/devSreBranchMonitor/__tests__/devSreBranchMonitor.test.js"
        report = {
            "success": True,
            "numFailedTestSuites": 0, "numFailedTests": 0,
            "numPassedTestSuites": 1, "numPassedTests": 2,
            "testResults": [{"name": str(suite), "status": "passed"}],
        }
        self.assertEqual(module.verify(report, [expected], ROOT), (1, 2))
        extra = dict(report, numPassedTestSuites=2,
                     testResults=report["testResults"] + [{"name": str(wrong), "status": "passed"}])
        with self.assertRaises(module.JestScopeError):
            module.verify(extra, [expected], ROOT)
        wrong_only = dict(report, testResults=[{"name": str(wrong), "status": "passed"}])
        with self.assertRaises(module.JestScopeError):
            module.verify(wrong_only, [expected], ROOT)
        with self.assertRaises(module.JestScopeError):
            module.verify(dict(report, success=False), [expected], ROOT)

    def test_jest_workflow_forwards_flags_after_separator_and_verifies_json(self):
        self.assertIn("sfdx-lwc-jest -- --runInBand --runTestsByPath", WORKFLOW)
        self.assertIn("--json --outputFile", WORKFLOW)
        self.assertIn("sf-kit-v2-jest-verify.py --json", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
