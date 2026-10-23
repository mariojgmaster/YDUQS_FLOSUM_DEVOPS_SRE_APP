import { createElement } from "lwc";
import ClonePipelineAction from "c/clonePipelineAction";
import getPreview from "@salesforce/apex/ClonePipelineController.getPreview";
import clonePipeline from "@salesforce/apex/ClonePipelineController.clonePipeline";

const mockNavigate = jest.fn();

jest.mock("lightning/navigation", () => {
  const Navigate = Symbol("Navigate");
  const NavigationMixin = (Base) =>
    class extends Base {
      [Navigate](pageReference) {
        mockNavigate(pageReference);
      }
    };
  NavigationMixin.Navigate = Navigate;
  return { NavigationMixin };
});
jest.mock(
  "lightning/actions",
  () => ({
    CloseActionScreenEvent: class CloseActionScreenEvent extends CustomEvent {
      constructor() {
        super("close");
      }
    }
  }),
  { virtual: true }
);
jest.mock(
  "@salesforce/apex/ClonePipelineController.getPreview",
  () => ({ default: jest.fn() }),
  { virtual: true }
);
jest.mock(
  "@salesforce/apex/ClonePipelineController.clonePipeline",
  () => ({ default: jest.fn() }),
  { virtual: true }
);

const PREVIEW = {
  sourceName: "Pipeline Origem",
  suggestedName: "Pipeline Origem - Cópia 01",
  stepCount: 2,
  maxNameLength: 80,
  steps: [
    { stepNumber: 1, description: "Primeiro passo", action: "Deploy" },
    { stepNumber: 2, description: "Segundo passo", action: "Validate" }
  ]
};

const flushPromises = async () => {
  await Promise.resolve();
  await Promise.resolve();
};

function createComponent() {
  const element = createElement("c-clone-pipeline-action", {
    is: ClonePipelineAction
  });
  document.body.appendChild(element);
  element.recordId = "a01000000000001AAA";
  return element;
}

