import { createElement } from "lwc";
import DevSrePipelineMonitor from "c/devSrePipelineMonitor";
import listPipelines from "@salesforce/apex/DevSrePipelineMonitorController.listPipelines";
import getPipelineDetail from "@salesforce/apex/DevSrePipelineMonitorController.getPipelineDetail";

jest.mock(
  "@salesforce/apex/DevSrePipelineMonitorController.listPipelines",
  () => ({ default: jest.fn() }),
  { virtual: true }
);
jest.mock(
  "@salesforce/apex/DevSrePipelineMonitorController.getPipelineDetail",
  () => ({ default: jest.fn() }),
  { virtual: true }
);

const flushPromises = async () => {
  await Promise.resolve();
  await Promise.resolve();
};

const PIPELINE_ID = "a01000000000001AAA";

function mount() {
  const component = createElement("c-dev-sre-pipeline-monitor", {
    is: DevSrePipelineMonitor
  });
  document.body.appendChild(component);
  return component;
}

describe("c-dev-sre-pipeline-monitor", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    listPipelines.mockResolvedValue({
      pipelines: [{ id: PIPELINE_ID, name: "Pipeline Real" }],
      hasMore: false
    });
  });

  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("loads real server pipelines rather than built-in demo data", async () => {
    const component = mount();
    await flushPromises();
    expect(listPipelines).toHaveBeenCalledWith({ searchTerm: "" });
    const rows = component.shadowRoot.querySelector(
      'lightning-datatable[data-name="pipelines"]'
    );
    expect(rows.data).toHaveLength(1);
    expect(rows.data[0].name).toBe("Pipeline Real");
  });

  it("shows an empty state when the server returns no pipelines", async () => {
    listPipelines.mockResolvedValue({ pipelines: [], hasMore: false });
    const component = mount();
    await flushPromises();
    expect(component.shadowRoot.textContent).toContain(
      "Nenhum Pipeline encontrado"
    );
  });

  it("fetches steps only for the selected Pipeline", async () => {
    getPipelineDetail.mockResolvedValue({
      id: PIPELINE_ID,
      name: "Pipeline Real",
      canReadNumber: true,
      canReadDescription: true,
      canReadAction: true,
      canReadPass: true,
      canReadFail: false,
      hasMore: false,
      steps: [
        { id: "a02000000000001AAA", stepNumber: 1, description: "Validar", action: "Validate", nextOnPass: "a02000000000002AAA", nextOnFail: null },
        { id: "a02000000000002AAA", stepNumber: 2, description: "Publicar", action: "Deploy", nextOnPass: null, nextOnFail: null }
      ]
    });
    const component = mount();
    await flushPromises();
    const table = component.shadowRoot.querySelector(
      'lightning-datatable[data-name="pipelines"]'
    );
    table.dispatchEvent(
      new CustomEvent("rowaction", {
        detail: { action: { name: "view_steps" }, row: { id: PIPELINE_ID } }
      })
    );
    await flushPromises();
    expect(getPipelineDetail).toHaveBeenCalledWith({ pipelineId: PIPELINE_ID });
    const stepTable = component.shadowRoot.querySelector(
      'lightning-datatable[data-name="steps"]'
    );
    expect(stepTable.data).toHaveLength(2);
    expect(stepTable.data[0].passLabel).toBe("Step 2");
    expect(stepTable.columns.some((col) => col.fieldName === "failLabel")).toBe(false);
  });

  it("shows safe server errors without rendering a fake successful list", async () => {
    listPipelines.mockRejectedValue({ body: { message: "Acesso negado." } });
    const component = mount();
    await flushPromises();
    expect(component.shadowRoot.textContent).toContain("Acesso negado.");
    expect(component.shadowRoot.querySelector('lightning-datatable[data-name="pipelines"]')).toBeNull();
  });

  it("reissues the current query when the user selects Atualizar", async () => {
    const component = mount();
    await flushPromises();
    const updateButton = component.shadowRoot.querySelector('header lightning-button');
    updateButton.click();
    await flushPromises();
    expect(listPipelines).toHaveBeenCalledTimes(2);
  });

  it("clearly warns when the backend truncates the list", async () => {
    listPipelines.mockResolvedValue({ pipelines: [{ id: PIPELINE_ID, name: "Pipeline Real" }], hasMore: true });
    const component = mount();
    await flushPromises();
    expect(component.shadowRoot.textContent).toContain("Mais de 50 Pipelines encontrados");
  });
});
