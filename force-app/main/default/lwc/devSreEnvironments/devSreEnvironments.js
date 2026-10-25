import { LightningElement } from "lwc";
import { NavigationMixin } from "lightning/navigation";
import loadOverview from "@salesforce/apex/DevSreEnvironmentController.loadOverview";

export default class DevSreEnvironments extends NavigationMixin(LightningElement) {
  period = "30";
  organizationId = "";
  loading = true;
  error = "";
  data;
  selectedId;
  requestVersion = 0;

  connectedCallback() { this.load(); }
  disconnectedCallback() { ++this.requestVersion; }
  get periodOptions() {
    return [
      { label: "Últimos 7 dias", value: "7" },
      { label: "Últimos 30 dias", value: "30" },
      { label: "Últimos 90 dias", value: "90" }
    ];
  }
  get complete() { return this.data && this.data.complete; }
  get hasRows() { return this.complete && this.data.organizations.length > 0; }
  get rows() {
    return (this.data?.organizations || []).map(row => ({
      ...row,
      count: row.deployments + row.validations + row.otherOperations,
      selected: row.id === this.selectedId,
      selectedClass: row.id === this.selectedId ? "org-row org-row_selected" : "org-row"
    }));
  }
  get selected() {
    return this.rows.find(row => row.id === this.selectedId) || null;
  }
  get hasSelection() { return Boolean(this.selected); }
  get metrics() {
    if (!this.complete) return [];
    return [
      { key: "orgs", label: "Organizações consultadas", value: this.data.organizationCount },
      { key: "deploys", label: "Deployments", value: this.data.deploymentCount },
      { key: "validates", label: "Validações", value: this.data.validationCount },
      { key: "success", label: "Operações com sucesso", value: this.data.successCount },
      { key: "failed", label: "Operações com falha", value: this.data.failureCount }
    ];
  }
  handlePeriod(event) { this.period = event.detail.value; this.load(); }
  handleOrganization(event) {
    this.organizationId = event.detail.recordId || "";
    this.selectedId = null;
    this.load();
  }
  handleClear() {
    this.organizationId = "";
    this.selectedId = null;
    this.load();
  }
  handleSelect(event) { this.selectedId = event.currentTarget.dataset.id; }
  handleClose() { this.selectedId = null; }
  handleRefresh() { this.load(); }
  handleOpenOrg(event) { this.open(event.currentTarget.dataset.id, "Flosum__Organisation__c"); }
  handleOpenLog(event) { this.open(event.currentTarget.dataset.id, "Flosum__Metadata_Log__c"); }
  open(recordId, objectApiName) {
    if (!recordId) return;
    this[NavigationMixin.Navigate]({
      type: "standard__recordPage",
      attributes: { recordId, objectApiName, actionName: "view" }
    });
  }
  async load() {
    const version = ++this.requestVersion;
    this.loading = true;
    this.error = "";
    try {
      const result = await loadOverview({
        days: Number(this.period),
        organizationId: this.organizationId || null
      });
      if (version !== this.requestVersion) return;
      this.data = result;
      if (!this.selectedId || !(result.organizations || []).some(r => r.id === this.selectedId)) {
        this.selectedId = result.organizations?.[0]?.id || null;
      }
    } catch (ex) {
      if (version !== this.requestVersion) return;
      this.data = null;
      this.error = ex?.body?.message || "Não foi possível consultar as operações das organizações.";
    } finally {
      if (version === this.requestVersion) this.loading = false;
    }
  }
}