describe("c-clone-pipeline-action", () => {
  afterEach(() => {
    while (document.body.firstChild) {
      document.body.removeChild(document.body.firstChild);
    }
    jest.clearAllMocks();
  });

  it("loads the preview and shows the suggested name and step count", async () => {
    getPreview.mockResolvedValue(PREVIEW);
    const element = createComponent();

    await flushPromises();

    expect(getPreview).toHaveBeenCalledWith({
      sourcePipelineId: "a01000000000001AAA"
    });
    expect(element.shadowRoot.querySelector("lightning-input").value).toBe(
      "Pipeline Origem - Cópia 01"
    );
    expect(element.shadowRoot.textContent).toContain("2 Pipeline Steps");
  });

  it("renders a read-only Step preview and a character counter", async () => {
    getPreview.mockResolvedValue(PREVIEW);
    const element = createComponent();
    await flushPromises();

    expect(element.shadowRoot.textContent).toContain("Primeiro passo");
    expect(element.shadowRoot.textContent).toContain("Segundo passo");
    expect(element.shadowRoot.textContent).toContain("2 Pipeline Steps");
    expect(element.shadowRoot.textContent).toContain(
      `${PREVIEW.suggestedName.length}/80`
    );
  });

  it("shows the zero-Step message without blocking cloning", async () => {
    getPreview.mockResolvedValue({
      ...PREVIEW,
      stepCount: 0,
      steps: []
    });
    const element = createComponent();
    await flushPromises();

    expect(element.shadowRoot.textContent).toContain(
      "Este Pipeline não possui Steps"
    );
    expect(element.shadowRoot.querySelectorAll("lightning-button")[1].disabled)
      .toBe(false);
  });

  it("supports an older Apex preview with no detailed Step list", async () => {
    getPreview.mockResolvedValue({
      sourceName: PREVIEW.sourceName,
      suggestedName: PREVIEW.suggestedName,
      stepCount: PREVIEW.stepCount,
      maxNameLength: PREVIEW.maxNameLength
    });
    const element = createComponent();
    await flushPromises();

    expect(element.shadowRoot.textContent).toContain(
      "A lista detalhada de Steps não está disponível"
    );
  });

  it("disables cloning when a new record preview fails", async () => {
    getPreview.mockResolvedValueOnce(PREVIEW).mockRejectedValueOnce({
      body: { message: "Não foi possível carregar o Pipeline." }
    });
    const element = createComponent();
    await flushPromises();

    expect(element.shadowRoot.querySelector("lightning-input").value).toBe(
      "Pipeline Origem - Cópia 01"
    );

    element.recordId = "a01000000000003AAA";
    await flushPromises();

    expect(element.shadowRoot.textContent).toContain(
      "Não foi possível carregar o Pipeline."
    );
    expect(
      element.shadowRoot.querySelectorAll("lightning-button")[1].disabled
    ).toBe(true);
    expect(clonePipeline).not.toHaveBeenCalled();
  });

  it("ignores a late preview for a previous record", async () => {
    let resolvePreviousPreview;
    getPreview
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolvePreviousPreview = resolve;
          })
      )
      .mockResolvedValueOnce({
        ...PREVIEW,
        sourceName: "Pipeline Atual",
        suggestedName: "Pipeline Atual - Cópia",
        stepCount: 1
      });

    const element = createComponent();
    element.recordId = "a01000000000003AAA";
    await flushPromises();

    resolvePreviousPreview(PREVIEW);
    await flushPromises();

    expect(getPreview).toHaveBeenCalledTimes(2);
    expect(element.shadowRoot.querySelector("lightning-input").value).toBe(
      "Pipeline Atual - Cópia"
    );
    expect(element.shadowRoot.textContent).toContain("1 Pipeline Step");
  });

  it("does not submit a blank name", async () => {
    getPreview.mockResolvedValue(PREVIEW);
    const element = createComponent();
    await flushPromises();

    const input = element.shadowRoot.querySelector("lightning-input");
    input.value = "   ";
    input.dispatchEvent(new CustomEvent("change"));
    await flushPromises();

    const buttons = element.shadowRoot.querySelectorAll("lightning-button");
    expect(buttons[1].disabled).toBe(true);
    expect(clonePipeline).not.toHaveBeenCalled();
  });

  it("clears a server error when the user edits the name", async () => {
    getPreview.mockResolvedValue(PREVIEW);
    clonePipeline.mockRejectedValue({
      body: { message: "O nome do Pipeline já existe." }
    });
    const element = createComponent();
    await flushPromises();

    const input = element.shadowRoot.querySelector("lightning-input");
    input.reportValidity = jest.fn().mockReturnValue(true);
    element.shadowRoot.querySelectorAll("lightning-button")[1].click();
    await flushPromises();
    expect(element.shadowRoot.textContent).toContain(
      "O nome do Pipeline já existe."
    );

    input.value = "Novo nome";
    input.dispatchEvent(new CustomEvent("change"));
    await flushPromises();
    expect(element.shadowRoot.textContent).not.toContain(
      "O nome do Pipeline já existe."
    );
  });

  it("submits only once while processing", async () => {
    getPreview.mockResolvedValue(PREVIEW);
    clonePipeline.mockReturnValue(new Promise(() => {}));
    const element = createComponent();
    await flushPromises();

    element.shadowRoot.querySelector("lightning-input").reportValidity = jest
      .fn()
      .mockReturnValue(true);
    const cloneButton =
      element.shadowRoot.querySelectorAll("lightning-button")[1];
    cloneButton.click();
    cloneButton.click();
    await flushPromises();

    expect(clonePipeline).toHaveBeenCalledTimes(1);
    expect(cloneButton.disabled).toBe(true);
  });

  it("closes and navigates to the clone after success", async () => {
    getPreview.mockResolvedValue(PREVIEW);
    clonePipeline.mockResolvedValue({
      pipelineId: "a01000000000002AAA",
      pipelineName: "Pipeline Origem - Cópia 01",
      stepCount: 2
    });
    const element = createComponent();
    const events = [];
    element.addEventListener("lightning__showtoast", (event) =>
      events.push(event)
    );
    element.addEventListener("close", (event) => events.push(event));
    await flushPromises();

    element.shadowRoot.querySelector("lightning-input").reportValidity = jest
      .fn()
      .mockReturnValue(true);
    element.shadowRoot.querySelectorAll("lightning-button")[1].click();
    await flushPromises();

    expect(clonePipeline).toHaveBeenCalledTimes(1);
    expect(events.some((event) => event.type === "lightning__showtoast")).toBe(
      true
    );
    expect(events.some((event) => event.type === "close")).toBe(true);
    expect(mockNavigate).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "standard__recordPage",
        attributes: expect.objectContaining({ recordId: "a01000000000002AAA" })
      })
    );
  });

  it("shows a safe server error and keeps the action open", async () => {
    getPreview.mockResolvedValue(PREVIEW);
    clonePipeline.mockRejectedValue({
      body: { message: "Permissão insuficiente." }
    });
    const element = createComponent();
    await flushPromises();

    element.shadowRoot.querySelector("lightning-input").reportValidity = jest
      .fn()
      .mockReturnValue(true);
    element.shadowRoot.querySelectorAll("lightning-button")[1].click();
    await flushPromises();

    expect(element.shadowRoot.textContent).toContain("Permissão insuficiente.");
  });
});
