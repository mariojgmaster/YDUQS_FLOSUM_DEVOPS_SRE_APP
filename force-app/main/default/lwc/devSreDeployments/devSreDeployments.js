import { LightningElement, api } from "lwc";
import { NavigationMixin } from "lightning/navigation";
import listDeployments from "@salesforce/apex/DevSreDeploymentController.listDeployments";
import searchOrganizations from "@salesforce/apex/DevSreEnvironmentController.searchOrganizations";

const RESULTS = {
  Success: "Sucesso",
  Failed: "Falha",
  Partial: "Parcial",
  NotRun: "Não executado",
  Pending: "Em andamento",
  Unknown: "Desconhecido"
};
const DATE = {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  timeZone: "UTC"
};
export default class DevSreDeployments extends NavigationMixin(
  LightningElement
) {
  rows = [];
  error = "";
  loading = false;
  fromDate = new Date(Date.now() - 90 * 86400000).toISOString().slice(0, 10);
  toDate = new Date().toISOString().slice(0, 10);
  organizationId = "";
  organizationSearch = "";
  organizations = [{ label: "Todas as organizações", value: "" }];
  organizationsHaveMore = false;
  environmentClass = "";
  outcome = "";
  branchId = "";
  hasMore = false;
  cursorCreated = null;
  cursorId = null;
  inspectedRows = 0;
  requestVersion = 0;
  organizationVersion = 0;
  correlationIncomplete = false;
  columns = [
    {
      label: "Deployment",
      fieldName: "name",
      type: "button",
      typeAttributes: {
        label: { fieldName: "name" },
        name: "source",
        variant: "base"
      }
    },
    { label: "Organização", fieldName: "organizationName" },
    { label: "Ambiente", fieldName: "environmentClass" },
    {
      label: "Branch",
      fieldName: "branchName",
      type: "button",
      typeAttributes: {
        label: { fieldName: "branchName" },
        name: "branch",
        variant: "base",
        disabled: { fieldName: "noBranch" }
      }
    },
    { label: "Resultado", fieldName: "outcomeLabel" },
    {
      label: "Início (UTC)",
      fieldName: "startedAt",
      type: "date",
      typeAttributes: DATE
    },
    {
      label: "Conclusão (UTC)",
      fieldName: "completedAt",
      type: "date",
      typeAttributes: DATE
    },
    { label: "Duração (s)", fieldName: "durationSeconds", type: "number" },
    { label: "Qualidade / correlação", fieldName: "quality", wrapText: true }
  ];
  get environmentOptions() {
    return [
      { label: "Todos os ambientes", value: "" },
      ...["PROD", "UAT", "SIT", "DEV", "UNKNOWN", "AMBIGUOUS"].map((value) => ({
        label: value,
        value
      }))
    ];
  }
  get outcomeOptions() {
    return [
      { label: "Todos os resultados", value: "" },
      ...Object.keys(RESULTS).map((value) => ({ label: RESULTS[value], value }))
    ];
  }
  get hasRows() {
    return this.rows.length > 0;
  }
  get statusLabel() {
    return `${this.rows.length} registros nesta página; ${this.inspectedRows} registros de origem examinados. Não é um total global.`;
  }
  get nextDisabled() {
    return this.loading || !this.hasMore;
  }
  connectedCallback() {
    this.loadOrganizations();
    this.load(false);
  }
  disconnectedCallback() {
    this.requestVersion++;
    this.organizationVersion++;
  }
  handleChange(event) {
    this[event.target.name] = event.detail?.value ?? event.target.value;
    this.requestVersion++;
    this.loading = false;
    this.rows = [];
    this.hasMore = false;
    this.cursorCreated = null;
    this.cursorId = null;
    this.inspectedRows = 0;
  }
  async loadOrganizations() {
    const version = ++this.organizationVersion;
    try {
      const page = await searchOrganizations({
        searchTerm: this.organizationSearch
      });
      if (version !== this.organizationVersion) return;
      this.organizations = [
        { label: "Todas as organizações", value: "" },
        ...page.options
      ];
      this.organizationsHaveMore = page.hasMore;
    } catch {
      if (version === this.organizationVersion)
        this.error =
          "Não foi possível consultar organizações. Revise seu acesso ou tente novamente.";
    }
  }
  handleSearchOrganizations() {
    this.loadOrganizations();
  }
  handleSearch() {
    this.load(false);
  }
  @api refresh() {
    this.load(false);
  }
  handleNext() {
    this.load(true);
  }
  async load(next) {
    const version = ++this.requestVersion;
    this.loading = true;
    this.error = "";
    this.rows = [];
    this.inspectedRows = 0;
    const fields = [
      ...this.template.querySelectorAll("lightning-input, lightning-combobox")
    ];
    if (!fields.every((input) => input.reportValidity())) {
      this.loading = false;
      return;
    }
    try {
      if (!this.fromDate || !this.toDate) throw new Error("period");
      const fromUtc = `${this.fromDate}T00:00:00.000Z`;
      const toUtc = new Date(
        new Date(`${this.toDate}T00:00:00.000Z`).getTime() + 86400000
      ).toISOString();
      const page = await listDeployments({
        fromUtc,
        toUtc,
        organizationId: this.organizationId || null,
        branchId: this.branchId.trim() || null,
        environmentClass: this.environmentClass || null,
        outcome: this.outcome || null,
        cursorCreated: next ? this.cursorCreated : null,
        cursorId: next ? this.cursorId : null
      });
      if (version !== this.requestVersion) return;
      this.rows = page.rows.map((row) => ({
        ...row,
        noBranch: !row.branchId,
        outcomeLabel: RESULTS[row.outcome] || "Desconhecido"
      }));
      this.hasMore = page.hasMore;
      this.cursorCreated = page.cursorCreated;
      this.cursorId = page.cursorId;
      this.inspectedRows = page.inspectedRows;
      this.correlationIncomplete = page.correlationIncomplete;
    } catch (error) {
      if (version === this.requestVersion) {
        this.error =
          error?.body?.message ||
          "Não foi possível consultar. Verifique o período, os filtros e suas permissões.";
        this.hasMore = false;
      }
    } finally {
      if (version === this.requestVersion) this.loading = false;
    }
  }
  handleRowAction(event) {
    const row = event.detail.row;
    const branch = event.detail.action.name === "branch";
    const recordId = branch ? row.branchId : row.id;
    if (recordId)
      this[NavigationMixin.Navigate]({
        type: "standard__recordPage",
        attributes: {
          recordId,
          objectApiName: branch
            ? "Flosum__Branch__c"
            : "Flosum__Metadata_Log__c",
          actionName: "view"
        }
      });
  }
}
