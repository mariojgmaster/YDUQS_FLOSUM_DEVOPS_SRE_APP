import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('spec004',ROOT/'scripts/ci/sf-spec004-validate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class ValidationTests(unittest.TestCase):
    def test_exact_owner_event_and_no_retry(self):
        ctx={'GITHUB_REPOSITORY_OWNER':'owner','GITHUB_ACTOR':'owner','GITHUB_REF':'refs/heads/master','GITHUB_RUN_ATTEMPT':'1','GITHUB_EVENT_NAME':'issues'}
        event={'action':'opened','sender':{'login':'owner'},'issue':{'title':m.TITLE,'body':m.BODY+'\n','user':{'login':'owner'}}}
        m.verify_event(event,ctx)
        for key,value in [('GITHUB_ACTOR','attacker'),('GITHUB_REF','refs/heads/unreviewed'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','push')]:
            wrong=dict(ctx);wrong[key]=value
            with self.assertRaises(m.Invalid):m.verify_event(event,wrong)
        event['issue']['body']+='operation=deploy'
        with self.assertRaises(m.Invalid):m.verify_event(event,ctx)

    def test_manifest_is_scoped_without_managed_objects(self):
        config=m.package_policy()
        self.assertEqual(config['members']['CustomObject'],['DevSre_EnvironmentMapping__c'])
        self.assertEqual(config['members']['CustomTab'],['pipelineMonitor'])
        self.assertEqual(config['tests'],['DevSreEnvironmentTest','DevSreDeploymentTest'])
        self.assertNotIn('CustomApplication',config['members'])

    def test_navigation_drift_fails_and_known_states_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive=Path(tmp)/'nav.zip'
            before=(ROOT/'config/spec004/pipelineMonitor.original.xml').read_bytes()
            after=(ROOT/'force-app/main/default/tabs/pipelineMonitor.tab-meta.xml').read_bytes()
            for content in (before,after):
                with zipfile.ZipFile(archive,'w') as z:z.writestr('unpackaged/tabs/pipelineMonitor.tab',content)
                m.check_navigation(archive)
            with zipfile.ZipFile(archive,'w') as z:z.writestr('unpackaged/tabs/pipelineMonitor.tab',before.replace(b'Custom39',b'Custom40'))
            with self.assertRaises(m.Invalid):m.check_navigation(archive)

    def test_converted_package_rejects_unreviewed_files(self):
        config=m.package_policy()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for typ,names in config['members'].items():
                directory,suffix={'ApexClass':('classes','.cls'),'ApexTrigger':('triggers','.trigger'),'CustomObject':('objects','.object'),'CustomPermission':('customPermissions','.customPermission'),'PermissionSet':('permissionsets','.permissionset'),'CustomTab':('tabs','.tab'),'Layout':('layouts','.layout'),'LightningComponentBundle':('lwc','.js-meta.xml')}[typ]
                for name in names:
                    path=root/directory/name/(name+suffix) if typ=='LightningComponentBundle' else root/directory/(name+suffix)
                    path.parent.mkdir(parents=True,exist_ok=True);path.write_text('synthetic')
                    if typ in ('ApexClass','ApexTrigger'):path.with_name(path.name+'-meta.xml').write_text('synthetic')
            m.converted_policy(root,config)
            (root/'objects/Flosum__Metadata_Log__c.object').write_text('forbidden')
            with self.assertRaises(m.Invalid):m.converted_policy(root,config)

    def test_no_persistent_deploy_command(self):
        with self.assertRaises(m.Invalid):m.cli(['project','deploy','start'],'forbidden',{'phases':{}})
        y=(ROOT/'.github/workflows/sf-spec004-validate.yml').read_text()
        self.assertNotIn('pull_request_target',y)
        self.assertNotIn('github.event.issue.body }}',y)
        self.assertIn('environment: sf-devsrefeat-read',y)
        self.assertIn('spec004-validation.cms',y)
        self.assertIn('retention-days: 1',y)

    def test_history_layout_uses_metadata_related_list_identifier(self):
        layout=m.ET.parse(ROOT/'force-app/main/default/layouts/DevSre_EnvironmentMapping__c-Environment Mapping.layout-meta.xml').getroot()
        names=[x.text for x in layout.findall('m:relatedLists/m:relatedList',m.NS)]
        self.assertNotIn('Histories',names)
        self.assertIn('RelatedEntityHistoryList',names)
        obj=m.ET.parse(ROOT/'force-app/main/default/objects/DevSre_EnvironmentMapping__c/DevSre_EnvironmentMapping__c.object-meta.xml').getroot()
        self.assertEqual(obj.findtext('m:enableHistory',namespaces=m.NS),'true')

    def test_xml_is_parseable_and_config_is_not_seeded_with_ids(self):
        paths=list((ROOT/'force-app/main/default/objects/DevSre_EnvironmentMapping__c').rglob('*.xml'))
        for path in paths:m.ET.parse(path)
        self.assertNotIn('records',json.loads((ROOT/'config/spec004/package.json').read_text()))


if __name__=='__main__':unittest.main()
