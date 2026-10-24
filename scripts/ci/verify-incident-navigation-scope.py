"""Explicit three-member migration manifest guardrail."""
from pathlib import Path
from xml.etree import ElementTree as ET
N = "{http://soap.sforce.com/2006/04/metadata}"
root = ET.parse("manifest/sf-devops-sre-incidents-navigation.xml").getroot()
expected = {
    "ApexClass": ["DevSreIncidentControllerTest"],
    "LightningComponentBundle": ["devSreIncidentsHost"],
    "CustomTab": ["incidentsRollbacks"],
}
actual = {}
for typ in root.findall(N+"types"):
    kind = typ.findtext(N+"name")
    assert kind not in actual
    actual[kind] = [x.text for x in typ.findall(N+"members")]
assert actual == expected and root.findtext(N+"version")=="67.0"
tab = ET.parse("force-app/main/default/tabs/incidentsRollbacks.tab-meta.xml").getroot()
assert tab.findtext(N+"lwcComponent")=="devSreIncidentsHost"
host = Path("force-app/main/default/lwc/devSreIncidentsHost/devSreIncidentsHost.html").read_text("utf-8")
assert "<c-incidents-rollbacks>" in host and "<c-dev-sre-incident-intake>" in host
assert not Path("force-app/main/default/tabs/DevSre_Incident_Intake.tab-meta.xml").exists()
print("PASS: INCIDENT_NAVIGATION_DELTA_CLOSED_SCOPE")
