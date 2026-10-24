"""Verifica invariantes estáticos de segurança do review dos RMs.
Nao substitui validate da org e testes de sharing/FLS reais.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
N = "{http://soap.sforce.com/2006/04/metadata}"
root = Path("force-app/main/default")
def read(path):
    return ET.parse(path).getroot()
def v(e,tag):
    el=e.find(N+tag)
    return el.text if el is not None else None
rm = read(root/"permissionsets/DevSreIncident_Operator.permissionset-meta.xml")
grant=rm.find(N+"customPermissions")
assert v(grant, "name")=="DevSre_ReviewIncidentCausality"
assert v(grant,"enabled")=="true"
perm={v(x,"field"):x for x in rm.findall(N+"fieldPermissions")}
for k in ("CauseType__c","CauseReviewStatus__c","CauseJustification__c"):
    key="DevSre_Incident__c."+k
    assert key in perm and v(perm[key],"editable")=="true",key
for x in rm.findall(N+"objectPermissions"):
    for tag in ("allowDelete","viewAllRecords","modifyAllRecords"):
        assert v(x,tag)=="false",(tag,x)
for name,required in {
    "CauseFieldsRequireRM":"$Permission.DevSre_ReviewIncidentCausality",
    "InitialCauseIsPending":"ISNEW()",
    "VerifiedDeploymentRequired":'ISPICKVAL(CauseType__c, "DeploymentRelated")',
    "CauseReviewNeedsJustification":"CauseJustification__c",
    "CauseConfirmationNeedsClassification":'ISPICKVAL(CauseType__c, "Unconfirmed")',
}.items():
    obj=read(root/("objects/DevSre_Incident__c/validationRules/"+name+".validationRule-meta.xml"))
    assert v(obj,"active")=="true",name
    assert required in v(obj,"errorConditionFormula"),name
reader=read(root/"permissionsets/DevSreIncident_Reader.permissionset-meta.xml")
for fp in reader.findall(N+"fieldPermissions"):
    if v(fp,"field") in perm:
        assert v(fp,"editable")=="false","Reader nao pode alterar causa"
for item in rm.findall(N+"objectPermissions"):
    for tag in ("allowDelete", "viewAllRecords", "modifyAllRecords"):
        assert v(item,tag)=="false",tag
group=read(root/"groups/DevSre_Incident_RMs.group-meta.xml")
assert v(group,"doesIncludeBosses")=="false"
for name,prefix in (("DevSre_Incident__c","INC-"),("DevSre_RecoveryAction__c","REC-")):
    rules=read(root/("sharingRules/"+name+".sharingRules-meta.xml"))
    rows=rules.findall(N+"sharingCriteriaRules")
    assert len(rows)==1,name
    rule=rows[0]
    assert v(rule,"accessLevel")=="Edit",name
    assert v(rule.find(N+"sharedTo"),"group")=="DevSre_Incident_RMs",name
    item=rule.find(N+"criteriaItems")
    assert v(item,"field")=="Name" and v(item,"operation")=="startsWith" and v(item,"value")==prefix,name
print("PASS: DEVOPS_TEAM_REVIEW_AND_SHARING_GUARDS_DEFINED")
