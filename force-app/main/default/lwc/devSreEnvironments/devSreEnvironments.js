import { LightningElement } from "lwc";
import { NavigationMixin } from "lightning/navigation";
import searchOrganizations from "@salesforce/apex/DevSreEnvironmentController.searchOrganizations";
import listMappings from "@salesforce/apex/DevSreEnvironmentController.listMappings";
import saveMapping from "@salesforce/apex/DevSreEnvironmentController.saveMapping";

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
  columns = [
    { label: "Organização", fieldName: "organizationName" },
    { label: "Ambiente", fieldName: "environmentClass" },
    {
      label: "Desde (UTC)",
      fieldName: "validFrom",
      type: "date",
      typeAttributes: DATE
    },
    {
      label: "Até (UTC, exclusivo)",
      fieldName: "validTo",
      type: "date",
      typeAttributes: DATE
    },
    { label: "Justificativa", fieldName: "reason", wrapText: true },
    {
      type: "action",
      typeAttributes: { rowActions: this.rowActions.bind(this) }
    }
  ];
  get hasRows() {
    return this.rows.length > 0;
  }
  get editing() {
    return Boolean(this.mappingId);
  }
  get busy() {
    return this.loading || this.saving;
  }
  get environmentOptions() {
    return ["PROD", "UAT", "SIT", "DEV"].map((value) => ({
      label: value,
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
    return this.editing
      ? "Encerrar vigência / atualizar justificativa"
      : "Nova classificação de ambiente";
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
    const actions = [{ label: "Abrir registro / histórico", name: "open" }];
    if (this.canManage)
      actions.push({ label: "Encerrar / justificar", name: "edit" });
    done(actions);
  }
  handleChange(event) {
    this[event.target.name] = event.detail?.value ?? event.target.value;
  }
  async loadOrganizations() {
    const version = ++this.organizationVersion;
    try {
      const page = await searchOrganizations({
        searchTerm: this.organizationSearch
      });
      if (version !== this.organizationVersion) return;
      this.organizations = page.options;
      this.organizationsHaveMore = page.hasMore;
      this.canManage = page.canManage;
    } catch {
      if (version === this.organizationVersion)
        this.error =
          "Não foi possível consultar organizações com seu acesso atual.";
    }
  }
  handleSearchOrganizations() {
    this.loadOrganizations();
  }
  handleRefresh() {
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
      if (version === this.requestVersion) this.rows = rows;
    } catch (error) {
      if (version === this.requestVersion)
        this.error =
          error?.body?.message || "Não foi possível consultar as vigências.";
    } finally {
      if (version === this.requestVersion) this.loading = false;
    }
  }
  handleNew() {
    this.mappingId = null;
    this.organizationId = "";
    this.environmentClass = "";
    this.validFrom = "";
    this.validTo = "";
    this.reason = "";
  }
  handleRowAction(event) {
    const row = event.detail.row;
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
    if (this.saving || !this.canManage) return;
    const inputs = [...this.template.querySelectorAll("[data-form]")];
    if (!inputs.every((input) => input.reportValidity())) return;
    this.saving = true;
    this.error = "";
    this.notice = "";
    try {
      await saveMapping({
        mappingId: this.mappingId,
        organizationId: this.organizationId,
        environmentClass: this.environmentClass,
        validFrom: this.validFrom
          ? new Date(this.validFrom).toISOString()
          : null,
        validTo: this.validTo ? new Date(this.validTo).toISOString() : null,
        reason: this.reason
      });
      this.notice =
        "Vigência salva. Atualize a consulta de deployments para aplicar a configuração.";
      this.handleNew();
      await this.loadMappings();
      this.dispatchEvent(new CustomEvent("mappingchange"));
    } catch (error) {
      this.error =
        error?.body?.message ||
        "Não foi possível salvar. Verifique o período, a sobreposição e suas permissões.";
    } finally {
      this.saving = false;
    }
  }
}
