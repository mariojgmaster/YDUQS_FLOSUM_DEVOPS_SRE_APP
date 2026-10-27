import { LightningElement } from "lwc";
import { NavigationMixin } from "lightning/navigation";
import searchFilteredComponents from "@salesforce/apex/DevSreComponentDescriberController.searchFilteredComponents";
import getComponentTypes from "@salesforce/apex/DevSreComponentDescriberController.getComponentTypes";
import describeComponent from "@salesforce/apex/DevSreComponentDescriberController.describeComponent";
import inspectHistoryArchive from "@salesforce/apex/DevSreComponentDescriberController.inspectHistoryArchive";

export default class DevSreComponentDescriber extends NavigationMixin(LightningElement) {
  search = "";
  typeText = "";
  typeValue = null;
  typeOptions = [];
  typeMenuOpen = false;
  typeLoading = false;
  typeError;
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
  _typeRequest = 0;
  archiveOpen = false;
  archiveFilter = "";
  detailExpanded = false;
  archiveLoading = false;
  archiveError;
  archiveData;
  archiveHistoryId;
  _archiveRequest = 0;
  _debounce;
  _typeDebounce;

  connectedCallback() { this.load(false); }
  disconnectedCallback() {
    clearTimeout(this._debounce);
    clearTimeout(this._typeDebounce);
    ++this._searchRequest;
    ++this._detailRequest;
    ++this._typeRequest;
    ++this._archiveRequest;
  }

  get tooLong() { return this.search.length > 80; }
  get eligible() {
    const length = this.search.trim().length;
    return !this.tooLong && (length === 0 || length >= 2);
  }
  get hasResults() { return this.results.length > 0; }
  get hasDetail() { return Boolean(this.detail); }
  get histories() { return this.detail?.histories || []; }
  get historyRows() {
    return this.histories.map((row, index) => ({
      ...row,
      sequence: index + 1,
      rowClass: this.archiveOpen && this.archiveHistoryId === row.id ?
        "cd-history cd-history_selected" : "cd-history"
    }));
  }
  get historyCountLabel() {
    const count = this.histories.length;
    return count === 1 ? "1 histórico nesta consulta" : `${count} históricos nesta consulta`;
  }
  get hasHistories() { return this.histories.length > 0; }
  get historyUnavailable() { return this.detail?.historyQuality !== "TYPED_LINK_SAMPLE"; }
  get hasHistoryMore() { return Boolean(this.detail?.historiesHasMore); }
  get nextDisabled() { return !this.hasMore || this.loading || !this.eligible; }
  get hasTypeOptions() { return this.typeOptions.length > 0; }
  get isTypeSelected() { return Boolean(this.typeValue); }
  get emptyWithoutFilters() { return !this.search.trim() && !this.typeValue; }
  get showResults() { return !this.detailExpanded; }
  get layoutClass() { return this.detailExpanded ? "cd-layout cd-layout_focus" : "cd-layout"; }
  get hasArchiveEntries() { return (this.archiveData?.entries || []).length > 0; }
  get archiveEntries() {
    const term = this.archiveFilter.trim().toLocaleLowerCase();
    return (this.archiveData?.entries || []).filter(x =>
      !term || (x.path || "").toLocaleLowerCase().includes(term)
    ).map(x => ({
      ...x,
      disabled: !x.previewable,
      rowClass: x.path === this.archiveData?.selectedPath ?
        "cd-archive-item cd-archive-item_selected" : "cd-archive-item"
    }));
  }
  get hasMatchingArchiveEntries() { return this.archiveEntries.length > 0; }
  get archiveMatchCount() { return this.archiveEntries.length; }
  get archiveTotalCount() { return (this.archiveData?.entries || []).length; }
  get hasArchiveText() { return this.archiveData?.text !== null && this.archiveData?.text !== undefined; }
  get archiveContent() { return this.archiveData?.text || ""; }
  get archiveFileName() { return this.archiveData?.selectedPath || ""; }
  get archiveName() { return this.archiveData?.attachmentName || "Arquivo Flosum"; }
  get entries() {
    return this.results.map(r => ({
      ...r,
      rowClass: r.id === this.selectedId ? "cd-row cd-row-selected" : "cd-row",
      typeLabel: r.componentType || "—",
      displayName: r.componentName || "Nome não informado",
      displaySource: r.source || "—",
      displayVersion: r.version || "—"
    }));
  }
  get helpText() {
    if (this.tooLong) return "A pesquisa permite até 80 caracteres.";
    if (!this.eligible) return "Informe pelo menos 2 caracteres ou deixe o nome vazio.";
    return "";
  }
  get detailName() { return this.detail?.component?.componentName || "Nome não informado"; }
  get detailNumber() { return this.detail?.component?.name || ""; }
  get detailSource() { return this.detail?.component?.source || "Não informado"; }
  get detailSourceDetails() { return this.detail?.component?.sourceDetails || "Não informado"; }
  get detailVersion() { return this.detail?.component?.version || "Não informada"; }
  get detailChangedOn() { return this.detail?.component?.changedOn || null; }
  get detailCommittedOn() { return this.detail?.component?.committedOn || null; }
  get detailBranchName() { return this.detail?.component?.branchName || ""; }
  get detailBranchId() { return this.detail?.component?.branchId; }
  get detailType() { return this.detail?.component?.componentType || "Não informado"; }
  get noMatches() { return this.searched && !this.loading && !this.error && !this.hasResults; }

