import { createElement } from "lwc";
import DevSreIncidentIntake from "c/devSreIncidentIntake";
import listIncidents from "@salesforce/apex/DevSreIncidentController.listIncidents";
import listRecoveryActions from "@salesforce/apex/DevSreIncidentController.listRecoveryActions";

jest.mock("@salesforce/apex/DevSreIncidentController.listIncidents", () => ({ default: jest.fn() }), { virtual: true });
jest.mock("@salesforce/apex/DevSreIncidentController.listRecoveryActions", () => ({ default: jest.fn() }), { virtual: true });
jest.mock("@salesforce/customPermission/DevSre_ReviewIncidentCausality", () => ({ default: true }), { virtual: true });

const flush = async () => { await Promise.resolve(); await Promise.resolve(); };
const INCIDENT_ID = "a01000000000001AAA";

describe("revisao pela equipe DevOps/SRE", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    listIncidents.mockResolvedValue({ incidents: [{ id: INCIDENT_ID, number: "INC-000001", title: "Análise RM", status: "Open" }], hasMore: false });
    listRecoveryActions.mockResolvedValue({ actions: [], hasMore: false });
  });
  afterEach(() => { document.body.innerHTML = ""; });

  it("exibe controle de revisao apenas apos selecao do incidente para RM", async () => {
    const component = createElement("c-dev-sre-incident-intake", { is: DevSreIncidentIntake });
    document.body.appendChild(component);
    await flush();
    expect(component.shadowRoot.querySelector('lightning-button[label="Revisar causa"]')).toBeNull();
    component.shadowRoot.querySelector('lightning-datatable[data-name="incidents"]').dispatchEvent(
      new CustomEvent("rowaction", { detail: { action: { name: "view_actions" }, row: { id: INCIDENT_ID, number: "INC-000001" } } })
    );
    await flush();
    const buttons = [...component.shadowRoot.querySelectorAll("lightning-button")];
    const btn = buttons.find(x => x.label === "Revisar causa");
    expect(btn).toBeDefined();
    btn.click();
    await flush();
    const form = component.shadowRoot.querySelector('lightning-record-edit-form[data-name="rm-review"]');
    expect(form).not.toBeNull();
    expect(form.recordId).toBe(INCIDENT_ID);
    expect(component.shadowRoot.textContent).toContain("confirmação de causa por deployment está bloqueada");
  });

  it("nao salva nem certifica metricas por existir apenas uma tela", async () => {
    const component = createElement("c-dev-sre-incident-intake", { is: DevSreIncidentIntake });
    document.body.appendChild(component);
    await flush();
    expect(component.shadowRoot.textContent).toContain("DORA: não mensurável");
    expect(component.shadowRoot.textContent).not.toContain("Certificado");
  });
});
