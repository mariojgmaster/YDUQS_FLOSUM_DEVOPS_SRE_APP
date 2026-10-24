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
      "lightning-input, lightning-combobox, lightning-textarea"
    )
  ]
    .find((x) => x.name === name)
    .dispatchEvent(new CustomEvent("change", { detail: { value } }));
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
  });
  it("leitor consulta mas não recebe formulário de escrita", async () => {
    const el = mount();
    await flush();
    expect(button(el, "Salvar vigência")).toBeUndefined();
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
    change(el, "organizationId", "org1");
    change(el, "environmentClass", "PROD");
    change(el, "validFrom", "2026-01-01T00:00:00.000Z");
    change(el, "reason", "Classificação aprovada");
    el.shadowRoot.querySelectorAll("[data-form]").forEach((input) => {
      input.reportValidity = jest.fn(() => true);
    });
    button(el, "Salvar vigência").click();
    await flush();
    expect(saveMapping).toHaveBeenCalledWith({
      mappingId: null,
      organizationId: "org1",
      environmentClass: "PROD",
      validFrom: "2026-01-01T00:00:00.000Z",
      validTo: null,
      reason: "Classificação aprovada"
    });
    expect(el.shadowRoot.textContent).toContain("Vigência salva");
    expect(listMappings).toHaveBeenCalledTimes(2);
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
    el.shadowRoot
      .querySelector("lightning-datatable")
      .dispatchEvent(
        new CustomEvent("rowaction", {
          detail: { action: { name: "edit" }, row }
        })
      );
    await flush();
    expect(
      [
        ...el.shadowRoot.querySelectorAll("lightning-input, lightning-combobox")
      ].find((x) => x.name === "organizationId").disabled
    ).toBe(true);
    expect(
      [
        ...el.shadowRoot.querySelectorAll("lightning-input, lightning-combobox")
      ].find((x) => x.name === "environmentClass").disabled
    ).toBe(true);
    expect(
      [
        ...el.shadowRoot.querySelectorAll("lightning-input, lightning-combobox")
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
    el.shadowRoot.querySelectorAll("[data-form]").forEach((input) => {
      input.reportValidity = jest.fn(() => true);
    });
    button(el, "Salvar vigência").click();
    await flush();
    expect(el.shadowRoot.querySelector('[role="alert"]').textContent).toContain(
      "sobrepostas"
    );
    expect(el.shadowRoot.textContent).not.toContain("Vigência salva");
  });
});
