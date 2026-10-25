import { createElement } from "lwc";
import Component from "c/devSreDeployments";
import listDeployments from "@salesforce/apex/DevSreDeploymentController.listDeployments";
import listDeploymentsWithSearch from "@salesforce/apex/DevSreDeploymentController.listDeploymentsWithSearch";
import searchOrganizations from "@salesforce/apex/DevSreEnvironmentController.searchOrganizations";
jest.mock(
  "@salesforce/apex/DevSreDeploymentController.listDeployments",
  () => ({ default: jest.fn() }),
  { virtual: true }
);
jest.mock(
  "@salesforce/apex/DevSreDeploymentController.listDeploymentsWithSearch",
  () => ({ default: jest.fn() }),
  { virtual: true }
);
jest.mock(
  "@salesforce/apex/DevSreEnvironmentController.searchOrganizations",
  () => ({ default: jest.fn() }),
  { virtual: true }
);
const flush = async () => {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
};
const PAGE = {
  rows: [
    {
      id: "log1",
      name: "Log real",
      outcome: "Success",
      environmentClass: "PROD",
      quality: "Completo"
    }
  ],
  hasMore: false,
  inspectedRows: 1,
  cursorCreated: "2026-01-01T00:00:00Z",
  cursorId: "log1"
};
function mount() {
  const el = createElement("c-dev-sre-deployments", { is: Component });
  document.body.appendChild(el);
  return el;
}
function valid(el) {
  el.shadowRoot
    .querySelectorAll("lightning-input, lightning-combobox")
    .forEach((input) => {
      input.reportValidity = jest.fn(() => true);
    });
}
function button(el, label) {
  return [...el.shadowRoot.querySelectorAll("lightning-button")].find(
    (x) => x.label === label
  );
}
describe("deployments reais", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    listDeployments.mockResolvedValue(PAGE);
    listDeploymentsWithSearch.mockResolvedValue(PAGE);
    searchOrganizations.mockResolvedValue({ options: [], hasMore: false });
  });
  afterEach(() => {
    document.body.innerHTML = "";
  });
  it("busca nome de log/Branch no servidor, sem filtrar só a página atual", async () => {
    const el = mount();
    await flush();
    valid(el);
    const search = [...el.shadowRoot.querySelectorAll("lightning-input")].find(
      (input) => input.name === "searchTerm"
    );
    search.dispatchEvent(new CustomEvent("change", { detail: { value: "release" } }));
    await flush();
    expect(el.shadowRoot.textContent).toContain("Filtros alterados");
    button(el, "Aplicar filtros").click();
    await flush();
    expect(listDeploymentsWithSearch).toHaveBeenCalledWith(
      expect.objectContaining({ searchTerm: "release", branchId: null })
    );
    expect(el.shadowRoot.querySelector("lightning-datatable").data).toHaveLength(1);
  });
  it("ordena somente a página carregada sem alterar o cursor da consulta", async () => {
    listDeployments.mockResolvedValue({
      ...PAGE, rows: [
        { ...PAGE.rows[0], id: "a", name: "Alpha" },
        { ...PAGE.rows[0], id: "b", name: "Beta" }
      ]
    });
    const el = mount();
    await flush();
    const table = el.shadowRoot.querySelector("lightning-datatable");
    table.dispatchEvent(new CustomEvent("sort", {
      detail: { fieldName: "name", sortDirection: "desc" }
    }));
    await flush();
    expect(table.data.map((row) => row.name)).toEqual(["Beta", "Alpha"]);
    expect(listDeployments).toHaveBeenCalledTimes(1);
  });
  it("seleciona detalhe sem navegar e exporta só a página visível", async () => {
    const el = mount();
    await flush();
    expect(el.shadowRoot.textContent).toContain("Detalhes da entrega");
    expect(el.shadowRoot.textContent).toContain("Completo");
    const dt = el.shadowRoot.querySelector("lightning-datatable");
    dt.dispatchEvent(new CustomEvent("rowaction", {
      detail: { action: { name: "details" }, row: PAGE.rows[0] }
    }));
    await flush();
    expect(el.shadowRoot.textContent).toContain("Log real");
  });
  it("limpa busca e filtros sem inventar dados", async () => {
    const el = mount();
    await flush();
    valid(el);
    const search = [...el.shadowRoot.querySelectorAll("lightning-input")].find(
      (input) => input.name === "searchTerm"
    );
    search.dispatchEvent(new CustomEvent("change", { detail: { value: "x" } }));
    await flush();
    valid(el);
    button(el, "Limpar").click();
    await flush();
    expect(listDeployments).toHaveBeenCalledTimes(2);
  });
  it("apresenta dados reais e distingue resultados sem certificar KPI", async () => {
    const el = mount();
    await flush();
    const table = el.shadowRoot.querySelector("lightning-datatable");
    expect(table.data[0].outcomeLabel).toBe("Sucesso");
    expect(table.data[0].name).toBe("Log real");
    expect(el.shadowRoot.textContent).toContain("não certificadas");
    expect(el.shadowRoot.textContent).toContain("Não é um total global");
  });
  it("transmite cursor e reinicia ao trocar filtros", async () => {
    listDeployments.mockResolvedValue({ ...PAGE, hasMore: true });
    const el = mount();
    await flush();
    valid(el);
    button(el, "Próxima página").click();
    await flush();
    expect(listDeployments.mock.calls[1][0].cursorId).toBe("log1");
    const env = [...el.shadowRoot.querySelectorAll("lightning-combobox")].find(
      (x) => x.name === "environmentClass"
    );
    env.dispatchEvent(new CustomEvent("change", { detail: { value: "UAT" } }));
    await flush();
    expect(button(el, "Próxima página")).toBeUndefined();
    expect(el.shadowRoot.textContent).toContain("Filtros alterados");
    valid(el);
    button(el, "Aplicar filtros").click();
    await flush();
    expect(listDeployments.mock.calls[2][0]).toMatchObject({
      environmentClass: "UAT",
      cursorId: null,
      cursorCreated: null
    });
  });
  it("permite continuar mesmo quando a página filtrada está vazia", async () => {
    listDeployments.mockResolvedValue({
      ...PAGE,
      rows: [],
      hasMore: true,
      inspectedRows: 200
    });
    const el = mount();
    await flush();
    expect(el.shadowRoot.textContent).toContain("nesta página");
    expect(button(el, "Próxima página").disabled).toBe(false);
  });
  it("mostra erro sem conteúdo fictício e permite tentar novamente", async () => {
    listDeployments.mockRejectedValueOnce({
      body: { message: "Sem permissão para consultar." }
    });
    const el = mount();
    await flush();
    expect(el.shadowRoot.querySelector('[role="alert"]').textContent).toContain(
      "Sem permissão"
    );
    expect(el.shadowRoot.querySelector("lightning-datatable")).toBeNull();
    valid(el);
    button(el, "Aplicar filtros").click();
    await flush();
    expect(
      el.shadowRoot.querySelector("lightning-datatable").data
    ).toHaveLength(1);
  });
  it("descarta resposta antiga após edição dos filtros", async () => {
    let resolve;
    listDeployments.mockReturnValueOnce(
      new Promise((done) => {
        resolve = done;
      })
    );
    const el = mount();
    await flush();
    [...el.shadowRoot.querySelectorAll("lightning-combobox")]
      .find((x) => x.name === "environmentClass")
      .dispatchEvent(new CustomEvent("change", { detail: { value: "DEV" } }));
    resolve(PAGE);
    await flush();
    expect(el.shadowRoot.querySelector("lightning-datatable")).toBeNull();
  });
  it("traduz ausência de classificação e orienta a ação na aba Ambientes", async () => {
    listDeployments.mockResolvedValue({
      ...PAGE,
      rows: [{ ...PAGE.rows[0], environmentClass: "UNKNOWN" }]
    });
    const el = mount();
    await flush();
    expect(
      el.shadowRoot.querySelector("lightning-datatable").data[0]
        .environmentLabel
    ).toBe("Não identificado");
    expect(el.shadowRoot.textContent).toContain("Consulte a aba Ambientes");
  });
  it("buscar opções de organização não descarta uma página já consultada", async () => {
    const el = mount();
    await flush();
    const search = [...el.shadowRoot.querySelectorAll("lightning-input")].find(
      (input) => input.name === "organizationSearch"
    );
    search.dispatchEvent(
      new CustomEvent("change", { detail: { value: "UAT" } })
    );
    await flush();
    expect(
      el.shadowRoot.querySelector("lightning-datatable").data
    ).toHaveLength(1);
    expect(el.shadowRoot.textContent).not.toContain("Filtros alterados");
    expect(listDeployments).toHaveBeenCalledTimes(1);
  });
  it("falha na busca de organizações preserva os deployments e oferece nova busca", async () => {
    searchOrganizations.mockRejectedValueOnce(new Error("lookup"));
    const el = mount();
    await flush();
    expect(
      el.shadowRoot.querySelector("lightning-datatable").data
    ).toHaveLength(1);
    expect(el.shadowRoot.querySelector('[role="alert"]').textContent).toContain(
      "organizações"
    );
    button(el, "Buscar organizações").click();
    await flush();
    expect(el.shadowRoot.querySelector('[role="alert"]')).toBeNull();
  });
});
