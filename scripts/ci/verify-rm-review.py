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
rm = read(root/"permissionsets/DevSreIncident_RMReviewer.permissionset-meta.xml")
grant=rm.find(N+"customPermissions")
assert v(grant, "name")=="DevSre_ReviewIncidentCausality"
assert v(grant,"enabled")=="true"
perm={v(x,"field"):x for x in rm.findall(N+"fieldPermissions")}
for k in ("CauseType__c","CauseReviewStatus__c","CauseJustification__c"):
    key="DevSre_Incident__c."+k
    assert key in perm and v(perm[key],"editable")=="true",key
for x in rm.findall(N+"objectPermissions"):
    for tag in ("allowDelete","allowCreate","viewAllRecords","modifyAllRecords"):
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
for name in ("DevSreIncident_Operator","DevSreIncident_Reader"):
    data=read(root/("permissionsets/"+name+".permissionset-meta.xml"))
    for fp in data.findall(N+"fieldPermissions"):
        if v(fp,"field") in perm:
            assert v(fp,"editable")=="false",name
print("PASS: RM_REVIEW_GUARDS_DEFINED")
