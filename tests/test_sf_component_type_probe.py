"""Tests for strictly scoped component-type metadata read-only probe."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("probe",ROOT/"scripts/ci/sf-flosum-component-type-probe.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ProbeTests(unittest.TestCase):
    def test_schema_resolves_candidate_shape_without_labels_or_values(self):
        fields=[
            {"name":"Flosum__Component_Type__c","label":"Component Type","type":"reference","referenceTo":["Flosum__Type__c"],"accessible":True},
            {"name":"Flosum__Component_Type_Text__c","label":"Component Type Name","type":"picklist","picklistValues":[{"value":"COMPANY_PRIVATE"}]},
            {"name":"Name","label":"Company confidential","type":"string"}]
        x=m.analyze(fields)
        self.assertEqual(2,len(x))
        self.assertEqual("reference",x[0]["kind"])
        self.assertTrue(x[0]["target_fl_namespace"])
        self.assertEqual(1,x[1]["picklist_values"])
        self.assertNotIn("COMPANY_PRIVATE",json.dumps(x))
        self.assertNotIn("Component_Type__c",json.dumps(x))
    def test_unapproved_owner_cannot_run(self):
        event={"action":"opened","sender":{"login":"owner"},"repository":{"owner":{"login":"owner"}},
        "issue":{"user":{"login":"owner"},"title":m.TITLE,"body":m.BODY}}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"event.json";p.write_text(json.dumps(event))
            m.verify(p,"owner")
            with self.assertRaises(m.Block):m.verify(p,"other")
if __name__=="__main__":unittest.main()
