"""Archive discovery must never disclose IDs, filenames, content or unauthorized operations."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("probe",ROOT/"scripts/ci/sf-flosum-archive-link-probe.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ArchiveProbeTests(unittest.TestCase):
    def test_intent_validated(self):
        event={"action":"opened","sender":{"login":"owner"},"repository":{"owner":{"login":"owner"}},
               "issue":{"user":{"login":"owner"},"title":m.TITLE,"body":m.BODY}}
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"evt";f.write_text(json.dumps(event))
            m.verify(f,"owner")
            with self.assertRaises(m.Block):m.verify(f,"other")
    def test_counts_only_and_restricts_payload(self):
        recorded=[]
        def read(query,limit):
            recorded.append(query)
            if "Component_History__c" in query:return [{"Id":"a0B000000000001"}]
            if " FROM Attachment " in query:return [
                {"Id":"00P000000000001","Name":"Private.zip","BodyLength":250},
                {"Id":"00P000000000002","Name":"Private.txt","BodyLength":250}]
            if " FROM ContentDocumentLink " in query:return []
            raise AssertionError(query)
        x=m.probe(read)
        self.assertEqual(1,x["attachment_zip_count"])
        self.assertEqual(1,x["attachment_small_zip_count"])
        self.assertEqual(0,x["files_count"])
        self.assertNotIn("Private",json.dumps(x))
        self.assertTrue(all("Body FROM" not in q for q in recorded))
    def test_rejects_untrusted_ids(self):
        with self.assertRaises(m.Block):
            m.probe(lambda q,l: [{"Id":"'; DELETE"}])
if __name__=="__main__":unittest.main()
