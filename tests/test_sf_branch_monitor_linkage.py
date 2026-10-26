"""Unit tests for bounded read-only Branch Monitor Flosum linkage diagnostics."""
import importlib.util
import io
import json
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/ci/sf-flosum-branch-monitor-linkage.py"
spec=importlib.util.spec_from_file_location("bm_linkage", SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def event(owner="mariojgmaster", body=m.BODY):
    return {"action":"opened","issue":{"title":m.TITLE,"body":body,"user":{"login":owner}},
            "sender":{"login":owner},"repository":{"owner":{"login":owner}}}

class BranchHistoryLinkageSafety(unittest.TestCase):
    def test_exact_owner_and_body_required(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"event.json"
            p.write_text(json.dumps(event()),encoding="utf-8")
            m.verify_issue(p,"mariojgmaster")
            p.write_text(json.dumps(event(body=m.BODY+"\noperation=deploy")),encoding="utf-8")
            with self.assertRaises(m.Block): m.verify_issue(p,"mariojgmaster")
            p.write_text(json.dumps(event(owner="stranger")),encoding="utf-8")
            with self.assertRaises(m.Block): m.verify_issue(p,"mariojgmaster")

    def test_only_unique_typed_foreign_key_allowed(self):
        fields=[
            {"name":"Flosum__Branch__c","type":"reference","referenceTo":[m.BRANCH]},
            {"name":"Flosum__Parent__c","type":"string","referenceTo":[m.BRANCH]}
        ]
        self.assertEqual(m.foreign_key({"fields":fields},m.BRANCH),"Flosum__Branch__c")
        with self.assertRaises(m.Block): m.foreign_key({"fields":fields+fields[:1]},m.BRANCH)
        with self.assertRaises(m.Block): m.foreign_key({"fields":[]},m.BRANCH)

    def test_positive_sample_and_complete_public_redaction(self):
        cid="a0A000000000001AAA"
        bid="a0B000000000002AAA"
        hid="a0C000000000003AAA"
        calls=[]
        def reader(q):
            calls.append(q)
            if "FROM "+m.HISTORY in q:
                return [{"Id":hid,"Flosum__Component__c":cid}]
            if "WHERE Id IN" in q:
                return [{"Id":cid,"Flosum__Branch__c":bid}]
            return [{"Id":cid,"Flosum__Branch__c":bid}]
        with redirect_stdout(io.StringIO()) as output:
            result=m.evaluate("Flosum__Branch__c","Flosum__Component__c",reader)
            print("FLOSUM_LINKAGE_SAMPLE:",result)
        self.assertEqual(result["history_component_refs_with_branch"],1)
        self.assertEqual(result["history_refs_resolved_to_accessible_component"],1)
        self.assertEqual(result["link_quality"],"positive_sample_only")
        self.assertNotIn(cid,output.getvalue())
        self.assertNotIn(bid,output.getvalue())
        self.assertTrue(all(" LIMIT 101" in q for q in calls))

    def test_incomplete_and_unlinked_not_certified(self):
        def reader(q):
            return [] if "FROM "+m.HISTORY in q or "WHERE Id IN" in q else [{
                "Id":"a0A000000000001AAA","Flosum__Branch__c":"a0B000000000002AAA"
            }]
        result=m.evaluate("Flosum__Branch__c","Flosum__Component__c",reader)
        self.assertEqual(result["link_quality"],"not_demonstrated")
        self.assertEqual(result["history_sample"],0)

    def test_schema_field_injection_and_id_injection_blocked(self):
        with self.assertRaises(m.Block):
            m.evaluate("Flosum__Branch__c FROM User","Flosum__Component__c",lambda _:[])
        with self.assertRaises(m.Block):
            m.validate_ids(["x';DELETE FROM ApexClass"])
        with self.assertRaises(m.Block):
            m.validate_ids(["a0A000000000001AAA"]*101)

if __name__=="__main__": unittest.main()
