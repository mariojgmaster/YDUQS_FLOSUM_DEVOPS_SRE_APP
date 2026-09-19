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
  isLoading = true;
  isSubmitting = false;
  sourceName;
  newName = "";
  stepCount = 0;
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

  get isCloneDisabled() {
    return this.isLoading || this.isSubmitting || !this.newName.trim();
  }

  get submitLabel() {
    return this.isSubmitting ? "Clonando..." : "Clonar";
  }

  async loadPreview() {
    this.isLoading = true;
    this.loadError = undefined;
    try {
      const preview = await getPreview({ sourcePipelineId: this._recordId });
      this.sourceName = preview.sourceName;
      this.newName = preview.suggestedName;
      this.stepCount = preview.stepCount;
      this.maxNameLength = preview.maxNameLength;
    } catch (error) {
      this.loadError = this.normalizeError(error);
    } finally {
      this.isLoading = false;
    }
  }

  handleNameChange(event) {
    this.newName = event.target.value;
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

    const nameInput = this.template.querySelector("lightning-input");
    if (nameInput && !nameInput.reportValidity()) {
      return;
    }

    this.isSubmitting = true;
    this.submitError = undefined;
    try {
      const result = await clonePipeline({
        sourcePipelineId: this._recordId,
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
