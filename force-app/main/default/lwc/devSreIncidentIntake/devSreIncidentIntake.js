import { LightningElement } from "lwc";
import { NavigationMixin } from "lightning/navigation";
import { ShowToastEvent } from "lightning/platformShowToastEvent";
import listIncidents from "@salesforce/apex/DevSreIncidentController.listIncidents";
import canReviewIncidents from "@salesforce/customPermission/DevSre_ReviewIncidentCausality";
import listRecoveryActions from "@salesforce/apex/DevSreIncidentController.listRecoveryActions";

const INCIDENT_COLUMNS = [
  { label: "Número", fieldName: "recordNumber", type: "text", initialWidth: 130 },
  { label: "Incidente", fieldName: "title", type: "text" },
  { label: "Serviço", fieldName: "serviceKey", type: "text" },
  { label: "Severidade", fieldName: "severity", type: "text", initialWidth: 115 },
  { label: "Status", fieldName: "status", type: "text", initialWidth: 125 },
  {
    type: "action",
    typeAttributes: {
      rowActions: [
        { label: "Ver ações", name: "view_actions" },
        { label: "Abrir registro", name: "open_record" }
      ]
    }
  }
];

const RECOVERY_COLUMNS = [
  { label: "Número", fieldName: "recordNumber", type: "text" },
  { label: "Tipo", fieldName: "actionType", type: "text" },
  { label: "Situação", fieldName: "status", type: "text" },
  {
    label: "Início",
    fieldName: "startedAt",
    type: "date",
    typeAttributes: { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }
  },
  {
    label: "Conclusão",
    fieldName: "completedAt",
    type: "date",
    typeAttributes: { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }
  }
];

export default class DevSreIncidentIntake extends NavigationMixin(LightningElement) {
  incidentColumns = INCIDENT_COLUMNS;
  recoveryColumns = RECOVERY_COLUMNS;
  incidents = [];
  actions = [];
  searchTerm = "";
  appliedSearch = "";
  selectedId;
  selectedNumber;
  isLoading = false;
  isLoadingActions = false;
  isIncidentFormOpen = false;
  isActionFormOpen = false;
  isReviewFormOpen = false;
  incidentsHasMore = false;
  actionsHasMore = false;
  errorMessage;
  actionsError;
  _incidentsRequest = 0;
  _actionsRequest = 0;

  connectedCallback() {
    this.loadIncidents();
  }

  get hasIncidents() { return this.incidents.length > 0; }
  get hasActions() { return this.actions.length > 0; }
  get hasSelected() { return Boolean(this.selectedId); }
  get canReview() { return Boolean(canReviewIncidents); }
  get searchDisabled() { return this.isLoading || this.searchTerm.trim().length > 80; }
  get listDescription() { return `${this.incidents.length} incidente(s) exibido(s)`; }

  handleSearchChange(event) { this.searchTerm = event.target.value || ""; }
  handleSearch() {
    if (!this.searchDisabled) {
      this.appliedSearch = this.searchTerm.trim();
      this.loadIncidents();
    }
  }
  handleRefresh() { this.loadIncidents(); }
  toggleIncidentForm() { this.isIncidentFormOpen = !this.isIncidentFormOpen; }
  toggleActionForm() {
    if (this.selectedId) this.isActionFormOpen = !this.isActionFormOpen;
  }
  toggleReviewForm() {
    if (this.canReview && this.selectedId) this.isReviewFormOpen = !this.isReviewFormOpen;
  }
  handleReviewSaved() {
    this.isReviewFormOpen = false;
    this.dispatchEvent(new ShowToastEvent({ title: "Revisão registrada", message: "A conclusão foi salva. As métricas DORA continuam indisponíveis até certificação das fontes.", variant: "success" }));
    this.loadIncidents();
  }

  async loadIncidents() {
    const request = ++this._incidentsRequest;
    ++this._actionsRequest;
    this.isLoading = true;
    this.isLoadingActions = false;
    this.errorMessage = undefined;
    this.actionsError = undefined;
    this.incidents = [];
    this.actions = [];
    this.incidentsHasMore = false;
    this.actionsHasMore = false;
    this.selectedId = undefined;
    this.selectedNumber = undefined;
    this.isActionFormOpen = false;
    this.isReviewFormOpen = false;
    try {
      const response = await listIncidents({ searchTerm: this.appliedSearch });
      if (request !== this._incidentsRequest) return;
      this.incidents = Array.isArray(response?.incidents) ? response.incidents : [];
      this.incidentsHasMore = Boolean(response?.hasMore);
    } catch (error) {
      if (request === this._incidentsRequest)
        this.errorMessage = this.formatError(error, "Não foi possível consultar incidentes.");
    } finally {
      if (request === this._incidentsRequest) this.isLoading = false;
    }
  }

  handleIncidentAction(event) {
    const { row, action } = event.detail;
    if (action?.name === "open_record") this.navigateTo("DevSre_Incident__c", row.id);
    if (action?.name === "view_actions") this.loadActions(row);
  }

  async loadActions(row) {
    const request = ++this._actionsRequest;
    this.selectedId = row.id;
    this.selectedNumber = row.recordNumber;
    this.isLoadingActions = true;
    this.actionsError = undefined;
    this.actions = [];
    this.actionsHasMore = false;
    this.isActionFormOpen = false;
    this.isReviewFormOpen = false;
    try {
      const response = await listRecoveryActions({ incidentId: row.id });
      if (request !== this._actionsRequest) return;
      this.actions = Array.isArray(response?.actions) ? response.actions : [];
      this.actionsHasMore = Boolean(response?.hasMore);
    } catch (error) {
      if (request === this._actionsRequest)
        this.actionsError = this.formatError(error, "Não foi possível consultar ações.");
    } finally {
      if (request === this._actionsRequest) this.isLoadingActions = false;
    }
  }

  handleIncidentCreated() {
    this.isIncidentFormOpen = false;
    this.dispatchEvent(new ShowToastEvent({
      title: "Incidente registrado",
      message: "Registro criado; causalidade permanece pendente de revisão.",
      variant: "success"
    }));
    this.loadIncidents();
  }

  handleActionCreated() {
    this.isActionFormOpen = false;
    this.isReviewFormOpen = false;
    this.dispatchEvent(new ShowToastEvent({
      title: "Ação registrada",
      message: "A ação foi documentada e não dispara operações no Flosum.",
      variant: "success"
    }));
    if (this.selectedId) {
      this.loadActions({ id: this.selectedId, number: this.selectedNumber });
    }
  }

  handleOpenSelected() {
    if (this.selectedId) this.navigateTo("DevSre_Incident__c", this.selectedId);
  }

  navigateTo(objectApiName, id) {
    this[NavigationMixin.Navigate]({
      type: "standard__recordPage",
      attributes: { recordId: id, objectApiName, actionName: "view" }
    });
  }

  formatError(error, fallback) { return error?.body?.message || fallback; }
}
