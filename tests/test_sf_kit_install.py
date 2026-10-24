"""Idempotent, hash-pinned Salesforce DevOps Kit installation regression."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sf_kit_install", ROOT/"scripts/ci/sf-kit-install.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InstallationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.dest = self.base/"target"
        self.dest.mkdir()
        (self.dest/"sfdx-project.json").write_text("{}", encoding="utf8")
        (self.dest/"config/salesforce-devops").mkdir(parents=True)
        (self.dest/"config/salesforce-devops/catalog.json").write_text(json.dumps({
            "schema": 1, "targets": {"lab": {"kind": "sandbox"}},
            "packages": {"apex": {"manifest": "manifest/approved.xml"}}
        }), encoding="utf8")
        self.source = self.base/"source"
        shutil.copytree(ROOT/"templates/salesforce-devops-kit", self.source/"templates/salesforce-devops-kit")

    def approve(self):
        manifest = self.source/module.MANIFEST
        data = json.loads(manifest.read_text("utf8"))
        data["status"] = "approved"
        manifest.write_text(json.dumps(data), encoding="utf8")

    def test_preview_and_approval_gate(self):
        preview = module.install(self.source, self.dest)
        self.assertEqual(len(preview), 9)
        self.assertTrue(all(state=="missing" for _, state in preview))
        with self.assertRaises(module.InstallationError):
            module.install(self.source, self.dest, apply=True)

    def test_install_idempotent_and_no_overwrite(self):
        self.approve()
        first = module.install(self.source, self.dest, apply=True)
        self.assertEqual(len([1 for _, status in first if status=="created"]), 9)
        second = module.install(self.source, self.dest, apply=True)
        self.assertTrue(all(status=="unchanged" for _, status in second))
        modified = self.dest/".github/workflows/sf-m5-chatops-plan.yml"
        modified.write_text("malicious overwrite",encoding="utf8")
        with self.assertRaises(module.InstallationError):
            module.install(self.source, self.dest, apply=True)
        self.assertEqual(modified.read_text(), "malicious overwrite")

    def test_any_conflict_prevents_partial_install(self):
        self.approve()
        f = self.dest/"scripts/ci/sf-deploy-policy.py"
        f.parent.mkdir(parents=True)
        f.write_text("existing policy",encoding="utf8")
        with self.assertRaises(module.InstallationError):
            module.install(self.source, self.dest, apply=True)
        self.assertFalse((self.dest/".github/workflows/sf-m5-chatops-plan.yml").exists())

    def test_template_hash_mutation_refused(self):
        self.approve()
        f = self.source/"templates/salesforce-devops-kit/v1/files/scripts/ci/sf-kit-read.sh"
        f.write_text(f.read_text()+"\nDESTRUCTIVE_UNREVIEWED_CHANGE\n",encoding="utf8")
        with self.assertRaises(module.InstallationError):
            module.install(self.source, self.dest, apply=True)

    def test_symlink_and_path_escape_refused(self):
        self.approve()
        f = self.dest/".github"
        f.symlink_to(self.base, target_is_directory=True)
        with self.assertRaises(module.InstallationError):
            module.install(self.source, self.dest, apply=True)
        with self.assertRaises(module.InstallationError):
            module.safe_child(self.dest, "../escape")


if __name__ == "__main__":
    unittest.main()
