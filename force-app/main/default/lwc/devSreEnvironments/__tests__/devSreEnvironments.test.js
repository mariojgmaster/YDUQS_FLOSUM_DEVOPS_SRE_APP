import { createElement } from "lwc";
import Component from "c/devSreEnvironments";
import searchOrganizations from "@salesforce/apex/DevSreEnvironmentController.searchOrganizations";
import listMappings from "@salesforce/apex/DevSreEnvironmentController.listMappings";
import saveMapping from "@salesforce/apex/DevSreEnvironmentController.saveMapping";
jest.mock(
  "@salesforce/apex/DevSreEnvironmentController.searchOrganizations",
  () => ({ default: jest.fn() }),
  { virtual: true }
);
jest.mock(
  "@salesforce/apex/DevSreEnvironmentController.listMappings",
  () => ({ default: jest.fn() }),
  { virtual: true }
);
jest.mock(
  "@salesforce/apex/DevSreEnvironmentController.saveMapping",
  () => ({ default: jest.fn() }),
  { virtual: true }
);
const flush = async () => {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
};
function mount() {
  const el = createElement("c-dev-sre-environments", { is: Component });
  document.body.appendChild(el);
  return el;
}
function button(el, label) {
  return [...el.shadowRoot.querySelectorAll("lightning-button")].find(
    (x) => x.label === label
  );
}
function change(el, name, value) {
  [
    ...el.shadowRoot.querySelectorAll(
      "lightning-input, lightning-combobox, lightning-textarea, lightning-record-picker"
    )
  ]
    .find((x) => x.name === name || x.dataset.org === name)
    .dispatchEvent(new CustomEvent("change", { detail: { value, recordId: value } }));
}
describe("vigências de ambientes", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    listMappings.mockResolvedValue([]);
    searchOrganizations.mockResolvedValue({
      options: [{ value: "org1", label: "Organização" }],
      canManage: false,
      hasMore: false
    });
    saveMapping.mockResolvedValue("map1");
  });
  afterEach(() => {
    document.body.innerHTML = "";
    jest.restoreAllMocks();
  });
  it("usa record picker no relacionamento de edição e filtro histórico", async () => {
    searchOrganizations.mockResolvedValue({ options: [], canManage: true });
    const el = mount();
    await flush();
    button(el,"Classificar organização").click();
    await flush();
    const recordPicker = el.shadowRoot.querySelector('lightning-record-picker[data-org="organizationId"]');
    expect(recordPicker.objectApiName).toBe("Flosum__Organisation__c");
    button(el,"Cancelar").click();
    button(el,"Histórico").click();
    await flush();
    const historyPicker = el.shadowRoot.querySelector('lightning-record-picker[data-org="organizationFilter"]');
    historyPicker.dispatchEvent(new CustomEvent("change", { detail: { recordId: "org1" } }));
    await flush();
    expect(listMappings).toHaveBeenLastCalledWith({ organizationId: "org1" });
  });
  it("histórico por organização mantém a classificação original", async () => {
    listMappings.mockResolvedValue([
      { id: "map1", organizationId: "org1", organizationName: "Org A",
        environmentClass: "UAT", validFrom: "2026-01-01T00:00:00Z",
        validTo: null, reason: "Histórico" }
    ]);
    const el = mount();
    await flush();
    const table = el.shadowRoot.querySelector("lightning-datatable");
    table.dispatchEvent(new CustomEvent("rowaction", {
      detail: { action: { name: "history" }, row: table.data[0] }
    }));
    await flush();
    expect(listMappings).toHaveBeenLastCalledWith({ organizationId: "org1" });
    expect([...el.shadowRoot.querySelectorAll("lightning-combobox")].find((x) => x.name === "view").label).toBe("Período do histórico");
  });
  it("pesquisa organização na lista sem descartar mapeamentos", async () => {
    listMappings.mockResolvedValue([
      { id: "1", organizationName: "Org A", environmentClass: "PROD",
        validFrom: "2026-01-01T00:00:00Z" },
      { id: "2", organizationName: "Org B", environmentClass: "UAT",
        validFrom: "2026-01-01T00:00:00Z" }
    ]);
    const el = mount();
    await flush();
    change(el, "organizationQuery", "Org B");
    await flush();
    expect(el.shadowRoot.querySelector("lightning-datatable").data.map((x) => x.id)).toEqual(["2"]);
    expect(listMappings).toHaveBeenCalledTimes(1);
  });
  it("leitor consulta mas não recebe formulário de escrita", async () => {
    const el = mount();
    await flush();
    expect(button(el, "Salvar classificação")).toBeUndefined();
    expect(el.shadowRoot.textContent).toContain("Somente leitura");
    expect(saveMapping).not.toHaveBeenCalled();
  });
  it("gerente salva período com justificativa e atualiza a lista", async () => {
    searchOrganizations.mockResolvedValue({
      options: [{ value: "org1", label: "Organização" }],
      canManage: true
    });
    const el = mount();
    await flush();
    button(el, "Classificar organização").click();
    await flush();
    change(el, "organizationId", "org1");
    change(el, "environmentClass", "PROD");
    change(el, "validFrom", "2026-01-01T00:00:00.000Z");
    change(el, "reason", "Classificação aprovada");
    el.shadowRoot.querySelectorAll("[data-form]").forEach((input) => {
      input.reportValidity = jest.fn(() => true);
    });
    button(el, "Salvar classificação").click();
    await flush();
    expect(saveMapping).toHaveBeenCalledWith({
      mappingId: null,
      organizationId: "org1",
      environmentClass: "PROD",
      validFrom: "2026-01-01T00:00:00.000Z",
      validTo: null,
      reason: "Classificação aprovada"
    });
    expect(el.shadowRoot.textContent).toContain("Classificação salva");
    expect(listMappings).toHaveBeenCalledTimes(2);
    expect(listMappings.mock.calls[1][0].organizationId).toBe("org1");
    expect(el.shadowRoot.querySelector("[data-form]")).toBeNull();
  });
  it("protege a identidade ao encerrar uma vigência", async () => {
    searchOrganizations.mockResolvedValue({ options: [], canManage: true });
    const row = {
      id: "map1",
      organizationId: "org1",
      environmentClass: "UAT",
      validFrom: "2026-01-01T00:00:00Z",
      validTo: null,
      reason: "Original"
    };
    listMappings.mockResolvedValue([row]);
    const el = mount();
    await flush();
    el.shadowRoot.querySelector("lightning-datatable").dispatchEvent(
      new CustomEvent("rowaction", {
        detail: { action: { name: "edit" }, row }
      })
    );
    await flush();
    expect(
      [
        ...el.shadowRoot.querySelectorAll("lightning-input, lightning-combobox, lightning-record-picker")
      ].find((x) => x.name === "organizationId").disabled
    ).toBe(true);
    expect(
      [
        ...el.shadowRoot.querySelectorAll("lightning-input, lightning-combobox, lightning-record-picker")
      ].find((x) => x.name === "environmentClass").disabled
    ).toBe(true);
    expect(
      [
        ...el.shadowRoot.querySelectorAll("lightning-input, lightning-combobox, lightning-record-picker")
      ].find((x) => x.name === "validFrom").disabled
    ).toBe(true);
  });
  it("não apresenta sucesso quando o servidor rejeita overlap", async () => {
    searchOrganizations.mockResolvedValue({ options: [], canManage: true });
    saveMapping.mockRejectedValue({
      body: { message: "Vigências sobrepostas." }
    });
    const el = mount();
    await flush();
    button(el, "Classificar organização").click();
    await flush();
    el.shadowRoot.querySelectorAll("[data-form]").forEach((input) => {
      input.reportValidity = jest.fn(() => true);
    });
    button(el, "Salvar classificação").click();
    await flush();
    expect(el.shadowRoot.querySelector('[role="alert"]').textContent).toContain(
      "sobrepostas"
    );
    expect(el.shadowRoot.textContent).not.toContain("Classificação salva");
  });
  it("abre apenas classificações atuais e respeita início inclusivo e fim exclusivo", async () => {
    jest.spyOn(Date, "now").mockReturnValue(Date.parse("2026-07-01T00:00:00Z"));
    listMappings.mockResolvedValue([
      {
        id: "past",
        environmentClass: "UAT",
        validFrom: "2026-01-01T00:00:00Z",
        validTo: "2026-07-01T00:00:00Z"
      },
      {
        id: "now",
        environmentClass: "PROD",
        validFrom: "2026-07-01T00:00:00Z",
        validTo: null
      },
      {
        id: "next",
        environmentClass: "DEV",
        validFrom: "2027-01-01T00:00:00Z",
        validTo: null
      }
    ]);
    const el = mount();
    await flush();
    const table = () => el.shadowRoot.querySelector("lightning-datatable");
    expect(table().data.map((row) => row.id)).toEqual(["now"]);
    expect(table().data[0].environmentLabel).toBe("PROD · Produção");
    button(el, "Histórico").click();
    await flush();
    change(el, "view", "ended");
    await flush();
    expect(table().data.map((row) => row.id)).toEqual(["past"]);
    change(el, "view", "scheduled");
    await flush();
    expect(table().data.map((row) => row.id)).toEqual(["next"]);
    change(el, "view", "all");
    await flush();
    expect(table().data).toHaveLength(3);
  });
  it("exige ação explícita para cadastrar, não presume data inicial e permite cancelar", async () => {
    searchOrganizations.mockResolvedValue({ options: [], canManage: true });
    const el = mount();
    await flush();
    expect(el.shadowRoot.querySelector("[data-form]")).toBeNull();
    button(el, "Classificar organização").click();
    await flush();
    const start = [...el.shadowRoot.querySelectorAll("lightning-input")].find(
      (input) => input.name === "validFrom"
    );
    expect(start.value).toBe("");
    expect(start.required).toBe(true);
    expect(
      [...el.shadowRoot.querySelectorAll("lightning-input")].find(
        (input) => input.name === "validTo"
      )
    ).toBeUndefined();
    button(el, "Cancelar").click();
    await flush();
    expect(el.shadowRoot.querySelector("[data-form]")).toBeNull();
    expect(saveMapping).not.toHaveBeenCalled();
  });
  it("revela data final apenas quando solicitada e não permite reabrir período encerrado", async () => {
    searchOrganizations.mockResolvedValue({ options: [], canManage: true });
    const row = {
      id: "map1",
      organizationId: "org1",
      environmentClass: "PROD",
      validFrom: "2026-01-01T00:00:00Z",
      validTo: "2026-06-01T00:00:00Z",
      reason: "Troca de uso"
    };
    listMappings.mockResolvedValue([row]);
    const el = mount();
    await flush();
    button(el, "Classificar organização").click();
    await flush();
    const toggle = [...el.shadowRoot.querySelectorAll("lightning-input")].find(
      (input) => input.name === "hasEnd"
    );
    toggle.checked = true;
    toggle.dispatchEvent(new CustomEvent("change"));
    await flush();
    expect(
      [...el.shadowRoot.querySelectorAll("lightning-input")].find(
        (input) => input.name === "validTo"
      ).required
    ).toBe(true);
    button(el, "Cancelar").click();
    button(el, "Histórico").click();
    await flush();
    change(el, "view", "all");
    await flush();
    el.shadowRoot.querySelector("lightning-datatable").dispatchEvent(
      new CustomEvent("rowaction", {
        detail: { action: { name: "edit" }, row }
      })
    );
    await flush();
    expect(
      [...el.shadowRoot.querySelectorAll("lightning-input")].find(
        (input) => input.name === "hasEnd"
      ).disabled
    ).toBe(true);
  });
  it("não apresenta vazio quando a consulta falha e permite recuperar", async () => {
    listMappings.mockRejectedValueOnce({
      body: { message: "Sem acesso às classificações" }
    });
    const el = mount();
    await flush();
    expect(el.shadowRoot.querySelector('[role="alert"]').textContent).toContain(
      "Sem acesso"
    );
    expect(el.shadowRoot.querySelector(".ds-empty")).toBeNull();
    button(el, "Atualizar lista").click();
    await flush();
    expect(el.shadowRoot.querySelector('[role="alert"]')).toBeNull();
    expect(el.shadowRoot.querySelector(".ds-empty")).not.toBeNull();
  });
});
