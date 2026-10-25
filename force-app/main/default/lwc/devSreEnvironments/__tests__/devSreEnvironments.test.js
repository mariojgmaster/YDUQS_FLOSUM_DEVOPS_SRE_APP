import { createElement } from "lwc";
import Component from "c/devSreEnvironments";
import loadOverview from "@salesforce/apex/DevSreEnvironmentInsightsController.loadOverview";
jest.mock("@salesforce/apex/DevSreEnvironmentInsightsController.loadOverview",
  () => ({ default: jest.fn() }), { virtual: true });

const flush = async () => { for (let i = 0; i < 8; i++) await Promise.resolve(); };
const DATA = {
  complete: true, organizationCount: 1, logCount: 2, deploymentCount: 1,
  validationCount: 1, successCount: 1, failureCount: 1,
  organizations: [{ id: "a01org", name: "Homologação", deployments: 1,
    validations: 1, otherOperations: 0, successes: 1, failures: 1,
    lastActivity: "2026-10-25T10:00:00Z",
    recent: [{id:"a02log", name:"ML-TEST", processType:"Deployment", result:"Sucesso"}]}]
};
function mount() { const e=createElement("c-dev-sre-environments",{is:Component}); document.body.appendChild(e);return e; }
describe("Ambientes — consulta operacional somente leitura", () => {
  beforeEach(() => { jest.clearAllMocks(); loadOverview.mockResolvedValue(DATA); });
  afterEach(() => { document.body.innerHTML=""; });
  it("renderiza apenas atividade Flosum, sem vigência nem formulário de classificação", async () => {
    const el=mount(); await flush();
    expect(el.shadowRoot.textContent).toContain("Organizações Flosum");
    expect(el.shadowRoot.textContent).toContain("Homologação");
    expect(el.shadowRoot.textContent).not.toContain("Classificar organização");
    expect(el.shadowRoot.querySelector("lightning-input[type='datetime']")).toBeNull();
    expect(el.shadowRoot.querySelector(".org-table")).not.toBeNull();
    expect(loadOverview).toHaveBeenCalledWith({ days:30, organizationId:null });
  });
  it("aplica período e lookup Organisation automaticamente", async () => {
    const el=mount(); await flush();
    const period=el.shadowRoot.querySelector("lightning-combobox");
    period.dispatchEvent(new CustomEvent("change",{detail:{value:"7"}}));
    await flush();
    expect(loadOverview).toHaveBeenLastCalledWith({days:7,organizationId:null});
    const picker=el.shadowRoot.querySelector("lightning-record-picker");
    expect(picker.objectApiName).toBe("Flosum__Organisation__c");
    picker.dispatchEvent(new CustomEvent("change",{detail:{recordId:"a01org"}}));
    await flush();
    expect(loadOverview).toHaveBeenLastCalledWith({days:7,organizationId:"a01org"});
  });
  it("não publica totais de amostra incompleta", async () => {
    loadOverview.mockResolvedValue({complete:false,organizations:[],organizationCount:null});
    const el=mount();await flush();
    expect(el.shadowRoot.textContent).toContain("limite seguro");
    expect(el.shadowRoot.querySelector(".metrics")).toBeNull();
    expect(el.shadowRoot.querySelector(".org-table")).toBeNull();
  });
  it("mostra erros de acesso sem dados ilustrativos", async () => {
    loadOverview.mockRejectedValue({body:{message:"Sem acesso"}});
    const el=mount();await flush();
    expect(el.shadowRoot.querySelector('[role="alert"]').textContent).toContain("Sem acesso");
    expect(el.shadowRoot.querySelector(".org-table")).toBeNull();
  });
});
