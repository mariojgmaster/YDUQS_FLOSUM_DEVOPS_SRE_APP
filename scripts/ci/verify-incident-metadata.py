"""Validacao estrutural e invariantes de seguranca do MVP de incidentes.

Nao substitui Metadata API dry-run, Apex tests nem testes de permissao na org.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

NS = "{http://soap.sforce.com/2006/04/metadata}"
ROOT = Path("force-app/main/default")
OBJECTS = ["DevSre_Incident__c", "DevSre_RecoveryAction__c"]


def read(path):
    element = ET.parse(path).getroot()
    assert element.tag.startswith(NS), f"Namespace inesperado: {path}"
    return element


def value(element, tag):
    child = element.find(NS + tag)
    return child.text if child is not None else None


count = 0
for root in [
    ROOT / "objects" / object_name for object_name in OBJECTS
] + [
    ROOT / "permissionsets",
    ROOT / "tabs",
    ROOT / "classes",
    ROOT / "lwc" / "devSreIncidentIntake",
    Path("manifest"),
]:
    for path in sorted(root.rglob("*.xml")):
        if root.name in ("permissionsets", "tabs", "classes", "manifest"):
            if not (
                path.name.startswith("DevSreIncident_")
                or path.name.startswith("DevSre_Incident_Intake")
                or path.name.startswith("DevSreIncidentController")
                or path.name == "sf-devops-sre-incident-intake.xml"
            ):
                continue
        read(path)
        count += 1

assert count >= 30, f"XMLs do MVP incompletos: {count}"

for object_name in OBJECTS:
    obj = read(ROOT / "objects" / object_name / (object_name + ".object-meta.xml"))
    assert value(obj, "enableHistory") == "true"
    assert value(obj, "sharingModel") == "Private"

lookup = read(ROOT / "objects/DevSre_RecoveryAction__c/fields/Incident__c.field-meta.xml")
assert value(lookup, "type") == "Lookup"
assert value(lookup, "referenceTo") == "DevSre_Incident__c"
assert value(lookup, "required") == "true"
assert value(lookup, "deleteConstraint") == "Restrict"

incident = ROOT / "objects/DevSre_Incident__c/fields"
for field, expected in {
    "Source__c": "Manual",
    "CauseType__c": "Unconfirmed",
    "CauseReviewStatus__c": "Pending",
}.items():
    data = read(incident / (field + ".field-meta.xml"))
    defaults = [
        value(child, "fullName")
        for child in data.findall(".//" + NS + "value")
        if value(child, "default") == "true"
    ]
    assert defaults == [expected], f"Default incorreto: {field}: {defaults}"

for name in ["DevSreIncident_Reader", "DevSreIncident_Operator"]:
    data = read(ROOT / "permissionsets" / (name + ".permissionset-meta.xml"))
    for permission in data.findall(NS + "objectPermissions"):
        assert value(permission, "allowDelete") == "false"
        assert value(permission, "modifyAllRecords") == "false"
        assert value(permission, "viewAllRecords") == "false"
        if name.endswith("_Reader"):
            assert value(permission, "allowCreate") == "false"
            assert value(permission, "allowEdit") == "false"
    for field_permission in data.findall(NS + "fieldPermissions"):
        field = value(field_permission, "field")
        if field and (".CauseType__c" in field or ".CauseReviewStatus__c" in field or ".CauseJustification__c" in field):
            expected = "false" if name.endswith("_Reader") else "true"
            assert value(field_permission, "editable") == expected, f"Acesso causal incorreto: {name} / {field}"

print(f"PASS: INCIDENT_XML_AND_SECURITY_GATES files={count}")