  resetResults() {
    this.handleArchiveClose();
    this.detailExpanded = false;
    ++this._searchRequest;
    ++this._detailRequest;
    this.results = [];
    this.loading = false;
    this.searched = false;
    this.hasMore = false;
    this.cursorName = undefined;
    this.cursorId = undefined;
    this.error = undefined;
    this.detail = undefined;
    this.detailError = undefined;
    this.selectedId = undefined;
  }
  handleChange(event) {
    this.search = event.target.value || "";
    clearTimeout(this._debounce);
    this.resetResults();
    if (!this.eligible) return;
    // eslint-disable-next-line @lwc/lwc/no-async-operation
    this._debounce = setTimeout(() => this.load(false), 350);
  }
  handleRefresh() {
    clearTimeout(this._debounce);
    this.typeMenuOpen = false;
    if (this.eligible) this.load(false);
  }
  handleReset() {
    clearTimeout(this._debounce);
    clearTimeout(this._typeDebounce);
    ++this._typeRequest;
    this.search = "";
    this.typeText = "";
    this.typeValue = null;
    this.typeOptions = [];
    this.typeError = undefined;
    this.typeMenuOpen = false;
    this.load(false);
  }
  handleNext() { if (!this.nextDisabled) this.load(true); }
  handleSelect(event) { this.loadDetail(event.currentTarget.dataset.id); }
  handleToggleDetailFocus() {
    if (this.hasDetail) this.detailExpanded = !this.detailExpanded;
  }
  handleArchiveFilterChange(event) {
    this.archiveFilter = event.target.value || "";
  }
  handleClose() {
    this.detailExpanded = false;
    this.handleArchiveClose();
    ++this._detailRequest;
    this.detail = undefined;
    this.selectedId = undefined;
    this.detailError = undefined;
  }
  handleOpenComponent(event) { this.open(event.currentTarget.dataset.id, "Flosum__Component__c"); }
  handleOpenBranch(event) { this.open(event.currentTarget.dataset.id, "Flosum__Branch__c"); }
  handleOpenHistory(event) { this.open(event.currentTarget.dataset.id, "Flosum__Component_History__c"); }

