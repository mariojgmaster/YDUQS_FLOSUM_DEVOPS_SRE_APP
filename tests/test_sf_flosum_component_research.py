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
    def test_role_profile_is_typed_but_does_not_expose_field_names(self):
        description={"fields":[
            {"name":"Flosum__Branch__c","type":"reference","referenceTo":["Flosum__Branch__c"]},
            {"name":"Flosum__Component_Key__c","type":"string"},
            {"name":"Flosum__Component_Link__c","type":"reference","referenceTo":["Flosum__Component__c"]},
            {"name":"Flosum__Version__c","type":"string"},
            {"name":"Flosum__Code_Body__c","type":"textarea"},
            {"name":"Flosum__SecretKey__c","type":"encryptedstring"},
        ]}
        roles=mod.role_profile(description)
        self.assertEqual(roles["branch"],{"reference":1})
        self.assertEqual(roles["component"],{"reference":1,"string":1})
        self.assertEqual(roles["version"],{"string":1})
        self.assertEqual(roles["body"],{"textarea":1})
        self.assertNotIn("secret",roles)
        import io
        from contextlib import redirect_stdout
        buf=io.StringIO()
        with redirect_stdout(buf): mod.print_role_profile("Flosum__Component_History__c",description)
        output=buf.getvalue()
        self.assertIn("candidate_types=reference:1,string:1",output)
        self.assertNotIn("Component_Key",output)
        self.assertNotIn("SecretKey",output)
    def test_invalid_schema_blocked(self):
        with self.assertRaises(mod.Block): mod.role_profile({"fields":None})
        with self.assertRaises(mod.Block): mod.role_profile({"fields":[{}]*5001})
    def test_singular_component_reference_classified(self):
        result=mod.summarize("Flosum__Component_History__c",{"fields":[
            {"name":"Flosum__Component__c","type":"reference",
             "referenceTo":["Flosum__Component__c"]},
        ]})
        self.assertEqual(len(result["component"]),1)

    def test_fixed_object_allowlist(self):
        self.assertEqual(mod.OBJECTS,("Flosum__Components__c","Flosum__Component__c","Flosum__Component_History__c"))

if __name__=="__main__": unittest.main()
