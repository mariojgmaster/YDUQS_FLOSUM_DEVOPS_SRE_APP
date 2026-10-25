import { LightningElement, api } from "lwc";
import { NavigationMixin } from "lightning/navigation";
import listMonitorDeployments from "@salesforce/apex/DevSreDeploymentController.listMonitorDeployments";
import getMonitorSummary from "@salesforce/apex/DevSreDeploymentController.getMonitorSummary";
import searchOrganizations from "@salesforce/apex/DevSreEnvironmentController.searchOrganizations";

const RESULTS = {
  Pending: { label: "Em andamento", tone: "running", icon: "utility:sync" },
  Success: { label: "Sucesso", tone: "success", icon: "utility:success" },
  Failed: { label: "Falha", tone: "failed", icon: "utility:error" },
  Partial: { label: "Parcial", tone: "partial", icon: "utility:warning" },
  NotRun: { label: "Não executado", tone: "neutral", icon: "utility:dash" },
  Unknown: {
    label: "Resultado desconhecido",
    tone: "neutral",
    icon: "utility:help"
  }
};
const ENVIRONMENTS = {
  PROD: "Produção",
  UAT: "Homologação · UAT",
  SIT: "Integração · SIT",
  DEV: "Desenvolvimento",
  UNKNOWN: "Ambiente não identificado",
  AMBIGUOUS: "Classificação conflitante"
};
const DAY = 86400000;
export default class DevSrePipelineOverview extends NavigationMixin(
  LightningElement
) {
  draft = {
    period: "30",
    environmentClass: "",
    outcome: "",
    organizationId: "",
    search: "",
    fromDate: "",
    toDate: ""
  };
  applied;
  rows = [];
  summary;
  error = "";
  summaryError = "";
  organizationError = "";
  exportError = "";
  organizations = [{ label: "Todas as organizações", value: "" }];
  organizationSearch = "";
  organizationsHaveMore = false;
  filtersOpen = false;
  loading = true;
  dirty = false;
  lastUpdated;
  hasMore = false;
  cursorCreated = null;
  cursorId = null;
  pageNumber = 1;
  visibleCount = 10;
  requestVersion = 0;
  filterTimer;
  organizationVersion = 0;
  downloadUrl;
  correlationIncomplete = false;

  connectedCallback() {
    this.applyFilters();
  }
  disconnectedCallback() {
    clearTimeout(this.filterTimer);
    this.requestVersion++;
    this.organizationVersion++;
    if (this.downloadUrl) URL.revokeObjectURL(this.downloadUrl);
  }
  get periodOptions() {
    return [
      { label: "Últimos 7 dias", value: "7" },
      { label: "Últimos 30 dias", value: "30" },
      { label: "Últimos 90 dias", value: "90" },
      { label: "Período personalizado", value: "custom" }
    ];
  }
  get environmentOptions() {
    return [
      { label: "Todos os ambientes", value: "" },
      ...Object.entries(ENVIRONMENTS).map(([value, label]) => ({
        value,
        label
      }))
    ];
  }
  get outcomeOptions() {
    return [
      { label: "Todos os resultados", value: "" },
      ...Object.entries(RESULTS).map(([value, item]) => ({
        value,
        label: item.label
      }))
    ];
  }
  get customPeriod() {
    return this.draft.period === "custom";
  }
  get filterLabel() {
    const count = [this.draft.outcome, this.draft.organizationId].filter(
      Boolean
    ).length;
    return count ? `Filtros (${count})` : "Filtros";
  }
  get refreshDisabled() {
    return this.loading || this.dirty;
  }
  get exportDisabled() {
    return this.loading || this.dirty || !this.rows.length;
  }
  get showRows() {
    return !this.loading && !this.dirty && !this.error && this.rows.length > 0;
  }
  get showEmpty() {
    return !this.loading && !this.dirty && !this.error && !this.rows.length;
  }
  get visibleRows() {
    return this.rows.slice(0, this.visibleCount);
  }
  get moreInPage() {
    return this.visibleCount < this.rows.length;
  }
  get nextDisabled() {
    return this.loading || this.dirty || !this.hasMore || this.moreInPage;
  }
  get emptyDescription() {
    return this.hasMore
      ? "Há mais registros de origem a examinar. Avance para continuar a consulta ou ajuste os filtros."
      : "Altere o período ou os filtros para localizar outras entregas.";
  }
  get pageLabel() {
    return `${Math.min(this.visibleCount, this.rows.length)} de ${this.rows.length} registros da página ${this.pageNumber}`;
  }
  get summaryUnavailable() {
    return this.summary && !this.summary.complete;
  }
  get summaryCards() {
    const valid = this.summary?.complete && !this.loading && !this.dirty;
    const value = (key) => (valid ? String(this.summary[key]) : "—");
    return [
      {
        key: "pending",
        label: "Em andamento",
        value: value("pending"),
        className: "metric metric-running",
        help: "Logs cujo processamento ainda não foi concluído. A fonte não distingue fila de execução."
      },
      {
        key: "queue",
        label: "Fila",
        value: "—",
        className: "metric",
        help: "A fonte integrada não informa separadamente quais entregas estão na fila."
      },
      {
        key: "success",
        label: "Sucessos no período",
        value: value("succeeded"),
        className: "metric metric-success",
        help: "Conclusão e sinalizadores de sucesso confirmados no Flosum."
      },
      {
        key: "failed",
        label: "Falhas no período",
        value: value("failed"),
        className: "metric metric-failed",
        help: "Falhas confirmadas. Resultados parciais ficam separados na lista e no contexto do resumo."
      },
      {
        key: "rate",
        label: "Taxa de sucesso",
        value:
          valid && this.summary.successRate != null
            ? `${Number(this.summary.successRate).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`
            : "—",
        className: "metric",
        help: "Sucessos divididos por sucessos + falhas + parciais. Indicador operacional de logs, sem certificação DORA."
      }
    ];
  }
  handleFilter(event) {
    const field = event.target.name;
    this.draft = {
      ...this.draft,
      [field]: event.detail?.value ?? event.target.value
    };
    this.dirty = true;
    ++this.requestVersion; // Ignore stale responses.
    this.loading = false;
    this.exportError = "";
    clearTimeout(this.filterTimer);
    if (field === "period" && this.customPeriod) return;
    if (this.customPeriod && (!this.draft.fromDate || !this.draft.toDate)) return;
    if (field === "search") {
      // Debounce free text to avoid an Apex call for every keypress.
      // eslint-disable-next-line @lwc/lwc/no-async-operation
      this.filterTimer = setTimeout(() => this.applyFilters(), 350);
    } else {
      this.applyFilters();
    }
  }
  handleOrganizationPicker(event) {
    this.handleFilter({ target: { name: "organizationId", value: event.detail.recordId || "" }, detail: { value: event.detail.recordId || "" } });
  }
  handleKey(event) {
    if (event.key === "Enter") {
      clearTimeout(this.filterTimer);
      this.applyFilters();
    }
  }
  handleToggleFilters() {
    this.filtersOpen = !this.filtersOpen;
  }
  handleOrganizationSearch(event) {
    this.organizationSearch = event.target.value || "";
  }
  async loadOrganizations() {
    const version = ++this.organizationVersion;
    this.organizationError = "";
    try {
      const page = await searchOrganizations({
        searchTerm: this.organizationSearch
      });
      if (version !== this.organizationVersion) return;
      const selected = this.organizations.filter(
        (item) =>
          item.value &&
          item.value === this.draft.organizationId &&
          !page.options.some((option) => option.value === item.value)
      );
      this.organizations = [
        { label: "Todas as organizações", value: "" },
        ...page.options,
        ...selected
      ];
      this.organizationsHaveMore = page.hasMore;
    } catch {
      if (version === this.organizationVersion)
        this.organizationError =
          "Não foi possível buscar organizações. Tente novamente.";
    }
  }
  applyFilters() {
    const fields = [...this.template.querySelectorAll("[data-filter]")];
    if (!fields.map((field) => field.reportValidity()).every(Boolean)) return;
    const today = new Date().toISOString().slice(0, 10);
    const endDate = this.customPeriod ? this.draft.toDate : today;
    const startDate = this.customPeriod
      ? this.draft.fromDate
      : new Date(
          Date.parse(`${today}T00:00:00Z`) -
            (Number(this.draft.period) - 1) * DAY
        )
          .toISOString()
          .slice(0, 10);
    if (
      !startDate ||
      !endDate ||
      startDate > endDate ||
      Date.parse(endDate) - Date.parse(startDate) >= 366 * DAY
    ) {
      this.error = "Informe um período válido de até 366 dias.";
      return;
    }
    this.applied = {
      fromUtc: `${startDate}T00:00:00.000Z`,
      toUtc: new Date(Date.parse(`${endDate}T00:00:00Z`) + DAY).toISOString(),
      endDate,
      environmentClass: this.draft.environmentClass || null,
      organizationId: this.draft.organizationId || null,
      outcome: this.draft.outcome || null,
      searchTerm: this.draft.search.trim() || null
    };
    this.dirty = false;
    this.load(false);
  }
  @api refresh() {
    if (!this.dirty) this.load(false);
  }
  async load(next) {
    const version = ++this.requestVersion;
    this.loading = true;
    this.error = "";
    this.exportError = "";
    this.summaryError = "";
    const { fromUtc, toUtc, organizationId, environmentClass, searchTerm } =
      this.applied;
    const summaryParams = {
      fromUtc,
      toUtc,
      organizationId,
      environmentClass,
      searchTerm
    };
    const params = { ...summaryParams, outcome: this.applied.outcome };
    const results = await Promise.allSettled([
      listMonitorDeployments({
        ...params,
        cursorCreated: next ? this.cursorCreated : null,
        cursorId: next ? this.cursorId : null
      }),
      next ? Promise.resolve(this.summary) : getMonitorSummary(summaryParams)
    ]);
    if (version !== this.requestVersion) return;
    const [pageResult, summaryResult] = results;
    if (summaryResult.status === "fulfilled")
      this.summary = summaryResult.value;
    else {
      this.summary = undefined;
      this.summaryError =
        "Não foi possível atualizar o resumo. A lista permanece disponível; tente Atualizar.";
    }
    if (pageResult.status === "fulfilled") {
      const page = pageResult.value;
      this.rows = (page.rows || []).map((row) => this.presentRow(row));
      this.hasMore = page.hasMore;
      this.cursorCreated = page.cursorCreated;
      this.cursorId = page.cursorId;
      this.correlationIncomplete = page.correlationIncomplete;
      this.pageNumber = next ? this.pageNumber + 1 : 1;
      this.visibleCount = 10;
      this.lastUpdated = new Date().toISOString();
    } else {
      this.rows = [];
      this.hasMore = false;
      this.error =
        pageResult.reason?.body?.message ||
        "Não foi possível consultar as entregas. Verifique o acesso e tente Atualizar.";
    }
    this.loading = false;
  }
  presentRow(row) {
    const result = RESULTS[row.outcome] || RESULTS.Unknown;
    return {
      ...row,
      title: row.branchName || row.name,
      hasBranch: Boolean(row.branchId),
      branchTitle: `Abrir Branch ${row.branchName || ""} no Flosum`,
      logTitle: `Abrir Metadata Log ${row.name} no Flosum`,
      environmentDetail: row.environmentClass === "UNKNOWN"
        ? "Nenhuma classificação válida encontrada para esta entrega"
        : row.environmentClass === "AMBIGUOUS"
          ? "Mais de uma classificação vigente nesta entrega"
          : `Classificação da entrega: ${ENVIRONMENTS[row.environmentClass] || ENVIRONMENTS.UNKNOWN}`,
      organizationDetail: `Organização Flosum: ${row.organizationName || "Não informada"}`,
      resultLabel: result.label,
      resultClass: `result result-${result.tone}`,
      environmentClassName: `environment-chip environment-${(row.environmentClass || "UNKNOWN").toLowerCase()}`,
      icon: result.icon,
      iconClass: `row-icon row-icon-${result.tone}`,
      environmentLabel:
        ENVIRONMENTS[row.environmentClass] || ENVIRONMENTS.UNKNOWN,
      organizationLabel: row.organizationName || "Organização não informada",
      durationLabel:
        row.durationSeconds == null
          ? "Duração indisponível"
          : row.durationSeconds < 60
            ? `${row.durationSeconds} s`
            : `${Math.floor(row.durationSeconds / 60)} min ${Math.round(row.durationSeconds % 60)} s`,
      clockLabel: row.completedAt
        ? "Conclusão"
        : row.startedAt
          ? "Início"
          : "Criação do log",
      clock: row.completedAt || row.startedAt || row.createdAt,
      openLabel: `Abrir ${row.branchName || row.name} no Flosum`,
      quality: row.quality || "Sem observações adicionais."
    };
  }
  handleMore() {
    this.visibleCount += 10;
  }
  handleNext() {
    if (!this.nextDisabled) this.load(true);
  }
  handleOpenBranch(event) {
    const id = event.currentTarget.dataset.id;
    if (id) this[NavigationMixin.Navigate]({
      type: "standard__recordPage",
      attributes: { recordId: id, objectApiName: "Flosum__Branch__c", actionName: "view" }
    });
  }
  handleOpen(event) {
    this[NavigationMixin.Navigate]({
      type: "standard__recordPage",
      attributes: {
        recordId: event.currentTarget.dataset.id,
        objectApiName: "Flosum__Metadata_Log__c",
        actionName: "view"
      }
    });
  }
  handleIncident() {
    this[NavigationMixin.Navigate]({
      type: "standard__navItemPage",
      attributes: { apiName: "incidentsRollbacks" }
    });
  }
  handleExport() {
    if (this.exportDisabled) return;
    const escape = (value) => {
      let text = String(value ?? "");
      if (/^[\s]*[=+@-]/.test(text)) text = `'${text}`;
      return `"${text.replace(/"/g, '""')}"`;
    };
    const headings = [
      "Deployment",
      "Branch",
      "Organização",
      "Ambiente",
      "Resultado",
      "Início UTC",
      "Conclusão UTC",
      "Duração s"
    ];
    const data = this.rows.map((row) => [
      row.name,
      row.branchName,
      row.organizationName,
      row.environmentLabel,
      row.resultLabel,
      row.startedAt,
      row.completedAt,
      row.durationSeconds
    ]);
    try {
      if (this.downloadUrl) URL.revokeObjectURL(this.downloadUrl);
      this.downloadUrl = URL.createObjectURL(
        new Blob(
          [
            "\uFEFF" +
              [headings, ...data]
                .map((row) => row.map(escape).join(";"))
                .join("\r\n")
          ],
          { type: "application/octet-stream" }
        )
      );
      const anchor = this.template.querySelector("[data-download]");
      anchor.href = this.downloadUrl;
      anchor.download = `pipeline-monitor-pagina-${this.pageNumber}.csv`;
      anchor.click();
    } catch {
      this.exportError =
        "Não foi possível exportar esta página. Tente novamente.";
    }
  }
}
