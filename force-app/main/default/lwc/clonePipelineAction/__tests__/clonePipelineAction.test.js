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
  suggestedName: "Pipeline Origem - Cópia",
  stepCount: 2,
  maxNameLength: 80
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
      "Pipeline Origem - Cópia"
    );
    expect(element.shadowRoot.textContent).toContain("2 Pipeline Steps");
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
      pipelineName: "Pipeline Origem - Cópia",
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
