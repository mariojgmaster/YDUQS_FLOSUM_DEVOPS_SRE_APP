import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
mod=importlib.util.spec_from_file_location("policy",ROOT/"scripts/ci/sf-deploy-policy.py")
policy=importlib.util.module_from_spec(mod);mod.loader.exec_module(policy)
NAME="DevSreBranchMonitor_Reader"
FILE=ROOT/"force-app/main/default/permissionsets"/(NAME+".permissionset-meta.xml")

class M2ReaderPermissionTests(unittest.TestCase):
    def test_allowlisted_package_exact_reader_and_tests(self):
        cat=policy.registry()
        info=policy.pkg_info(cat,"branch-monitor-m2-reader")
        self.assertEqual({"PermissionSet":[NAME]},policy.members(info))
        self.assertEqual(["DevSreComponentDescriberTest","DevSreBranchMonitorTest"],info["tests"])
        source=FILE.read_bytes()
        self.assertTrue(policy.verify_reader_visibility_change(source))
        package={"package.xml":b"<Package/>",f"permissionsets/{NAME}.permissionset":source}
        self.assertEqual({"permissionsets/"+NAME+".permissionset"},policy.selected(package,{"PermissionSet":[NAME]}))
    def test_missing_or_added_apex_class_denied(self):
        source=FILE.read_bytes()
        grant=b'<classAccesses><apexClass>DevSreComponentDescriberController</apexClass><enabled>true</enabled></classAccesses>'
        with self.assertRaises(policy.PolicyError):policy.verify_reader_visibility_change(source.replace(grant,b""))
        extra=b'<classAccesses><apexClass>SystemAdminController</apexClass><enabled>true</enabled></classAccesses>'
        with self.assertRaises(policy.PolicyError):policy.verify_reader_visibility_change(source.replace(b"</PermissionSet>",extra+b"</PermissionSet>"))
        with self.assertRaises(policy.PolicyError):policy.verify_reader_visibility_change(source.replace(b"<visibility>Visible</visibility>",b"<visibility>Hidden</visibility>"))
    def test_other_permission_sets_still_not_supported(self):
        catalog=policy.registry()
        catalog["packages"]["wrong"]={"manifest":"manifest/sf-branch-monitor-m2-reader.xml",
            "test_level":"RunSpecifiedTests","tests":["DevSreComponentDescriberTest"],
            "allowed_types":["PermissionSet"]}
        with self.assertRaises(policy.PolicyError):policy.pkg_info(catalog,"wrong")
if __name__=="__main__":unittest.main()
