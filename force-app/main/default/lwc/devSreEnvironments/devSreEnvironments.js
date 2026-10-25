import { LightningElement } from "lwc";
import { NavigationMixin } from "lightning/navigation";
import searchOrganizations from "@salesforce/apex/DevSreEnvironmentController.searchOrganizations";
import listMappings from "@salesforce/apex/DevSreEnvironmentController.listMappings";
import saveMapping from "@salesforce/apex/DevSreEnvironmentController.saveMapping";

const ENVIRONMENTS = {
  PROD: "PROD · Produção",
  UAT: "UAT · Homologação",
  SIT: "SIT · Integração",
  DEV: "DEV · Desenvolvimento"
};
const DATE = {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "UTC"
};
export default class DevSreEnvironments extends NavigationMixin(
  LightningElement
) {
  rows = [];
  view = "current";
  organizationQuery = "";
  asOf = Date.now();
  showForm = false;
  hasEnd = false;
  originalEnd = "";
  formError = "";
  pendingFocus = "";
  organizationsLoading = false;
  organizationError = "";
  capabilitiesKnown = false;
  organizations = [];
  organizationSearch = "";
  organizationFilter = "";
  organizationsHaveMore = false;
  canManage = false;
  loading = false;
  saving = false;
  error = "";
  notice = "";
  mappingId = null;
  organizationId = "";
  environmentClass = "";
  validFrom = "";
  validTo = "";
  reason = "";
  requestVersion = 0;
  organizationVersion = 0;
  get columns() {
    const base = [
      { label: "Organização Flosum", fieldName: "organizationName" },
      { label: "Uso nas análises", fieldName: "environmentLabel" },
      { label: "Vale desde (UTC)", fieldName: "validFrom", type: "date", typeAttributes: DATE },
      { label: "Situação", fieldName: "stateLabel" }
    ];
    if (this.isHistory) base.push({ label: "Vale até (UTC)", fieldName: "validTo", type: "date", typeAttributes: DATE });
    if (this.canManage) base.push({
      label: "Atualizar",
      type: "button",
      typeAttributes: { label: "Atualizar", name: "edit", variant: "neutral" }
    });
    base.push({
      label: "Histórico", type: "button",
      typeAttributes: { label: "Histórico", name: "history", variant: "base" }
    });
    base.push({ type: "action", typeAttributes: { rowActions: this.rowActions.bind(this) } });
    return base;
  }
  get isHistory() {
    return this.view !== "current";
  }
  get currentVariant() {
    return this.isHistory ? "neutral" : "brand-outline";
  }
  get historyVariant() {
    return this.isHistory ? "brand-outline" : "neutral";
  }
  get historyOptions() {
    return [
      { label: "Histórico encerrado", value: "ended" },
      { label: "Classificações futuras", value: "scheduled" },
      { label: "Todas as classificações", value: "all" }
    ];
  }
  get layoutClass() {
    return this.showEditor ? "environment-layout environment-layout-open" : "environment-layout";
  }
  get visibleRows() {
    return this.rows
      .map((row) => {
        const state =
          new Date(row.validFrom).getTime() > this.asOf
            ? "scheduled"
            : row.validTo && new Date(row.validTo).getTime() <= this.asOf
              ? "ended"
              : "current";
        return {
          ...row,
          state,
          environmentLabel:
            ENVIRONMENTS[row.environmentClass] || row.environmentClass,
          stateLabel: {
            current: "Atual",
            scheduled: "Futura",
            ended: "Encerrada"
          }[state]
        };
      })
      .filter((row) => (this.view === "all" || row.state === this.view) &&
        (!this.organizationQuery.trim() || (row.organizationName || "").toLocaleLowerCase("pt-BR").includes(this.organizationQuery.trim().toLocaleLowerCase("pt-BR"))));
  }
  get hasVisibleRows() {
    return this.visibleRows.length > 0;
  }
  get showEmpty() {
    return !this.error;
  }
  get readOnly() {
    return this.capabilitiesKnown && !this.canManage;
  }
  get showEditor() {
    return this.canManage && this.showForm;
  }
  get identityDisabled() {
    return this.editing || this.saving;
  }
  get endToggleDisabled() {
    return this.saving || Boolean(this.originalEnd);
  }
  get statusLabel() {
    return `${this.visibleRows.length} classificações nesta consulta. Sem data final, a classificação continua valendo.`;
  }
  get emptyTitle() {
    return this.rows.length
      ? "Nenhuma classificação nesta visão"
      : "Nenhuma classificação cadastrada nesta consulta";
  }
  get emptyDescription() {
    return this.rows.length
      ? "Altere a visão para consultar classificações atuais, futuras ou encerradas."
      : this.canManage
        ? "Use Classificar organização para definir o ambiente e desde quando ele é válido."
        : "Solicite a classificação das organizações ao responsável pelos ambientes.";
  }
  get viewOptions() {
    return [
      { label: "Classificações atuais", value: "current" },
      { label: "Classificações futuras", value: "scheduled" },
      { label: "Histórico encerrado", value: "ended" },
      { label: "Todas as classificações", value: "all" }
    ];
  }
  get editing() {
    return Boolean(this.mappingId);
  }
  get busy() {
    return this.loading || this.saving || this.organizationsLoading;
  }
  get environmentOptions() {
    return Object.keys(ENVIRONMENTS).map((value) => ({
      label: ENVIRONMENTS[value],
      value
    }));
  }
  get filterOptions() {
    return [
      { label: "Todas as organizações", value: "" },
      ...this.organizations
    ];
  }
  get formTitle() {
    return this.editing ? "Atualizar classificação" : "Classificar organização";
  }
  get formHelp() {
    return this.editing
      ? "Você pode encerrar esta classificação ou atualizar o motivo. Para mudar o uso da organização, encerre a atual e cadastre a nova com a mesma data de troca. Um período já encerrado não pode ser reaberto ou ampliado."
      : "Escolha a organização, seu uso e desde quando ele é válido. Defina uma data final apenas se esse uso tiver término previsto.";
  }
  renderedCallback() {
    if (!this.pendingFocus) return;
    const target = this.template.querySelector(this.pendingFocus);
    if (target) {
      this.pendingFocus = "";
      target.focus();
    }
  }
  connectedCallback() {
    this.loadOrganizations();
    this.loadMappings();
  }
  disconnectedCallback() {
    this.requestVersion++;
    this.organizationVersion++;
  }
  rowActions(row, done) {
    const actions = [{ label: "Abrir registro e auditoria", name: "open" }];
    if (this.canManage)
      actions.push({ label: "Atualizar classificação", name: "edit" });
    done(actions);
  }
  handleChange(event) {
    const name = event.target.name;
    this[name] =
      name === "hasEnd"
        ? event.target.checked
        : (event.detail?.value ?? event.target.value);
    if (name === "hasEnd" && !this.hasEnd) this.validTo = "";
    if (name === "organizationFilter") this.loadMappings();
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
      // Retain selected values when a narrower search replaces the result options.
      const selected = new Set([this.organizationId, this.organizationFilter]);
      this.organizations = [
        ...page.options,
        ...this.organizations.filter(
          (item) =>
            selected.has(item.value) &&
            !page.options.some((option) => option.value === item.value)
        )
      ];
      this.organizationsHaveMore = page.hasMore;
      this.canManage = page.canManage;
      this.capabilitiesKnown = true;
    } catch {
      if (version === this.organizationVersion)
        this.organizationError =
          "Não foi possível consultar organizações com seu acesso atual. Use Buscar organizações para tentar novamente.";
    } finally {
      if (version === this.organizationVersion)
        this.organizationsLoading = false;
    }
  }
  handleSearchOrganizations() {
    this.loadOrganizations();
  }
  handleRefresh() {
    this.loadMappings();
  }
  handleCurrent() {
    this.view = "current";
    this.organizationFilter = "";
    this.organizationQuery = "";
    this.loadMappings();
  }
  handleHistory() {
    this.view = "ended";
    this.organizationFilter = "";
    this.organizationQuery = "";
    this.loadMappings();
  }
  handleClearHistoryFilter() {
    this.organizationFilter = "";
    this.organizationQuery = "";
    this.loadMappings();
  }
  async loadMappings() {
    const version = ++this.requestVersion;
    this.loading = true;
    this.error = "";
    this.rows = [];
    try {
      const rows = await listMappings({
        organizationId: this.organizationFilter || null
      });
      if (version === this.requestVersion) {
        this.rows = rows;
        this.asOf = Date.now();
      }
    } catch (error) {
      if (version === this.requestVersion)
        this.error =
          error?.body?.message ||
          "Não foi possível consultar as classificações. Use Atualizar lista para tentar novamente.";
    } finally {
      if (version === this.requestVersion) this.loading = false;
    }
  }
  handleNew() {
    this.showForm = true;
    this.notice = "";
    this.formError = "";
    this.pendingFocus = "[data-focus]";
    this.hasEnd = false;
    this.originalEnd = "";
    this.mappingId = null;
    this.organizationId = "";
    this.environmentClass = "";
    this.validFrom = "";
    this.validTo = "";
    this.reason = "";
  }
  handleCancel() {
    this.showForm = false;
    this.formError = "";
    this.pendingFocus = "[data-create]";
  }
  handleRowAction(event) {
    const row = event.detail.row;
    if (event.detail.action.name === "history") {
      this.view = "all";
      this.organizationFilter = row.organizationId;
      this.organizationQuery = "";
      this.showForm = false;
      if (!this.organizations.some((item) => item.value === row.organizationId)) {
        this.organizations = [
          ...this.organizations,
          { value: row.organizationId, label: row.organizationName }
        ];
      }
      this.loadMappings();
      return;
    }
    if (event.detail.action.name === "open") {
      this[NavigationMixin.Navigate]({
        type: "standard__recordPage",
        attributes: {
          recordId: row.id,
          objectApiName: "DevSre_EnvironmentMapping__c",
          actionName: "view"
        }
      });
      return;
    }
    if (!this.canManage) return;
    this.showForm = true;
    this.formError = "";
    this.pendingFocus = "[data-reason-focus]";
    this.hasEnd = Boolean(row.validTo);
    this.originalEnd = row.validTo || "";
    this.mappingId = row.id;
    this.organizationId = row.organizationId;
    this.environmentClass = row.environmentClass;
    this.validFrom = row.validFrom;
    this.validTo = row.validTo || "";
    this.reason = row.reason;
    if (!this.organizations.some((item) => item.value === row.organizationId)) {
      this.organizations = [
        ...this.organizations,
        { value: row.organizationId, label: row.organizationName }
      ];
    }
  }
  async handleSave() {
    if (this.busy || !this.canManage) return;
    const inputs = [...this.template.querySelectorAll("[data-form]")];
    if (!inputs.map((input) => input.reportValidity()).every(Boolean)) return;
    this.saving = true;
    this.formError = "";
    this.notice = "";
    try {
      await saveMapping({
        mappingId: this.mappingId,
        organizationId: this.organizationId,
        environmentClass: this.environmentClass,
        validFrom: this.validFrom
          ? new Date(this.validFrom).toISOString()
          : null,
        validTo:
          this.hasEnd && this.validTo
            ? new Date(this.validTo).toISOString()
            : null,
        reason: this.reason
      });
      this.notice =
        "Classificação salva. A consulta de deployments será atualizada com essa configuração.";
      this.showForm = false;
      this.view = "all";
      // Make a newly created mapping visible even when another organization was filtered.
      this.organizationFilter = this.organizationId;
      this.pendingFocus = "[data-create]";
      await this.loadMappings();
      this.dispatchEvent(new CustomEvent("mappingchange"));
    } catch (error) {
      this.formError =
        error?.body?.message ||
        "Não foi possível salvar. Verifique as datas e suas permissões. Cada organização deve ter apenas uma classificação por período.";
    } finally {
      this.saving = false;
    }
  }
}
