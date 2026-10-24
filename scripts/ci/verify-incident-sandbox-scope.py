"""Valida a allowlist exata do manifesto Salesforce (sem segredos)."""
from pathlib import Path
from xml.etree import ElementTree as ET
import json

root = Path("manifest/sf-devops-sre-incidents-sandbox-validate.xml")
ns = "{http://soap.sforce.com/2006/04/metadata}"
doc = ET.parse(root).getroot()
entries = {}
for t in doc.findall(ns + "types"):
    key = t.findtext(ns + "name")
    assert key not in entries, f"Tipo duplicado: {key}"
    entries[key] = [x.text for x in t.findall(ns + "members")]

expected = {
    "CustomObject": ["DevSre_Incident__c", "DevSre_RecoveryAction__c"],
    "ApexClass": ["DevSreIncidentController", "DevSreIncidentControllerTest"],
    "LightningComponentBundle": ["devSreIncidentIntake", "devSreIncidentsHost"],
    "CustomPermission": ["DevSre_ReviewIncidentCausality"],
    "PermissionSet": ["DevSreIncident_Reader", "DevSreIncident_Operator"],
    "Group": ["DevSre_Incident_RMs"],
    "SharingRules": ["DevSre_Incident__c", "DevSre_RecoveryAction__c"],
    "CustomTab": ["incidentsRollbacks"]
}
assert entries == expected, "Manifest nao corresponde a allowlist aprovada"
assert doc.findtext(ns+"version") == "67.0"
obj = json.loads(Path("config/salesforce-devops/catalog.json").read_text())
target=obj["targets"].get("DevSreFeat")
assert target == {
    "github_environment":"sf-devsrefeat-read",
    "instance_url":"https://yduqs--devsrefeat.sandbox.my.salesforce.com",
    "kind":"sandbox",
}
print("PASS: DEV_SRE_FEAT_MANIFEST_SCOPE")
