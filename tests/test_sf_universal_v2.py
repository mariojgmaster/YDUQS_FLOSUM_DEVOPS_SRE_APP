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


if __name__ == "__main__":
    unittest.main()
