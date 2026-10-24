import { LightningElement } from "lwc";
import { NavigationMixin } from "lightning/navigation";
import listPipelines from "@salesforce/apex/DevSrePipelineMonitorController.listPipelines";
import getPipelineDetail from "@salesforce/apex/DevSrePipelineMonitorController.getPipelineDetail";

const PIPELINE_COLUMNS = [
  { label: "Pipeline", fieldName: "name", type: "text" },
  {
    type: "action",
    typeAttributes: {
      rowActions: [
        { label: "Visualizar etapas", name: "view_steps" },
        { label: "Abrir no Flosum", name: "open_record" }
      ]
    }
  }
];

export default class DevSrePipelineMonitor extends NavigationMixin(LightningElement) {
  pipelineColumns = PIPELINE_COLUMNS;
  pipelines = [];
  steps = [];
  selectedId;
  selectedName;
  searchTerm = "";
  appliedSearch = "";
  isLoading = false;
  isLoadingSteps = false;
  listError;
  detailError;
  listHasMore = false;
  detailHasMore = false;
  fieldAccess = {};
  _listRequest = 0;
  _detailRequest = 0;

  connectedCallback() {
    this.loadPipelines();
  }

  get hasPipelines() {
    return this.pipelines.length > 0;
  }

  get hasSelection() {
    return Boolean(this.selectedId);
  }

  get hasSteps() {
    return this.steps.length > 0;
  }

  get listCountLabel() {
    return `${this.pipelines.length} Pipeline(s) exibido(s)`;
  }

  get stepCountLabel() {
    return `${this.steps.length} Step(s) exibido(s)`;
  }

  get stepColumns() {
    const columns = [];
    if (this.fieldAccess.canReadNumber) {
      columns.push({ label: "Nº", fieldName: "stepNumberLabel", type: "text", initialWidth: 75 });
    }
    if (this.fieldAccess.canReadDescription) {
      columns.push({ label: "Descrição", fieldName: "description", type: "text" });
    }
    if (this.fieldAccess.canReadAction) {
      columns.push({ label: "Ação", fieldName: "action", type: "text" });
    }
    if (this.fieldAccess.canReadPass) {
      columns.push({ label: "On Pass", fieldName: "passLabel", type: "text" });
    }
    if (this.fieldAccess.canReadFail) {
      columns.push({ label: "On Fail", fieldName: "failLabel", type: "text" });
    }
    return columns;
  }

  get hasStepColumns() {
    return this.stepColumns.length > 0;
  }

  get isSearchDisabled() {
    return this.isLoading || this.searchTerm.trim().length > 80;
  }

  handleSearchChange(event) {
    this.searchTerm = event.target.value || "";
  }

  handleSearch() {
    if (!this.isSearchDisabled) {
      this.appliedSearch = this.searchTerm.trim();
      this.loadPipelines();
    }
  }

  handleRefresh() {
    this.loadPipelines();
  }

  async loadPipelines() {
    const request = ++this._listRequest;
    ++this._detailRequest;
    this.isLoading = true;
    this.isLoadingSteps = false;
    this.listError = undefined;
    this.detailError = undefined;
    this.selectedId = undefined;
    this.selectedName = undefined;
    this.steps = [];
    this.fieldAccess = {};
    this.detailHasMore = false;
    this.pipelines = [];
    this.listHasMore = false;
    try {
      const response = await listPipelines({ searchTerm: this.appliedSearch });
      if (request !== this._listRequest) return;
      this.pipelines = Array.isArray(response?.pipelines) ? response.pipelines : [];
      this.listHasMore = Boolean(response?.hasMore);
    } catch (error) {
      if (request === this._listRequest) {
        this.listError = this.normalizeError(error, "Falha ao consultar Pipelines.");
      }
    } finally {
      if (request === this._listRequest) this.isLoading = false;
    }
  }

  handleRowAction(event) {
    const row = event.detail.row;
    const action = event.detail.action?.name;
    if (action === "open_record") {
      this.navigateToPipeline(row.id);
    } else if (action === "view_steps") {
      this.loadDetails(row.id);
    }
  }

  async loadDetails(pipelineId) {
    const request = ++this._detailRequest;
    this.selectedId = pipelineId;
    this.selectedName = undefined;
    this.detailError = undefined;
    this.isLoadingSteps = true;
    this.steps = [];
    this.fieldAccess = {};
    this.detailHasMore = false;
    try {
      const detail = await getPipelineDetail({ pipelineId });
      if (request !== this._detailRequest) return;
      this.selectedName = detail.name;
      this.fieldAccess = {
        canReadNumber: Boolean(detail.canReadNumber),
        canReadDescription: Boolean(detail.canReadDescription),
        canReadAction: Boolean(detail.canReadAction),
        canReadPass: Boolean(detail.canReadPass),
        canReadFail: Boolean(detail.canReadFail)
      };
      const steps = Array.isArray(detail.steps) ? detail.steps : [];
      const byId = new Map(
        steps.map((step, index) => [
          step.id,
          step.stepNumber == null ? `Etapa exibida ${index + 1}` : `Step ${step.stepNumber}`
        ])
      );
      this.steps = steps.map((step) => ({
        ...step,
        stepNumberLabel: step.stepNumber == null ? "—" : String(step.stepNumber),
        description: step.description || "—",
        action: step.action || "—",
        passLabel: this.targetLabel(step.nextOnPass, byId),
        failLabel: this.targetLabel(step.nextOnFail, byId)
      }));
      this.detailHasMore = Boolean(detail.hasMore);
    } catch (error) {
      if (request === this._detailRequest) {
        this.detailError = this.normalizeError(error, "Falha ao consultar os Steps.");
      }
    } finally {
      if (request === this._detailRequest) this.isLoadingSteps = false;
    }
  }

  targetLabel(id, byId) {
    if (!id) return "—";
    return byId.get(id) || "Step não exibido";
  }

  handleOpenSelected() {
    if (this.selectedId) this.navigateToPipeline(this.selectedId);
  }

  navigateToPipeline(id) {
    this[NavigationMixin.Navigate]({
      type: "standard__recordPage",
      attributes: {
        recordId: id,
        objectApiName: "Flosum__Pipeline__c",
        actionName: "view"
      }
    });
  }

  normalizeError(error, fallback) {
    return error?.body?.message || fallback;
  }
}
