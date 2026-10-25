import { LightningElement, api } from "lwc";
import { NavigationMixin } from "lightning/navigation";
import listDeployments from "@salesforce/apex/DevSreDeploymentController.listDeployments";
import listDeploymentsWithSearch from "@salesforce/apex/DevSreDeploymentController.listDeploymentsWithSearch";
import searchOrganizations from "@salesforce/apex/DevSreEnvironmentController.searchOrganizations";

const RESULTS = {
  Success: "Sucesso",
  Failed: "Falha",
  Partial: "Parcial",
  NotRun: "Não executado",
  Pending: "Em andamento",
  Unknown: "Desconhecido"
};
const ENVIRONMENTS = {
  PROD: "PROD · Produção",
  UAT: "UAT · Homologação",
  SIT: "SIT · Integração",
  DEV: "DEV · Desenvolvimento",
  UNKNOWN: "Não identificado",
  AMBIGUOUS: "Classificação conflitante"
};
const formatUTC = (value) =>
  (value
    ? new Intl.DateTimeFormat("pt-BR", {
        timeZone: "UTC",
        day: "2-digit", month: "2-digit", year: "numeric",
        hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false
      }).format(new Date(value))
    : "—");
const durationLabel = (seconds) =>
  (seconds === null || seconds === undefined
    ? "—"
    : Math.floor(Number(seconds) / 60) + " min " + Math.round(Number(seconds) % 60) + " s");
