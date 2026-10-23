import { api, LightningElement } from "lwc";
import { CloseActionScreenEvent } from "lightning/actions";
import { NavigationMixin } from "lightning/navigation";
import { ShowToastEvent } from "lightning/platformShowToastEvent";
import getPreview from "@salesforce/apex/ClonePipelineController.getPreview";
import clonePipeline from "@salesforce/apex/ClonePipelineController.clonePipeline";

export default class ClonePipelineAction extends NavigationMixin(
  LightningElement
) {
  _recordId;
  _previewRequestId = 0;
  isLoading = true;
  isSubmitting = false;
  sourceName;
  newName = "";
  stepCount = 0;
  steps = [];
  maxNameLength = 80;
  loadError;
  submitError;

  @api
  get recordId() {
    return this._recordId;
  }

  set recordId(value) {
    if (value && value !== this._recordId) {
      this._recordId = value;
      this.loadPreview();
    }
  }

  get stepCountLabel() {
    return this.stepCount === 1
      ? "1 Pipeline Step"
      : `${this.stepCount} Pipeline Steps`;
  }

  get previewSectionLabel() {
    return `Pré-visualização dos Pipeline Steps (${this.stepCount})`;
  }

  get nameCounter() {
    return `${this.newName.length}/${this.maxNameLength}`;
  }

  get hasNoSteps() {
    return this.stepCount === 0;
  }

  get hasStepDetails() {
    return this.steps.length > 0;
  }

  get stepItems() {
    return this.steps.map((step, index) => ({
      key: `step-${index}`,
      number: step.number == null ? index + 1 : step.number,
      description:
        (typeof step.description === "string" && step.description.trim()) ||
        (typeof step.action === "string" && step.action.trim()) ||
        `Step ${index + 1}`,
      action: step.action || ""
    }));
  }

  get isCloneDisabled() {
    return (
      this.isLoading ||
      this.isSubmitting ||
      Boolean(this.loadError) ||
      !this._recordId ||
      !this.newName.trim() ||
      this.newName.trim().length > this.maxNameLength
    );
  }

  get submitLabel() {
    return this.isSubmitting ? "Clonando..." : "Clonar Pipeline";
  }

  async loadPreview() {
    const requestedRecordId = this._recordId;
    const requestId = ++this._previewRequestId;
    this.isLoading = true;
    this.loadError = undefined;
    this.submitError = undefined;
    this.sourceName = undefined;
    this.newName = "";
    this.stepCount = 0;
    this.steps = [];

    try {
      const preview = await getPreview({
        sourcePipelineId: requestedRecordId
      });
      // A delayed preview must not overwrite the currently selected Pipeline.
      if (requestId !== this._previewRequestId) {
        return;
      }
      this.sourceName = preview.sourceName;
      this.newName = preview.suggestedName;
      this.stepCount = preview.stepCount;
      this.maxNameLength = preview.maxNameLength;
      // Compatible with Apex versions deployed before the optional details.
      this.steps = Array.isArray(preview.steps) ? preview.steps : [];
    } catch (error) {
      if (requestId === this._previewRequestId) {
        this.loadError = this.normalizeError(error);
      }
    } finally {
      if (requestId === this._previewRequestId) {
        this.isLoading = false;
      }
    }
  }

  handleNameChange(event) {
    this.newName = event.target.value || "";
    this.submitError = undefined;
  }

  handleCancel() {
    if (!this.isSubmitting) {
      this.dispatchEvent(new CloseActionScreenEvent());
    }
  }

  async handleClone() {
    if (this.isCloneDisabled) {
      return;
    }
    const nameInput = this.template.querySelector(
      '[data-name="pipeline-name"]'
    );
    if (nameInput && !nameInput.reportValidity()) {
      return;
    }

    const sourcePipelineId = this._recordId;
    this.isSubmitting = true;
    this.submitError = undefined;
    try {
      const result = await clonePipeline({
        sourcePipelineId,
        newName: this.newName.trim()
      });
      this.dispatchEvent(
        new ShowToastEvent({
          title: "Pipeline clonado",
          message: `${result.pipelineName} foi criado com ${result.stepCount} Pipeline Steps.`,
          variant: "success"
        })
      );
      this.dispatchEvent(new CloseActionScreenEvent());
      this[NavigationMixin.Navigate]({
        type: "standard__recordPage",
        attributes: {
          recordId: result.pipelineId,
          objectApiName: "Flosum__Pipeline__c",
          actionName: "view"
        }
      });
    } catch (error) {
      this.submitError = this.normalizeError(error);
    } finally {
      this.isSubmitting = false;
    }
  }

  normalizeError(error) {
    return (
      error?.body?.message ||
      error?.message ||
      "Não foi possível clonar o Pipeline."
    );
  }
}
