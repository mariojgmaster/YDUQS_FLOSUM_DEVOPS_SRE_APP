import importlib.util
import unittest
import json
import tempfile
from unittest.mock import patch
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
        self.assertIn("branch_id:",y)
        self.assertNotIn("inputs.branch_id",y)
        self.assertNotIn("BRANCH_RECORD_ID",y)
        self.assertNotIn("--branch-id",y)
        self.assertIn("python3 scripts/ci/sf-flosum-branch-inspect.py",y)
        self.assertIn('"$GITHUB_ACTOR" != "$GITHUB_REPOSITORY_OWNER"',y)
        self.assertNotIn(FAKE_ID,PATH.read_text("utf-8"))
        self.assertNotIn("sf project deploy",PATH.read_text("utf-8"))

    def test_two_links_are_queried_separately_with_overlap_and_org_counts(self):
        fields=log_fields()
        fields["Flosum__Other_Branch__c"]={"type":"reference","referenceTo":[m.BRANCH]}
        fields["Flosum__Organisation__c"]={"type":"reference","referenceTo":["Flosum__Organisation__c"]}
        statements=[]
        def fetch(sql):
            statements.append(sql)
            if f"FROM {m.BRANCH}" in sql:
                return [{"Id":FAKE_ID}]
            return [{"Id":"private-log", "Flosum__Organisation__c":"private-org"}]
        output=StringIO()
        with redirect_stdout(output):
            m.inspect(FAKE_ID,lambda name: branch_fields() if name==m.BRANCH else fields,fetch)
        self.assertEqual(len(statements),3)
        self.assertIn("WHERE Flosum__Branch__c =",statements[1])
        self.assertIn("WHERE Flosum__Other_Branch__c =",statements[2])
        for sql in statements[1:]:
            self.assertIn("LIMIT 8",sql)
            self.assertIn("Flosum__Organisation__c",sql)
        self.assertIn("organization_references=1",output.getvalue())
        self.assertIn("organization_populated=1",output.getvalue())
        self.assertIn("unique_sample_rows=1 overlap_sample_rows=1 canonical_link_verified=false",output.getvalue())
        for value in (FAKE_ID,"private-log","private-org","Flosum__Other_Branch__c","Flosum__Organisation__c"):
            self.assertNotIn(value,output.getvalue())

    def test_more_than_two_links_does_not_query_logs(self):
        fields=log_fields()
        for name in ("Flosum__Other_Branch__c","Flosum__Third_Branch__c"):
            fields[name]={"type":"reference","referenceTo":[m.BRANCH]}
        statements=[]
        def fetch(sql):
            statements.append(sql)
            return [{"Id":FAKE_ID}]
        output=StringIO()
        with redirect_stdout(output):
            m.inspect(FAKE_ID,lambda name: branch_fields() if name==m.BRANCH else fields,fetch)
        self.assertEqual(len(statements),1)
        self.assertIn("reason=link_limit_exceeded",output.getvalue())

    def test_oversized_log_result_is_rejected(self):
        def fetch(sql):
            return [{"Id":FAKE_ID}] if f"FROM {m.BRANCH}" in sql else [{"Id":"private"}]*9
        with redirect_stdout(StringIO()), self.assertRaises(m.AuditError):
            m.inspect(FAKE_ID,lambda name: branch_fields() if name==m.BRANCH else log_fields(),fetch)

    def test_workflow_input_loaded_without_echoing_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            event=Path(tmp)/"event.json"
            event.write_text(json.dumps({"inputs":{"branch_id":FAKE_ID}}),encoding="utf-8")
            output=StringIO()
            with patch.dict(m.os.environ,{"GITHUB_EVENT_PATH":str(event)}),redirect_stdout(output):
                self.assertEqual(m.event_branch_id(),FAKE_ID)
                event.write_text(json.dumps({"inputs":{"branch_id":FAKE_ID+"'"}}),encoding="utf-8")
                with self.assertRaises(m.AuditError):
                    m.event_branch_id()
                event.write_text("{}",encoding="utf-8")
                with self.assertRaises(m.AuditError):
                    m.event_branch_id()
            self.assertEqual(output.getvalue(),"")


if __name__=="__main__":
    unittest.main()