const csvCell = (value) => {
  const raw = String(value ?? "");
  const safe = /^[=+\-@\t\r]/.test(raw) ? "'" + raw : raw;
  return '"' + safe.replace(/"/g, '""') + '"';
};
export default class DevSreDeployments extends NavigationMixin(
  LightningElement
) {
  rows = [];
  searchTerm = "";
  selectedId = null;
  csvStatus = "";
  advancedSection = "";
  sourceSection = "";
  sortBy = "";
  sortDirection = "asc";
  error = "";
  organizationError = "";
  organizationsLoading = false;
  filtersDirty = false;
  pageNumber = 1;
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
    { label: "Deployment / Branch", fieldName: "name", sortable: true, type: "button", typeAttributes: { label: { fieldName: "name" }, name: "details", variant: "base" } },
    { label: "Organização", fieldName: "organizationName", sortable: true },
    { label: "Ambiente", fieldName: "environmentLabel", sortable: true },
    { label: "Resultado", fieldName: "outcomeLabel", sortable: true, cellAttributes: { class: { fieldName: "outcomeTone" } } },
    { label: "Conclusão (UTC)", fieldName: "completionLabel", sortable: true },
    { label: "Duração", fieldName: "durationLabel", sortable: true },
    { type: "button-icon", initialWidth: 58, typeAttributes: { name: "details", iconName: "utility:chevronright", variant: "border", alternativeText: "Detalhes" } }
  ];
  get environmentOptions() {
    return [
      { label: "Todos os ambientes", value: "" },
      ...["PROD", "UAT", "SIT", "DEV", "UNKNOWN", "AMBIGUOUS"].map((value) => ({
        label: ENVIRONMENTS[value],
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
  get selectedRow() {
    return this.rows.find((row) => row.id === this.selectedId) || null;
  }
  get hasSelection() {
    return Boolean(this.selectedRow);
  }
  get exportDisabled() {
    return !this.hasRows || this.loading || this.filtersDirty || Boolean(this.error);
  }
  get statusLabel() {
    return `${this.rows.length} deployments nesta página · Página ${this.pageNumber}`;
  }
  get showResults() {
    return !this.error;
  }
  get hasUnclassified() {
    return this.rows.some((row) =>
      ["UNKNOWN", "AMBIGUOUS"].includes(row.environmentClass)
    );
  }
  get paginationLabel() {
    return this.hasMore
      ? "Há mais registros de origem a examinar. Continue a consulta na próxima página."
      : "Fim dos registros para estes filtros.";
  }
  get emptyDescription() {
    return this.hasMore
      ? "Há mais registros a examinar. Avance para a próxima página ou ajuste os filtros."
      : "Ajuste o período, a organização ou os demais filtros e tente novamente.";
  }
  get nextDisabled() {
    return this.loading || this.filtersDirty || !this.hasMore;
  }
  connectedCallback() {
    this.load(false);
  }
  disconnectedCallback() {
    this.requestVersion++;
    this.organizationVersion++;
  }
  handleOrganizationPicker(event) {
    this.handleChange({ target: { name: "organizationId", value: event.detail.recordId || "" }, detail: { value: event.detail.recordId || "" } });
  }
  handleChange(event) {
    this[event.target.name] = event.detail?.value ?? event.target.value;
    if (event.target.name === "organizationSearch") return;
    this.filtersDirty = true;
    this.error = "";
    this.correlationIncomplete = false;
    this.requestVersion++;
    this.loading = false;
    this.rows = [];
    this.selectedId = null;
    this.csvStatus = "";
    this.hasMore = false;
    this.cursorCreated = null;
    this.cursorId = null;
    this.inspectedRows = 0;
  }
  async loadOrganizations() {
    const version = ++this.organizationVersion;
    this.organizationsLoading = true;
    this.organizationError = "";
    try {
      const page = await searchOrganizations({
        searchTerm: this.organizationSearch
      });
      if (version !== this.organizationVersion) return;
      this.organizations = [
        { label: "Todas as organizações", value: "" },
        ...page.options,
        ...this.organizations.filter(
          (item) =>
            item.value &&
            item.value === this.organizationId &&
            !page.options.some((option) => option.value === item.value)
        )
      ];
      this.organizationsHaveMore = page.hasMore;
    } catch {
      if (version === this.organizationVersion)
        this.organizationError =
          "Não foi possível consultar organizações. Revise seu acesso ou tente novamente.";
    } finally {
      if (version === this.organizationVersion)
        this.organizationsLoading = false;
    }
  }
  handleSearchOrganizations() {
    this.loadOrganizations();
  }
  handleSearch() {
    this.load(false);
  }
  handleClear() {
    this.fromDate = new Date(Date.now() - 90 * 86400000).toISOString().slice(0, 10);
    this.toDate = new Date().toISOString().slice(0, 10);
    this.organizationId = "";
    this.environmentClass = "";
    this.outcome = "";
    this.branchId = "";
    this.searchTerm = "";
    this.sortBy = "";
    this.sortDirection = "asc";
    this.filtersDirty = false;
    this.csvStatus = "";
    this.load(false);
  }
  handleSort(event) {
    this.sortBy = event.detail.fieldName;
    this.sortDirection = event.detail.sortDirection;
    this.sortCurrentPage();
  }
  sortCurrentPage() {
    if (!this.sortBy) return;
    const key = {
      completionLabel: "completedAt",
      durationLabel: "durationSeconds"
    }[this.sortBy] || this.sortBy;
    const multiplier = this.sortDirection === "desc" ? -1 : 1;
    this.rows = [...this.rows].sort((left, right) => {
      const a = left[key], b = right[key];
      if (a == null && b == null) return 0;
      if (a == null) return 1;
      if (b == null) return -1;
      const compared = typeof a === "number" && typeof b === "number"
        ? a - b
        : String(a).localeCompare(String(b), "pt-BR", { numeric: true, sensitivity: "base" });
      return compared * multiplier;
    });
  }
  handleAdvancedToggle(event) {
    this.advancedSection = event.detail.openSections?.[0] || "";
  }
  handleSourceToggle(event) {
    this.sourceSection = event.detail.openSections?.[0] || "";
  }
  handleCloseDetails() {
    this.selectedId = null;
  }
  handleOpenSelected() {
    if (this.selectedRow) this.openSource(this.selectedRow.id, false);
  }
  handleExport() {
    if (this.exportDisabled) return;
    const columns = [
      ["Deployment", "name"], ["ID", "id"], ["Branch", "branchName"],
      ["Organização", "organizationName"], ["Ambiente", "environmentLabel"],
      ["Resultado", "outcomeLabel"], ["Início UTC", "startLabel"],
      ["Conclusão UTC", "completionLabel"], ["Duração", "durationLabel"],
      ["Observações", "quality"]
    ];
    const lines = [
      columns.map(([title]) => csvCell(title)).join(";"),
      ...this.rows.map((row) => columns.map(([, key]) => csvCell(row[key])).join(";"))
    ];
    const blob = new Blob(["\uFEFF", lines.join("\r\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "deployments-pagina-" + this.pageNumber + ".csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    this.csvStatus = "Exportada somente a página exibida (" + this.rows.length + " registros).";
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
    this.selectedId = null;
    this.inspectedRows = 0;
    this.correlationIncomplete = false;
    const fields = [
      ...this.template.querySelectorAll("lightning-input, lightning-combobox")
    ];
    if (!fields.every((input) => input.reportValidity())) {
      this.loading = false;
      return;
    }
    try {
      if (!this.fromDate || !this.toDate || this.fromDate > this.toDate)
        throw new Error("Informe um período válido: a data inicial deve ser anterior ou igual à final.");
      const fromUtc = `${this.fromDate}T00:00:00.000Z`;
      const toUtc = new Date(
        new Date(`${this.toDate}T00:00:00.000Z`).getTime() + 86400000
      ).toISOString();
      const args = {
        fromUtc,
        toUtc,
        organizationId: this.organizationId || null,
        branchId: this.branchId.trim() || null,
        environmentClass: this.environmentClass || null,
        outcome: this.outcome || null,
        cursorCreated: next ? this.cursorCreated : null,
        cursorId: next ? this.cursorId : null
      };
      const page = this.searchTerm.trim()
        ? await listDeploymentsWithSearch({ ...args, searchTerm: this.searchTerm.trim() })
        : await listDeployments(args);
      if (version !== this.requestVersion) return;
      this.rows = (page.rows || []).map((row) => ({
        ...row,
        noBranch: !row.branchId,
        branchName: row.branchName || "—",
        organizationName: row.organizationName || "Não informada",
        environmentLabel: ENVIRONMENTS[row.environmentClass] || "Não identificado",
        outcomeLabel: RESULTS[row.outcome] || "Desconhecido",
        outcomeClass: "delivery-pill delivery-pill-" + (row.outcome || "Unknown").toLowerCase(),
        outcomeTone: row.outcome === "Success" ? "slds-text-color_success" : row.outcome === "Failed" ? "slds-text-color_error" : "slds-text-color_default",
        startLabel: formatUTC(row.startedAt),
        completionLabel: formatUTC(row.completedAt),
        durationLabel: durationLabel(row.durationSeconds)
      }));
      this.sortCurrentPage();
      this.selectedId = this.rows[0]?.id || null;
      this.filtersDirty = false;
      this.pageNumber = next ? this.pageNumber + 1 : 1;
      this.hasMore = page.hasMore;
      this.cursorCreated = page.cursorCreated;
      this.cursorId = page.cursorId;
      this.inspectedRows = page.inspectedRows;
      this.correlationIncomplete = page.correlationIncomplete;
    } catch (error) {
      if (version === this.requestVersion) {
        this.error =
          error?.body?.message || error?.message ||
          "Não foi possível consultar. Verifique o período, os filtros e suas permissões.";
        this.hasMore = false;
      }
    } finally {
      if (version === this.requestVersion) this.loading = false;
    }
  }
  handleRowAction(event) {
    const row = event.detail.row;
    const action = event.detail.action.name;
    if (action === "details") {
      this.selectedId = row.id;
      return;
    }
    this.openSource(action === "branch" ? row.branchId : row.id, action === "branch");
  }
  openSource(recordId, branch) {
    if (!recordId) return;
    this[NavigationMixin.Navigate]({
      type: "standard__recordPage",
      attributes: {
        recordId,
        objectApiName: branch ? "Flosum__Branch__c" : "Flosum__Metadata_Log__c",
        actionName: "view"
      }
    });
  }
}
