import { LightningElement } from "lwc";
import { NavigationMixin } from "lightning/navigation";
import getOverview from "@salesforce/apex/DevSreBranchMonitorController.getOverview";
import listBranches from "@salesforce/apex/DevSreBranchMonitorController.listBranches";
import getBranchDetail from "@salesforce/apex/DevSreBranchMonitorController.getBranchDetail";

const TAB_NAMES = ["overview", "branches", "compare", "components"];
const TABS = [
  { value: "overview", label: "Visão geral" },
  { value: "branches", label: "Branches" },
  { value: "compare", label: "Comparar" },
  { value: "components", label: "Componentes" }
];

export default class DevSreBranchMonitor extends NavigationMixin(LightningElement) {
  tabs = TABS;
  activeTab = "overview";
  period = "30";
  summary;
  summaryLoading = false;
  summaryError;
  branches = [];
  branchSearch = "";
  branchCursorName;
  branchCursorId;
  branchHasMore = false;
  branchesLoading = false;
  branchError;
  detail;
  detailLoading = false;
  detailError;
  selectedId;
  _summaryRequest = 0;
  _branchRequest = 0;
  _detailRequest = 0;
  _searchTimer;

  connectedCallback() {
    this.loadSummary();
  }
  disconnectedCallback() {
    clearTimeout(this._searchTimer);
    ++this._summaryRequest;
    ++this._branchRequest;
    ++this._detailRequest;
  }
  get isOverview() { return this.activeTab === "overview"; }
  get isBranches() { return this.activeTab === "branches"; }
  get isCompare() { return this.activeTab === "compare"; }
  get isComponents() { return this.activeTab === "components"; }
  get sectionLabel() { return TABS.find(t => t.value === this.activeTab)?.label || "Visão geral"; }
  get sectionId() { return "bm-panel-" + this.activeTab; }
  get tabItems() {
    return this.tabs.map(t => ({
      ...t,
      className: t.value === this.activeTab ? "bm-tab bm-tab_active" : "bm-tab",
      selected: t.value === this.activeTab,
      tabIndex: t.value === this.activeTab ? "0" : "-1"
    }));
  }
  get periodOptions() {
    return [
      { label: "Últimos 7 dias", value: "7" },
      { label: "Últimos 30 dias", value: "30" },
      { label: "Últimos 90 dias", value: "90" }
    ];
  }
  get hasSummary() { return Boolean(this.summary); }
  get summaryComplete() { return Boolean(this.summary?.complete); }
  get summaryIncomplete() { return this.hasSummary && !this.summaryComplete; }
  get cards() {
    if (!this.summaryComplete) return [];
    return [
      { id: "branches", label: "Branches com atividade no período", value: this.summary.activeBranches },
      { id: "deployments", label: "Operações de deployment", value: this.summary.deployments },
      { id: "validations", label: "Operações de validação", value: this.summary.validations },
      { id: "succeeded", label: "Logs com sucesso", value: this.summary.succeeded },
      { id: "failed", label: "Logs com falha", value: this.summary.failed }
    ];
  }
  get recentLogs() { return this.summary?.recent || []; }
  get hasRecentLogs() { return this.recentLogs.length > 0; }
  get hasBranches() { return this.branches.length > 0; }
  get hasDetail() { return Boolean(this.detail); }
  get selectedLogs() { return this.detail?.recent || []; }
  get hasSelectedLogs() { return this.selectedLogs.length > 0; }
  get selectedRows() {
    return this.branches.map(row => ({
      ...row,
      rowClass: row.id === this.selectedId ? "bm-branch-row bm-branch-row_selected" : "bm-branch-row"
    }));
  }
  get searchTooLong() { return this.branchSearch.length > 80; }
  get disableNext() { return this.branchesLoading || !this.branchHasMore; }

