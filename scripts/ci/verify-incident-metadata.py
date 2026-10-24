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
                or path.name.startswith("incidentsRollbacks.")
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


# Guard against the exact errors reported in DevSreFeat Deployment Details.
rules_checked = 0
for object_name in OBJECTS:
    directory = ROOT / "objects" / object_name / "validationRules"
    for rule_path in sorted(directory.glob("*.validationRule-meta.xml")):
        rule = read(rule_path)
        expected_name = rule_path.name.removesuffix(".validationRule-meta.xml")
        assert value(rule, "fullName") == expected_name, f"ValidationRule.fullName invalid: {rule_path}"
        assert value(rule, "active") == "true", f"ValidationRule inactive: {rule_path}"
        rules_checked += 1
assert rules_checked == 10, f"Unexpected number of incident validation rules: {rules_checked}"

# Salesforce forbids assigning field-level permission on a universally required custom field.
universally_required = set()
for object_name in OBJECTS:
    for field_path in (ROOT / "objects" / object_name / "fields").glob("*.field-meta.xml"):
        field = read(field_path)
        if value(field, "required") == "true":
            universally_required.add(f"{object_name}.{value(field, 'fullName')}")
assert {
    "DevSre_Incident__c.Title__c", "DevSre_Incident__c.ServiceKey__c",
    "DevSre_RecoveryAction__c.Incident__c"
}.issubset(universally_required)
for permission_name in ("DevSreIncident_Reader", "DevSreIncident_Operator"):
    perm = read(ROOT / "permissionsets" / (permission_name + ".permissionset-meta.xml"))
    configured = {value(x, "field") for x in perm.findall(NS + "fieldPermissions")}
    assert not configured.intersection(universally_required), (
        f"Required field appears in PermissionSet fieldPermissions: {permission_name}"
    )

# Apex keyword 'number' is reserved. LWC uses the new DTO field in both grids.
apex = (ROOT / "classes/DevSreIncidentController.cls").read_text("utf-8")
assert "public String number {" not in apex and "row.number" not in apex
assert apex.count("public String recordNumber { get; set; }") == 2
assert apex.count("row.recordNumber =") == 2
lwc = (ROOT / "lwc/devSreIncidentIntake/devSreIncidentIntake.js").read_text("utf-8")
assert lwc.count('fieldName: "recordNumber"') == 2
assert "row.number" not in lwc and "row.recordNumber" in lwc
print(f"PASS: INCIDENT_SF_DEPLOY_BLOCKERS_FIXED rules={rules_checked} required={len(universally_required)}")


# API 67 uses user mode by default. The test fixture must be explicit and
# must NOT relax the production controller's WITH USER_MODE or CRUD/FLS checks.
test_apex = (ROOT / "classes/DevSreIncidentControllerTest.cls").read_text("utf-8")
assert test_apex.count("Database.insert(incidents, AccessLevel.SYSTEM_MODE)") == 1
assert "Database.insert(new List<DevSre_RecoveryAction__c>{" in test_apex
assert test_apex.count("AccessLevel.SYSTEM_MODE") >= 4
assert "WHERE Name = 'DevSreIncident_Operator'" in test_apex
assert "new PermissionSetAssignment(" in test_apex
assert "List<PermissionSetAssignment> assigned" in test_apex
assert "if (assigned.isEmpty())" in test_apex
assert "private static User operatorContext()" in test_apex
assert "System.runAs(new User(Id = runningUser))" in test_apex
assert test_apex.count("User actor = operatorContext();") == 3
assert test_apex.count("System.runAs(actor)") == 3
assert test_apex.count("WITH SYSTEM_MODE") >= 5
controller = (ROOT / "classes/DevSreIncidentController.cls").read_text("utf-8")
assert controller.count("WITH USER_MODE") >= 3
assert "with sharing class DevSreIncidentController" in controller
print("PASS: INCIDENT_API67_TEST_FIXTURE_MODE_AND_CONTROLLER_SECURITY")

assert (ROOT / "tabs/incidentsRollbacks.tab-meta.xml").exists()
assert not (ROOT / "tabs/DevSre_Incident_Intake.tab-meta.xml").exists()
host = (ROOT / "lwc/devSreIncidentsHost/devSreIncidentsHost.html").read_text("utf-8")
assert "<c-incidents-rollbacks>" in host
assert "<c-dev-sre-incident-intake>" in host
assert host.count("<lightning-tab ") == 2
assert "lightning__Tab" in (ROOT / "lwc/devSreIncidentsHost/devSreIncidentsHost.js-meta.xml").read_text("utf-8")
print("PASS: INCIDENT_ORIGINAL_TAB_BRIDGE_AND_NO_DUPLICATE_TAB")
print(f"PASS: INCIDENT_XML_AND_SECURITY_GATES files={count}")
