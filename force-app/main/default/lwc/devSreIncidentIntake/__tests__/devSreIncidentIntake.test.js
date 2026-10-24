import { createElement } from "lwc";
import DevSreIncidentIntake from "c/devSreIncidentIntake";
import listIncidents from "@salesforce/apex/DevSreIncidentController.listIncidents";
jest.mock("@salesforce/customPermission/DevSre_ReviewIncidentCausality", () => ({ default: undefined }), { virtual: true });
import listRecoveryActions from "@salesforce/apex/DevSreIncidentController.listRecoveryActions";

jest.mock("@salesforce/apex/DevSreIncidentController.listIncidents", () => ({ default: jest.fn() }), { virtual: true });
jest.mock("@salesforce/apex/DevSreIncidentController.listRecoveryActions", () => ({ default: jest.fn() }), { virtual: true });

const flush = async () => { await Promise.resolve(); await Promise.resolve(); };
const INCIDENT_ID = "a01000000000001AAA";
function mount() {
  const component = createElement("c-dev-sre-incident-intake", { is: DevSreIncidentIntake });
  document.body.appendChild(component);
  return component;
}

describe("c-dev-sre-incident-intake", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    listIncidents.mockResolvedValue({
      incidents: [{ id: INCIDENT_ID, number: "INC-000001", title: "Interrupção de serviço", status: "Open", serviceKey: "A", severity: "SEV2" }],
      hasMore: false
    });
  });
  afterEach(() => { document.body.innerHTML = ""; });

  it("carrega incidentes reais exclusivamente da consulta Apex", async () => {
    const component = mount();
    await flush();
    expect(listIncidents).toHaveBeenCalledWith({ searchTerm: "" });
    const table = component.shadowRoot.querySelector('lightning-datatable[data-name="incidents"]');
    expect(table.data).toHaveLength(1);
    expect(table.data[0].number).toBe("INC-000001");
  });

  it("mostra estado vazio sem sintetizar incidentes", async () => {
    listIncidents.mockResolvedValue({ incidents: [], hasMore: false });
    const component = mount();
    await flush();
    expect(component.shadowRoot.textContent).toContain("Nenhum incidente encontrado");
  });

  it("permite visualizar ações somente quando seleciona incidente", async () => {
    listRecoveryActions.mockResolvedValue({ actions: [{ id: "a02000000000001AAA", number: "REC-000001", actionType: "Rollback", status: "Planned" }], hasMore: false });
    const component = mount();
    await flush();
    component.shadowRoot.querySelector('lightning-datatable[data-name="incidents"]').dispatchEvent(
      new CustomEvent("rowaction", { detail: { action: { name: "view_actions" }, row: { id: INCIDENT_ID, number: "INC-000001" } } })
    );
    await flush();
    expect(listRecoveryActions).toHaveBeenCalledWith({ incidentId: INCIDENT_ID });
    expect(component.shadowRoot.querySelector('lightning-datatable[data-name="actions"]').data).toHaveLength(1);
  });

  it("exibe aviso de cobertura e nunca representa incidente como falha de mudança", async () => {
    const component = mount();
    await flush();
    expect(component.shadowRoot.textContent).toContain("DORA: não mensurável");
    expect(component.shadowRoot.textContent).toContain("Incidente não equivale a falha de mudança.");
  });

  it("mostra erro de consulta e não exibe tabela falsa", async () => {
    listIncidents.mockRejectedValue({ body: { message: "Acesso negado" } });
    const component = mount();
    await flush();
    expect(component.shadowRoot.textContent).toContain("Acesso negado");
    expect(component.shadowRoot.querySelector('lightning-datatable[data-name="incidents"]')).toBeNull();
  });

  it("avisa quando a busca está truncada", async () => {
    listIncidents.mockResolvedValue({ incidents: [{ id: INCIDENT_ID, title: "Incidente" }], hasMore: true });
    const component = mount();
    await flush();
    expect(component.shadowRoot.textContent).toContain("mais de 50 incidentes");
  });

  it("nao exibe a revisao de causa para operador sem Custom Permission", async () => {
    const component = mount();
    await flush();
    expect(component.shadowRoot.querySelector('lightning-button[label="Revisar causa (RM)"]')).toBeNull();
  });

  it("atualiza a consulta sem inventar estado", async () => {
    const component = mount();
    await flush();
    component.shadowRoot.querySelector("header lightning-button").click();
    await flush();
    expect(listIncidents).toHaveBeenCalledTimes(2);
  });
});
