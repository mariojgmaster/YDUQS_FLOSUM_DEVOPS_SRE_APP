#!/usr/bin/env python3
"""Use current Salesforce tab metadata, preserve all fields, and stage only
the approved component swap. Verify deployed Apex test is previous reviewed
revision or the current revision. Never print org source to public logs."""
import argparse, json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, BadZipFile
N="{http://soap.sforce.com/2006/04/metadata}"
OLD="""      Database.insert(
        new PermissionSetAssignment(
          AssigneeId = runningUser,
          PermissionSetId = operatorAccess.Id
        ),
        AccessLevel.SYSTEM_MODE
      );
"""
START="      // In a deployed sandbox, the running integration user may already"
END="    }\n\n    return new User"
ALLOWED={"DevSreIncidentControllerTest","incidentsRollbacks","devSreIncidentsHost"}

def check_preview(data):
    assert data["status"]==0
    result=data["result"]
    values={}
    for key in ("toDeploy","conflicts","toDelete","ignored"):
        group=result[key]
        assert isinstance(group,list)
        names=[]
        for item in group:
            assert isinstance(item,dict)
            name=next((item[k] for k in ("name","fullName","member","componentName")
                       if isinstance(item.get(k),str) and item[k] in ALLOWED),None)
            assert name is not None and name not in names
            names.append(name)
        values[key]=set(names)
    assert not values["toDelete"] and not values["ignored"]
    assert values["toDeploy"].issubset({"devSreIncidentsHost"})
    assert values["conflicts"].issubset({"incidentsRollbacks","DevSreIncidentControllerTest"})
    assert values["toDeploy"]|values["conflicts"]==ALLOWED

def zip_member(zipname,filename):
    with ZipFile(zipname) as z:
        candidates=[x for x in z.infolist() if x.filename.split("/")[-1]==filename and x.file_size<300000]
        assert len(candidates)==1
        return z.read(candidates[0])

def norm(s):
    return s.replace("\r\n","\n").strip()

def stage(tabs,klass,candidate,preview):
    check_preview(json.loads(Path(preview).read_text(encoding="utf-8")))
    print("INFO: INCIDENT_MDAPI_STAGE_PREVIEW_OK",flush=True)
    source=Path("force-app/main/default/classes/DevSreIncidentControllerTest.cls").read_text(encoding="utf-8-sig")
    a=source.index(START); b=source.index(END,a)
    previous=source[:a]+OLD+source[b:]
    deployed=zip_member(klass,"DevSreIncidentControllerTest.cls").decode("utf-8-sig")
    print("INFO: INCIDENT_MDAPI_STAGE_CLASS_RETRIEVED",flush=True)
    assert norm(deployed) in (norm(previous),norm(source)), "unexpected Apex test drift"
    print("INFO: INCIDENT_MDAPI_STAGE_CLASS_BASELINE_OK",flush=True)
    root=ET.fromstring(zip_member(tabs,"incidentsRollbacks.tab"))
    print("INFO: INCIDENT_MDAPI_STAGE_TAB_RETRIEVED",flush=True)
    assert root.tag==N+"CustomTab"
    refs=root.findall(N+"lwcComponent")
    assert len(refs)==1 and refs[0].text in ("incidentsRollbacks","devSreIncidentsHost")
    assert not root.findall(N+"auraComponent") and not root.findall(N+"flexiPage")
    refs[0].text="devSreIncidentsHost"
    candidate=Path(candidate)
    tab=candidate/"tabs/incidentsRollbacks.tab"
    assert tab.is_file() and not tab.is_symlink()
    tab.write_bytes(ET.tostring(root,encoding="utf-8",xml_declaration=True))
    print("INFO: INCIDENT_MDAPI_STAGE_TAB_PRESERVED",flush=True)
    test=candidate/"classes/DevSreIncidentControllerTest.cls"
    assert test.is_file() and norm(test.read_text(encoding="utf-8-sig"))==norm(source)
    print("INFO: INCIDENT_MDAPI_STAGE_CANDIDATE_CLASS_OK",flush=True)
    md=ET.parse(candidate/"package.xml").getroot()
    groups={}
    for elem in md.findall(N+"types"):
        key=elem.findtext(N+"name")
        assert key not in groups
        groups[key]=[x.text for x in elem.findall(N+"members")]
    assert groups=={"ApexClass":["DevSreIncidentControllerTest"],"LightningComponentBundle":["devSreIncidentsHost"],"CustomTab":["incidentsRollbacks"]}
    print("INFO: INCIDENT_MDAPI_STAGE_PACKAGE_XML_OK",flush=True)
    paths={i.relative_to(candidate).as_posix() for i in candidate.rglob("*") if i.is_file()}
    required={"package.xml","tabs/incidentsRollbacks.tab","classes/DevSreIncidentControllerTest.cls","classes/DevSreIncidentControllerTest.cls-meta.xml","lwc/devSreIncidentsHost/devSreIncidentsHost.js-meta.xml"}
    assert required.issubset(paths)
    assert all(x in required or x.startswith("lwc/devSreIncidentsHost/") for x in paths)
    assert all(not x.is_symlink() for x in candidate.rglob("*"))
    print("PASS: INCIDENT_APPROVED_MDAPI_DELTA_AND_ORIGINAL_TAB_PRESERVED")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("tabs","klass","candidate","preview"):
        p.add_argument("--"+name,required=True)
    a=p.parse_args()
    try: stage(a.tabs,a.klass,a.candidate,a.preview)
    except (AssertionError,ValueError,KeyError,OSError,ET.ParseError,BadZipFile,UnicodeError):
        print("::error title=INCIDENT_MDAPI_STAGE_DENIED::Unapproved preview, org changes, or unexpected package.")
        raise SystemExit(1)
