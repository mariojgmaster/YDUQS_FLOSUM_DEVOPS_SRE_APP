import importlib.util
from pathlib import Path
import json
import tempfile
import unittest

SOURCE=Path(__file__).resolve().parents[1]/"scripts/ci/sf-flosum-component-research.py"
spec=importlib.util.spec_from_file_location("component_research",SOURCE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def issue(owner="mariojgmaster", title=mod.TITLE, body=mod.BODY):
    return {"action":"opened","issue":{"title":title,"body":body,"user":{"login":owner}},
            "sender":{"login":owner},"repository":{"owner":{"login":owner}}}

class ComponentsResearchSafety(unittest.TestCase):
    def test_exact_owner_intent(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"event.json"
            p.write_text(json.dumps(issue()),encoding="utf-8")
            mod.verify_issue(p,"mariojgmaster")
            p.write_text(json.dumps(issue(body=mod.BODY+"\n--deploy")),encoding="utf-8")
            with self.assertRaises(mod.Block): mod.verify_issue(p,"mariojgmaster")
            p.write_text(json.dumps(issue(owner="other")),encoding="utf-8")
            with self.assertRaises(mod.Block): mod.verify_issue(p,"mariojgmaster")
    def test_known_relationships_only(self):
        data={"fields":[
            {"name":"Flosum__Branch__c","type":"reference","referenceTo":["Flosum__Branch__c"]},
            {"name":"Flosum__Component__c","type":"reference","referenceTo":["Flosum__Components__c"]},
            {"name":"Flosum__Changed__c","type":"string"},
            {"name":"Flosum__Body__c","type":"textarea"},
        ]}
        refs=mod.summarize(mod.OBJECTS[2],data)
        self.assertEqual(len(refs["branch"]),1)
        self.assertEqual(len(refs["component"]),1)
        self.assertEqual(len(refs["log"]),0)
    def test_fixed_object_allowlist(self):
        self.assertEqual(mod.OBJECTS,("Flosum__Components__c","Flosum__Component__c","Flosum__Component_History__c"))

if __name__=="__main__": unittest.main()
