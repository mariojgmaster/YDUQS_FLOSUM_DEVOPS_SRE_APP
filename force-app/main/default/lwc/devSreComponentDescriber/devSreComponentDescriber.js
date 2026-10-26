import { LightningElement } from "lwc";
import { NavigationMixin } from "lightning/navigation";
import searchComponents from "@salesforce/apex/DevSreComponentDescriberController.searchComponents";
import describeComponent from "@salesforce/apex/DevSreComponentDescriberController.describeComponent";

export default class DevSreComponentDescriber extends NavigationMixin(LightningElement) {
  search = "";
  results = [];
  cursorName;
  cursorId;
  hasMore = false;
  loading = false;
  searched = false;
  error;
  detail;
  detailLoading = false;
  detailError;
  selectedId;
  _searchRequest = 0;
  _detailRequest = 0;
  _debounce;

  disconnectedCallback() {
    clearTimeout(this._debounce);
    ++this._searchRequest;
    ++this._detailRequest;
  }
  get tooLong() { return this.search.length > 80; }
  get eligible() { return this.search.trim().length >= 2 && !this.tooLong; }
  get hasResults() { return this.results.length > 0; }
  get hasDetail() { return Boolean(this.detail); }
  get histories() { return this.detail?.histories || []; }
  get hasHistories() { return this.histories.length > 0; }
  get historyUnavailable() { return this.detail?.historyQuality !== "TYPED_LINK_SAMPLE"; }
  get hasHistoryMore() { return Boolean(this.detail?.historiesHasMore); }
  get nextDisabled() { return !this.hasMore || this.loading || !this.eligible; }
  get entries() {
    return this.results.map(r => ({
      ...r, selected: r.id === this.selectedId,
      rowClass: r.id === this.selectedId ? "cd-row cd-row-selected" : "cd-row"
    }));
  }
  get helpText() {
    if (this.tooLong) return "A pesquisa permite até 80 caracteres.";
    if (!this.eligible) return "Informe pelo menos 2 caracteres para pesquisar.";
    return "";
  }
  get detailName() { return this.detail?.component?.name || ""; }
  get detailBranchName() { return this.detail?.component?.branchName || ""; }
  get detailBranchId() { return this.detail?.component?.branchId; }
  get noMatches() { return this.searched && !this.loading && !this.error && !this.hasResults; }

  handleChange(event) {
    this.search = event.target.value || "";
    clearTimeout(this._debounce);
    ++this._searchRequest; // Invalidate outstanding results when typing.
    ++this._detailRequest;
    this.results = [];
    this.searched = false;
    this.loading = false;
    this.hasMore = false;
    this.cursorName = undefined;
    this.cursorId = undefined;
    this.error = undefined;
    this.detail = undefined;
    this.selectedId = undefined;
    if (!this.eligible) return;
    // eslint-disable-next-line @lwc/lwc/no-async-operation
    this._debounce = setTimeout(() => this.load(false), 350);
  }
  handleRefresh() {
    clearTimeout(this._debounce);
    if (this.eligible) this.load(false);
  }
  handleNext() { if (!this.nextDisabled) this.load(true); }
  handleSelect(event) { this.loadDetail(event.currentTarget.dataset.id); }
  handleClose() {
    ++this._detailRequest;
    this.detail = undefined;
    this.selectedId = undefined;
    this.detailError = undefined;
  }
  handleOpenComponent(event) { this.open(event.currentTarget.dataset.id, "Flosum__Component__c"); }
  handleOpenBranch(event) { this.open(event.currentTarget.dataset.id, "Flosum__Branch__c"); }
  handleOpenHistory(event) { this.open(event.currentTarget.dataset.id, "Flosum__Component_History__c"); }
  open(id, objectApiName) {
    if (!id) return;
    this[NavigationMixin.Navigate]({
      type: "standard__recordPage",
      attributes: { recordId: id, objectApiName, actionName: "view" }
    });
  }
  message(error, fallback) { return error?.body?.message || fallback; }
  async load(append) {
    if (!this.eligible) return;
    const request = ++this._searchRequest;
    this.loading = true;
    this.error = undefined;
    if (!append) {
      this.results = [];
      this.hasMore = false;
      this.cursorId = undefined;
      this.cursorName = undefined;
      ++this._detailRequest;
      this.selectedId = undefined;
      this.detail = undefined;
    }
    try {
      const page = await searchComponents({
        search: this.search.trim(),
        cursorName: append ? this.cursorName : null,
        cursorId: append ? this.cursorId : null
      });
      if (request !== this._searchRequest) return;
      this.results = append ? [...this.results, ...(page.rows || [])] : page.rows || [];
      this.cursorName = page.cursorName;
      this.cursorId = page.cursorId;
      this.hasMore = Boolean(page.hasMore);
      this.searched = true;
    } catch (error) {
      if (request === this._searchRequest) {
        this.error = this.message(error, "Não foi possível pesquisar os componentes.");
        this.hasMore = false;
      }
    } finally {
      if (request === this._searchRequest) this.loading = false;
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
      const result = await describeComponent({ componentId: id });
      if (request === this._detailRequest) this.detail = result;
    } catch (error) {
      if (request === this._detailRequest)
        this.detailError = this.message(error, "Não foi possível consultar o histórico.");
    } finally {
      if (request === this._detailRequest) this.detailLoading = false;
    }
  }
}