  handleArchiveClose() {
    ++this._archiveRequest;
    this.archiveFilter = "";
    this.archiveOpen = false;
    this.archiveLoading = false;
    this.archiveData = undefined;
    this.archiveError = undefined;
    this.archiveHistoryId = undefined;
  }
  handleExploreHistory(event) {
    const historyId = event.currentTarget.dataset.id;
    if (!historyId) return;
    this.archiveHistoryId = historyId;
    this.archiveFilter = "";
    this.archiveData = undefined;
    this.archiveOpen = true;
    this.loadArchive(null);
  }
  handleSelectArchiveFile(event) {
    const path = event.currentTarget.dataset.path;
    if (path) this.loadArchive(path);
  }
  async loadArchive(entryPath) {
    const request = ++this._archiveRequest;
    this.archiveLoading = true;
    this.archiveError = undefined;
    try {
      const response = await inspectHistoryArchive({historyId: this.archiveHistoryId, entryPath});
      if (request === this._archiveRequest) this.archiveData = response;
    } catch (error) {
      if (request === this._archiveRequest) {
        this.archiveError = this.message(error, "Não foi possível abrir o ZIP acessível.");
      }
    } finally {
      if (request === this._archiveRequest) this.archiveLoading = false;
    }
  }
  open(id, objectApiName) {
    if (!id) return;
    this[NavigationMixin.Navigate]({
      type: "standard__recordPage",
      attributes: { recordId: id, objectApiName, actionName: "view" }
    });
  }
  message(error, fallback) { return error?.body?.message || fallback; }

  handleTypeFocus() {
    this.typeMenuOpen = true;
    this.loadTypeOptions();
  }
  handleTypeChange(event) {
    this.typeText = event.target.value || "";
    clearTimeout(this._typeDebounce);
    ++this._typeRequest;
    if (this.typeValue) {
      this.typeValue = null;
      this.resetResults();
      if (this.eligible) this.load(false);
    }
    this.typeMenuOpen = true;
    this.typeOptions = [];
    if (this.typeText.length > 80) {
      this.typeError = "A pesquisa de tipos permite até 80 caracteres.";
      return;
    }
    this.typeError = undefined;
    // eslint-disable-next-line @lwc/lwc/no-async-operation
    this._typeDebounce = setTimeout(() => this.loadTypeOptions(), 250);
  }
  handleTypeKey(event) {
    if (event.key === "Escape") {
      this.typeMenuOpen = false;
    } else if (event.key === "ArrowDown" && this.hasTypeOptions) {
      event.preventDefault();
      this.template.querySelector(".cd-type-option")?.focus();
    } else if (event.key === "Enter" && this.hasTypeOptions && this.typeMenuOpen) {
      event.preventDefault();
      this.selectType(this.typeOptions[0]);
    }
  }
  handleTypeSelect(event) {
    const option = this.typeOptions.find(o => o.value === event.currentTarget.dataset.value);
    if (option) this.selectType(option);
  }
  selectType(option) {
    clearTimeout(this._typeDebounce);
    ++this._typeRequest;
    this.typeText = option.label;
    this.typeValue = option.value;
    this.typeMenuOpen = false;
    this.typeError = undefined;
    this.load(false);
  }
  handleTypeClear() {
    clearTimeout(this._typeDebounce);
    ++this._typeRequest;
    this.typeText = "";
    this.typeValue = null;
    this.typeMenuOpen = false;
    this.typeOptions = [];
    this.typeError = undefined;
    if (this.eligible) this.load(false);
  }
  async loadTypeOptions() {
    if (this.typeText.length > 80) return;
    const request = ++this._typeRequest;
    this.typeLoading = true;
    this.typeError = undefined;
    try {
      const options = await getComponentTypes({ searchTerm: this.typeValue ? "" : this.typeText.trim() });
      if (request === this._typeRequest) this.typeOptions = options || [];
    } catch (error) {
      if (request === this._typeRequest) {
        this.typeOptions = [];
        this.typeError = this.message(error, "Não foi possível consultar os tipos.");
      }
    } finally {
      if (request === this._typeRequest) this.typeLoading = false;
    }
  }

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
      const page = await searchFilteredComponents({
        search: this.search.trim() || null,
        componentType: this.typeValue || null,
        cursorName: append ? this.cursorName : null,
        cursorId: append ? this.cursorId : null
      });
      if (request !== this._searchRequest) return;
      this.results = append ? [...this.results, ...(page.rows || [])] : (page.rows || []);
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
    this.detailExpanded = false;
    this.handleArchiveClose();
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