  handleTabClick(event) { this.goTab(event.currentTarget.dataset.tab); }
  goTab(next) {
    if (!TAB_NAMES.includes(next)) return;
    this.activeTab = next;
    if (next === "branches" && !this._branchesLoaded) this.loadBranches(false);
  }
  handleTabKey(event) {
    const current = TAB_NAMES.indexOf(event.currentTarget.dataset.tab);
    let next = current;
    if (event.key === "ArrowRight") next = (current + 1) % TAB_NAMES.length;
    else if (event.key === "ArrowLeft") next = (current - 1 + TAB_NAMES.length) % TAB_NAMES.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = TAB_NAMES.length - 1;
    else return;
    event.preventDefault();
    this.goTab(TAB_NAMES[next]);
    this.template.querySelector('[data-tab="' + TAB_NAMES[next] + '"]')?.focus();
  }
  handlePeriod(event) { this.period = event.detail.value; this.loadSummary(); }
  handleRefreshSummary() { this.loadSummary(); }
  handleRefreshBranches() { this.loadBranches(false); }
  handleSearch(event) {
    this.branchSearch = event.target.value || "";
    clearTimeout(this._searchTimer);
    ++this._branchRequest; // Invalidate in-flight requests immediately.
    this.branches = [];
    this.branchHasMore = false;
    this.branchError = undefined;
    this._branchesLoaded = false;
    this.selectedId = undefined;
    this.detail = undefined;
    ++this._detailRequest;
    if (this.searchTooLong) { this.branchesLoading = false; return; }
    // eslint-disable-next-line @lwc/lwc/no-async-operation
    this._searchTimer = setTimeout(() => this.loadBranches(false), 350);
  }
  handleNext() { if (!this.disableNext) this.loadBranches(true); }
  handleSelectBranch(event) { this.loadDetail(event.currentTarget.dataset.id); }
  handleCloseDetail() { this.selectedId = undefined; this.detail = undefined; ++this._detailRequest; }
  handleOpenBranch(event) { this.openRecord(event.currentTarget.dataset.id, "Flosum__Branch__c"); }
  handleOpenLog(event) { this.openRecord(event.currentTarget.dataset.id, "Flosum__Metadata_Log__c"); }
  openRecord(id, objectApiName) {
    if (!id) return;
    this[NavigationMixin.Navigate]({
      type: "standard__recordPage", attributes: { recordId: id, objectApiName, actionName: "view" }
    });
  }
  normalize(error, fallback) { return error?.body?.message || fallback; }
  async loadSummary() {
    const request = ++this._summaryRequest;
    this.summaryLoading = true;
    this.summaryError = undefined;
    try {
      const result = await getOverview({ days: Number(this.period) });
      if (request !== this._summaryRequest) return;
      this.summary = result;
    } catch (error) {
      if (request === this._summaryRequest) {
        this.summary = undefined;
        this.summaryError = this.normalize(error, "Não foi possível consultar atividades Flosum.");
      }
    } finally {
      if (request === this._summaryRequest) this.summaryLoading = false;
    }
  }
  async loadBranches(append) {
    const request = ++this._branchRequest;
    this._branchesLoaded = true;
    this.branchesLoading = true;
    this.branchError = undefined;
    if (!append) {
      this.branches = [];
      this.branchCursorName = undefined;
      this.branchCursorId = undefined;
      this.branchHasMore = false;
      this.detail = undefined;
      this.selectedId = undefined;
      ++this._detailRequest;
    }
    try {
      const page = await listBranches({
        search: this.branchSearch.trim() || null,
        cursorName: append ? this.branchCursorName : null,
        cursorId: append ? this.branchCursorId : null
      });
      if (request !== this._branchRequest) return;
      this.branches = append ? [...this.branches, ...(page.rows || [])] : (page.rows || []);
      this.branchHasMore = Boolean(page.hasMore);
      this.branchCursorName = page.cursorName;
      this.branchCursorId = page.cursorId;
    } catch (error) {
      if (request === this._branchRequest) {
        this.branchError = this.normalize(error, "Não foi possível consultar as Branches.");
        this.branchHasMore = false;
      }
    } finally {
      if (request === this._branchRequest) this.branchesLoading = false;
    }
  }
  async loadDetail(id) {
    if (!id) return;
    const request = ++this._detailRequest;
    this.selectedId = id;
    this.detail = undefined;
    this.detailError = undefined;
    this.detailLoading = true;
    try {
      const result = await getBranchDetail({ branchId: id });
      if (request === this._detailRequest) this.detail = result;
    } catch (error) {
      if (request === this._detailRequest) this.detailError = this.normalize(error, "Falha ao carregar a Branch.");
    } finally {
      if (request === this._detailRequest) this.detailLoading = false;
    }
  }
}