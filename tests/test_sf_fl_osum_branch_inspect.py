import importlib.util
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"scripts/ci/sf-flosum-branch-inspect.py"
spec=importlib.util.spec_from_file_location("flosum_inspector",PATH)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
FAKE_ID="a0B"+"123456789012345"


def branch_fields():
    return {"Id":{"type":"id"},
            "Flosum__Organization__c":{"type":"reference","referenceTo":["Flosum__Org__c"]},
            "Flosum__Commit__c":{"type":"reference","referenceTo":["git__Git_Commit__c"]}}

def log_fields():
    return {"Id":{"type":"id"},"CreatedDate":{"type":"datetime"},
            "Flosum__Branch__c":{"type":"reference","referenceTo":["Flosum__Branch__c"]},
            "Flosum__Status__c":{"type":"picklist"},
            "Flosum__Completed_Date__c":{"type":"datetime"}}


class BranchInspectionTests(unittest.TestCase):
    def test_one_branch_and_bounded_logs(self):
        statements=[]
        def schema(name):
            return branch_fields() if name==m.BRANCH else log_fields()
        def query(soql):
            statements.append(soql)
            if "FROM Flosum__Branch__c" in soql:
                return [{"Id":FAKE_ID,"Flosum__Organization__c":"hidden",
                         "Flosum__Commit__c":None}]
            return [{"Id":"hidden","CreatedDate":"hidden","Flosum__Status__c":"hidden",
                     "Flosum__Completed_Date__c":"hidden"}]
        output=StringIO()
        with redirect_stdout(output):
            m.inspect(FAKE_ID,schema,query)
        self.assertEqual(len(statements),2)
        self.assertIn("LIMIT 1",statements[0])
        self.assertIn("LIMIT 8",statements[1])
        self.assertIn("WHERE Flosum__Branch__c =",statements[1])
        self.assertIn("category=organization populated=1",output.getvalue())
        self.assertIn("FLOSUM_METADATA_LOG_LINK: verified=true",output.getvalue())
        self.assertNotIn(FAKE_ID,output.getvalue())
        self.assertNotIn("hidden",output.getvalue())

    def test_no_join_is_reported_without_log_query(self):
        statements=[]
        def schema(name):
            return branch_fields() if name==m.BRANCH else {"Id":{"type":"id"}}
        def fetch(s):
            statements.append(s)
            return [{"Id":FAKE_ID}]
        output=StringIO()
        with redirect_stdout(output):
            m.inspect(FAKE_ID,schema,fetch)
        self.assertEqual(len(statements),1)
        self.assertIn("reason=no_direct_reference",output.getvalue())

    def test_rejects_injected_id(self):
        for value in ("", "bad", FAKE_ID+"' OR 1=1", FAKE_ID+"; SELECT", "a0B123456789012345999"):
            with self.assertRaises(m.AuditError):
                m.inspect(value,lambda x: {},lambda x: [])
        self.assertEqual(len(FAKE_ID),18)

    def test_workflow_requires_manual_owner_and_no_embedded_id(self):
        y=(ROOT/".github/workflows/sf-devsrefeat-diagnostics.yml").read_text("utf-8")
        self.assertIn("flosum-branch-inspect",y)
        self.assertIn("inputs.branch_id",y)
        self.assertIn('sf-flosum-branch-inspect.py --branch-id "$BRANCH_RECORD_ID"',y)
        self.assertIn('"$GITHUB_ACTOR" != "$GITHUB_REPOSITORY_OWNER"',y)
        self.assertNotIn(FAKE_ID,PATH.read_text("utf-8"))
        self.assertNotIn("sf project deploy",PATH.read_text("utf-8"))


if __name__=="__main__":
    unittest.main()
