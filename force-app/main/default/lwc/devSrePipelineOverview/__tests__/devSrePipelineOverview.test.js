import { createElement } from "lwc";
import Component from "c/devSrePipelineOverview";
import listMonitorDeployments from "@salesforce/apex/DevSreDeploymentController.listMonitorDeployments";
import getMonitorSummary from "@salesforce/apex/DevSreDeploymentController.getMonitorSummary";
import searchOrganizations from "@salesforce/apex/DevSreEnvironmentController.searchOrganizations";
jest.mock(
  "@salesforce/apex/DevSreDeploymentController.listMonitorDeployments",
  () => ({ default: jest.fn() }),
  { virtual: true }
);
jest.mock(
  "@salesforce/apex/DevSreDeploymentController.getMonitorSummary",
  () => ({ default: jest.fn() }),
  { virtual: true }
);
jest.mock(
  "@salesforce/apex/DevSreEnvironmentController.searchOrganizations",
  () => ({ default: jest.fn() }),
  { virtual: true }
);
const flush = async () => {
  for (let i = 0; i < 8; i++) await Promise.resolve();
};
const ROW = {
  id: "log1",
  name: "DEP-01",
  branchName: "Release CRM",
  organizationName: "Org CRM",
  environmentClass: "PROD",
  outcome: "Success",
  durationSeconds: 84,
  completedAt: "2026-10-24T12:00:00Z"
};
const SUMMARY = {
  complete: true,
  total: 54,
  succeeded: 53,
  failed: 1,
  pending: 0,
  partial: 0,
  notRun: 0,
  unknown: 0,
  successRate: 98.1
};
const PAGE = {
  rows: [ROW],
  hasMore: false,
  cursorCreated: "2026-10-24T12:00:00Z",
  cursorId: "log1"
};
function mount() {
  const el = createElement("c-dev-sre-pipeline-overview", { is: Component });
  document.body.appendChild(el);
  return el;
}
function button(el, label) {
  return [...el.shadowRoot.querySelectorAll("lightning-button")].find(
    (node) => node.label === label
  );
}
function valid(el) {
  el.shadowRoot.querySelectorAll("[data-filter]").forEach((node) => {
    node.reportValidity = jest.fn(() => true);
  });
}
function change(el, name, value) {
  [...el.shadowRoot.querySelectorAll("[data-filter]")]
    .find((node) => node.name === name)
    .dispatchEvent(new CustomEvent("change", { detail: { value } }));
}
describe("Pipeline Monitor principal", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    listMonitorDeployments.mockResolvedValue(PAGE);
    getMonitorSummary.mockResolvedValue(SUMMARY);
    searchOrganizations.mockResolvedValue({ options: [], hasMore: false });
  });
  afterEach(() => {
    document.body.innerHTML = "";
    jest.restoreAllMocks();
    jest.useRealTimers();
  });
  it("monta o protótipo com dados reais e resumo completo independente da página", async () => {
    const el = mount();
    await flush();
    expect(el.shadowRoot.querySelector("h1").textContent).toBe(
      "Pipeline Monitor"
    );
    expect(el.shadowRoot.textContent).toContain("Release CRM");
    expect(el.shadowRoot.textContent).toContain("Produção");
    expect(el.shadowRoot.textContent).not.toContain("54 registros acessíveis");
    expect(el.shadowRoot.textContent).toContain("98,1%");
    expect(el.shadowRoot.textContent).toContain("Fila");
    expect(button(el, "Novo deployment")).toBeUndefined();
    expect(el.shadowRoot.querySelector('lightning-button-icon[title="Atualizar monitor"]')).not.toBeNull();
    expect(el.shadowRoot.querySelector('lightning-input[type="toggle"]')).toBeNull();
  });
  it("aplica busca/ambiente no servidor e não envia filtro de resultado ao resumo", async () => {
    const el = mount();
    await flush();
    valid(el);
    button(el, "Filtros").click();
    await flush();
    change(el, "search", "CRM");
    jest.advanceTimersByTime(350);
    change(el, "environmentClass", "UAT");
    change(el, "outcome", "Failed");
    await flush();
    expect(button(el, "Aplicar filtros")).toBeUndefined();
    await flush();
    expect(listMonitorDeployments.mock.calls.at(-1)[0]).toMatchObject({
      searchTerm: "CRM",
      environmentClass: "UAT",
      outcome: "Failed",
      cursorId: null
    });
    expect(getMonitorSummary.mock.calls.at(-1)[0]).not.toHaveProperty("outcome");
    expect(getMonitorSummary.mock.calls.at(-1)[0]).toMatchObject({
      searchTerm: "CRM",
      environmentClass: "UAT"
    });
  });
  it("mantém a lista se o resumo falhar e não mostra zero como sucesso", async () => {
    getMonitorSummary.mockRejectedValue(new Error("summary"));
    const el = mount();
    await flush();
    expect(el.shadowRoot.querySelector('[role="alert"]').textContent).toContain(
      "resumo"
    );
    expect(el.shadowRoot.textContent).toContain("Release CRM");
    expect(el.shadowRoot.textContent).not.toContain("98,1%");
  });
  it("explica resumo indisponível quando a fonte ultrapassa o limite", async () => {
    getMonitorSummary.mockResolvedValue({ complete: false });
    const el = mount();
    await flush();
    expect(el.shadowRoot.textContent).toContain("mais de 2.000");
    expect(el.shadowRoot.textContent).not.toContain("undefined");
    expect(el.shadowRoot.textContent).toContain("Release CRM");
  });
  it("descarta resposta anterior quando o usuário altera o filtro", async () => {
    let resolve;
    listMonitorDeployments.mockReturnValueOnce(
      new Promise((done) => {
        resolve = done;
      })
    );
    const el = mount();
    await flush();
    change(el, "search", "Outro");
    resolve(PAGE);
    await flush();
    expect(el.shadowRoot.textContent).not.toContain("Release CRM");
    expect(el.shadowRoot.textContent).not.toContain("Release CRM");
  });
  it("não pula registros entre expansão da página e cursor seguinte", async () => {
    listMonitorDeployments.mockResolvedValue({
      ...PAGE,
      rows: Array.from({ length: 12 }, (_, i) => ({ ...ROW, id: `log${i}` })),
      hasMore: true
    });
    const el = mount();
    await flush();
    expect(el.shadowRoot.querySelectorAll(".delivery-row")).toHaveLength(10);
    expect(button(el, "Próxima página").disabled).toBe(true);
    button(el, "Mostrar mais desta página").click();
    await flush();
    expect(el.shadowRoot.querySelectorAll(".delivery-row")).toHaveLength(12);
    button(el, "Próxima página").click();
    await flush();
    expect(listMonitorDeployments.mock.calls[1][0].cursorId).toBe("log1");
    expect(getMonitorSummary).toHaveBeenCalledTimes(1);
  });
  it("permite avançar quando a página filtrada está vazia", async () => {
    listMonitorDeployments.mockResolvedValue({
      ...PAGE,
      rows: [],
      hasMore: true
    });
    const el = mount();
    await flush();
    expect(el.shadowRoot.textContent).toContain("mais registros de origem");
    expect(button(el, "Próxima página").disabled).toBe(false);
  });
  it("oferece 7/30/90 dias e intervalo personalizado, sem polling", async () => {
    const el = mount();
    await flush();
    valid(el);
    const period = [...el.shadowRoot.querySelectorAll("lightning-combobox")]
      .find((x) => x.name === "period");
    expect(period.options.map((x) => x.value)).toEqual(["7","30","90","custom"]);
    period.dispatchEvent(new CustomEvent("change", { detail: { value: "7" } }));
    await flush();
    expect(listMonitorDeployments).toHaveBeenCalledTimes(2);
    period.dispatchEvent(new CustomEvent("change", { detail: { value: "custom" } }));
    await flush();
    expect([...el.shadowRoot.querySelectorAll("lightning-input")]
      .filter((x) => x.name === "fromDate" || x.name === "toDate")).toHaveLength(2);
    expect(el.shadowRoot.querySelector('lightning-input[type="toggle"]')).toBeNull();
  });
  it("navega por Branch e Metadata Log separadamente, sem seta", async () => {
    listMonitorDeployments.mockResolvedValue({
      ...PAGE, rows: [{ ...ROW, branchId: "a0B0001" }]
    });
    const el = mount();
    await flush();
    expect(el.shadowRoot.querySelector(".delivery-row lightning-button-icon")).toBeNull();
    expect(el.shadowRoot.querySelector(".branch-link")).not.toBeNull();
    expect(el.shadowRoot.querySelector(".log-link")).not.toBeNull();
    expect(el.shadowRoot.textContent).toContain("Org Flosum:");
    expect(el.shadowRoot.textContent).toContain("Ambiente:");
  });
  it("seleciona organização Flosum por record-picker", async () => {
    const el = mount();
    await flush();
    button(el,"Filtros").click();
    await flush();
    const picker = el.shadowRoot.querySelector('lightning-record-picker[data-org="organizationId"]');
    expect(picker.objectApiName).toBe("Flosum__Organisation__c");
    picker.dispatchEvent(new CustomEvent("change", { detail: { recordId: "a01ORG" } }));
    await flush();
    await flush();
    expect(listMonitorDeployments).toHaveBeenLastCalledWith(
      expect.objectContaining({ organizationId: "a01ORG" })
    );
  });
  it("exporta apenas a página consultada e neutraliza fórmulas CSV", async () => {
    listMonitorDeployments.mockResolvedValue({
      ...PAGE,
      rows: [{ ...ROW, branchName: "=HYPERLINK(1)" }]
    });
    URL.createObjectURL = jest.fn(() => "blob:preview");
    URL.revokeObjectURL = jest.fn();
    const el = mount();
    await flush();
    el.shadowRoot.querySelector("[data-download]").click = jest.fn();
    button(el, "Exportar página").click();
    const blob = URL.createObjectURL.mock.calls[0][0];
    const text = await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.readAsText(blob);
    });
    expect(text).toContain("'=HYPERLINK(1)");
    expect(text).toContain("DEP-01");
    expect(el.shadowRoot.querySelector("[data-download]").download).toContain(
      "pagina-1.csv"
    );
  });
});
