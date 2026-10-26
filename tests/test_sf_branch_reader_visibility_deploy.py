"""Fail-closed regression tests for the single Branch Monitor Reader visibility patch."""
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("sf_deploy_policy", ROOT/"scripts/ci/sf-deploy-policy.py")
policy=importlib.util.module_from_spec(s);s.loader.exec_module(policy)
NAME="DevSreBranchMonitor_Reader"
SOURCE=ROOT/"force-app/main/default/permissionsets"/(NAME+".permissionset-meta.xml")
MDAPI_PATH=f"permissionsets/{NAME}.permissionset"

class ReaderVisibilityScopeTests(unittest.TestCase):
    def test_exact_package_registered_and_fully_scoped(self):
        cat=policy.registry()
        info=policy.pkg_info(cat,"branch-monitor-reader-visibility")
        self.assertEqual(info["allowed_types"],["PermissionSet"])
        self.assertEqual(info["tests"],["DevSreBranchMonitorTest"])
        self.assertEqual(policy.members(info),{"PermissionSet":[NAME]})
        self.assertEqual(policy.target(cat,"DevSreFeat")["kind"],"sandbox")
    def test_reader_xml_and_candidate_required(self):
        content=SOURCE.read_bytes()
        self.assertTrue(policy.verify_reader_visibility_change(content))
        data={"package.xml":b"<Package/>",MDAPI_PATH:content}
        self.assertEqual(policy.selected(data,{"PermissionSet":[NAME]}),{MDAPI_PATH})
        self.assertEqual(policy.compare(data,data,{"PermissionSet":[NAME]}),(True,0))
        self.assertEqual(policy.mismatched_file_types(data,data,{"PermissionSet":[NAME]}),[])
        changed=dict(data)
        changed[MDAPI_PATH]=content.replace(b"<visibility>Visible</visibility>",b"<visibility>Hidden</visibility>")
        with self.assertRaises(policy.PolicyError):policy.selected(changed,{"PermissionSet":[NAME]})
    def test_no_unreviewed_permission_expansion(self):
        content=SOURCE.read_bytes()
        addition=b"<userPermissions><enabled>true</enabled><name>ModifyAllData</name></userPermissions>"
        changed=content.replace(b"</PermissionSet>",addition+b"</PermissionSet>")
        with self.assertRaises(policy.PolicyError):policy.verify_reader_visibility_change(changed)
        changed=content.replace(b"<apexClass>DevSreBranchMonitorController</apexClass>",
                                b"<apexClass>SystemAdminController</apexClass>")
        with self.assertRaises(policy.PolicyError):policy.verify_reader_visibility_change(changed)
        changed=content.replace(b"<tab>branchMonitor</tab>",b"<tab>OtherTab</tab>")
        with self.assertRaises(policy.PolicyError):policy.verify_reader_visibility_change(changed)
    def test_unrelated_packages_cannot_deploy_permissionsets(self):
        cat=policy.registry()
        for typ in ["ApexClass","LightningComponentBundle"]:
            cat["packages"]["other"]={
                "manifest":"manifest/sf-branch-monitor-reader-visibility.xml",
                "test_level":"RunSpecifiedTests",
                "tests":["DevSreBranchMonitorTest"],
                "allowed_types":[typ,"PermissionSet"]
            }
            with self.assertRaises(policy.PolicyError):policy.pkg_info(cat,"other")
        with self.assertRaises(policy.PolicyError):
            policy.selected({"package.xml":b"<Package/>",
                MDAPI_PATH:SOURCE.read_bytes(),"classes/Sneaky.cls":b"private"},
                {"PermissionSet":[NAME]})
        with self.assertRaises(policy.PolicyError):
            policy.selected({"package.xml":b"<Package/>",MDAPI_PATH:SOURCE.read_bytes()},
                {"PermissionSet":["AnotherReader"]})
    def test_reader_drift_uses_allowlisted_identifier_only(self):
        original={"package.xml":b"<Package/>",MDAPI_PATH:SOURCE.read_bytes()}
        # The deployment path forbids any unexpected values. A normal comparison is identical.
        self.assertEqual(policy.mismatched_components(original,original,{"PermissionSet":[NAME]}),[])
        self.assertTrue(policy.members(policy.pkg_info(policy.registry(),
            "branch-monitor-reader-visibility")))

if __name__=="__main__":unittest.main()
