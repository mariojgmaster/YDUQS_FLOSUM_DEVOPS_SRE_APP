import { LightningElement } from "lwc";
import { NavigationMixin } from "lightning/navigation";
import searchFilteredComponents from "@salesforce/apex/DevSreComponentDescriberController.searchFilteredComponents";
import getComponentTypes from "@salesforce/apex/DevSreComponentDescriberController.getComponentTypes";
import describeComponent from "@salesforce/apex/DevSreComponentDescriberController.describeComponent";
import inspectHistoryArchive from "@salesforce/apex/DevSreComponentDescriberController.inspectHistoryArchive";
import { archivePathInventory, lineDiff, sideBySideDiff } from "./historyDiff";
import { componentEvidence } from "./componentEvidence";

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
  workspaceTab = "ficha";
  archiveLoading = false;
  archiveError;
  archiveData;
  archiveHistoryId;
  archiveRetryPath = null;
  _archiveRequest = 0;
  compareOpen = false;
  compareLoading = false;
  compareError;
  compareOptions = [];
  compareBaseId = "";
  compareTargetId = "";
  comparePaths = [];
  compareInventory = null;
  compareInventoryFilter = "all";
  comparePath = "";
  compareDiff;
  diffOnlyChanges = false;
  mobileDiffSide = "base";
  diffPage = 0;
  diffPageSize = 250;
  diffPairsAll = [];
  diffPairsChanges = [];
  _compareRequest = 0;
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
    ++this._compareRequest;
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
  get hasHistoryCount() { return !this.historyUnavailable; }
  get historyCountLabel() {
    const count = this.histories.length;
    return count === 1 ? "1 histórico nesta consulta" : `${count} históricos nesta consulta`;
  }
  get hasHistories() { return this.histories.length > 0; }
  get canCompareHistories() {
    return !this.historyUnavailable && this.histories.length >= 2;
  }
  get historyCompareOptions() {
    return this.histories.map((h, i) => ({
      label: `Histórico ${i + 1} · ${h.createdAt || "data indisponível"}`,
      value: h.id
    }));
  }
  get compareFileOptions() {
    return this.comparePaths.map(path => ({ label: path, value: path }));
  }
  get hasComparePaths() { return this.comparePaths.length > 0; }
  get hasCompareInventory() { return (this.compareInventory?.rows?.length || 0) > 0; }
  get compareInventoryCounts() { return this.compareInventory?.counts || {common:0,base:0,target:0,blocked:0}; }
  get compareInventoryRows() {
    const rows = this.compareInventory?.rows || [];
    return this.compareInventoryFilter === "all" ? rows :
      rows.filter(row => row.status === this.compareInventoryFilter);
  }
  get hasMatchingCompareInventory() { return this.compareInventoryRows.length > 0; }
  get compareInventoryFilterOptions() {
    const counts = this.compareInventoryCounts;
    const total = Object.values(counts).reduce((a,b)=>a+b,0);
    return [
      {label:`Todos (${total})`,value:"all"},
      {label:`Em ambos (${counts.common})`,value:"common"},
      {label:`Somente base (${counts.base})`,value:"base"},
      {label:`Somente destino (${counts.target})`,value:"target"},
      {label:`Indisponíveis (${counts.blocked})`,value:"blocked"}
    ];
  }
  get hasCompareRows() { return (this.compareDiff?.rows || []).length > 0; }
  get compareRows() { return this.compareDiff?.rows || []; }
  get diffBaseRows() { return this.sideBySideRows.map(row => ({ key: row.key, ...row.left })); }
  get mobileBasePaneClass() {
    return this.mobileDiffSide === "base" ? "cd-diff-col" : "cd-diff-col cd-diff-col_mobile-hidden";
  }
  get mobileTargetPaneClass() {
    return this.mobileDiffSide === "target" ? "cd-diff-col" : "cd-diff-col cd-diff-col_mobile-hidden";
  }
  get mobileBaseControlClass() {
    return this.mobileDiffSide === "base" ? "cd-mobile-switch-button cd-mobile-switch-button_active" : "cd-mobile-switch-button";
  }
  get mobileTargetControlClass() {
    return this.mobileDiffSide === "target" ? "cd-mobile-switch-button cd-mobile-switch-button_active" : "cd-mobile-switch-button";
  }
  get mobileBaseSelected() { return this.mobileDiffSide === "base"; }
  get mobileTargetSelected() { return this.mobileDiffSide === "target"; }
  get diffTargetRows() { return this.sideBySideRows.map(row => ({ key: row.key, ...row.right })); }
  get activeDiffPairs() { return this.diffOnlyChanges ? this.diffPairsChanges : this.diffPairsAll; }
  get diffTotalPages() { return Math.max(1, Math.ceil(this.activeDiffPairs.length / this.diffPageSize)); }
  get diffPageLabel() {
    return `Bloco ${this.diffPage+1} de ${this.diffTotalPages} · ${this.activeDiffPairs.length} linhas alinhadas`;
  }
  get diffPreviousDisabled() { return this.diffPage===0; }
  get diffNextDisabled() { return this.diffPage>=this.diffTotalPages-1; }
  get sideBySideRows() {
    return this.activeDiffPairs.slice(this.diffPage*this.diffPageSize,(this.diffPage+1)*this.diffPageSize);
  }
  get hasSideBySideRows() { return this.sideBySideRows.length > 0; }
  get allLinesButtonVariant() { return this.diffOnlyChanges ? "neutral" : "brand"; }
  get onlyChangesButtonVariant() { return this.diffOnlyChanges ? "brand" : "neutral"; }
  get hasNoChangedLines() { return this.diffOnlyChanges && this.compareUnchanged; }
  get compareAdded() { return this.compareDiff?.added || 0; }
  get compareRemoved() { return this.compareDiff?.removed || 0; }
  get compareUnchanged() { return Boolean(this.compareDiff?.unchanged); }
  get compareWarning() { return this.compareDiff?.error || ""; }
  get historyUnavailable() { return this.detail?.historyQuality !== "TYPED_LINK_SAMPLE"; }
  get hasHistoryMore() { return Boolean(this.detail?.historiesHasMore); }
  get nextDisabled() { return !this.hasMore || this.loading || !this.eligible; }
  get hasTypeOptions() { return this.typeOptions.length > 0; }
  get isTypeSelected() { return Boolean(this.typeValue); }
  get emptyWithoutFilters() { return !this.search.trim() && !this.typeValue; }
  get showResults() { return !this.detailExpanded; }
  get showWorkspaceNav() { return this.detailExpanded && this.hasDetail; }
  get showFactsSection() { return !this.detailExpanded || this.workspaceTab === "ficha"; }
  get showHistorySection() { return !this.detailExpanded || this.workspaceTab === "historicos"; }
  get showArchiveSection() {
    return this.archiveOpen && (!this.detailExpanded || this.workspaceTab === "arquivos");
  }
  get showCompareSection() {
    return this.compareOpen && (!this.detailExpanded || this.workspaceTab === "comparar");
  }
  get workspaceLabel() {
    return ({ficha:"Ficha",historicos:"Históricos",arquivos:"Arquivos ZIP",comparar:"Comparar"})[this.workspaceTab] || "Ficha";
  }
  get fichaVariant() { return this.workspaceTab === "ficha" ? "brand" : "neutral"; }
  get historiesVariant() { return this.workspaceTab === "historicos" ? "brand" : "neutral"; }
  get zipVariant() { return this.workspaceTab === "arquivos" ? "brand" : "neutral"; }
  get compareVariant() { return this.workspaceTab === "comparar" ? "brand" : "neutral"; }
  get archiveNavigationDisabled() { return !this.archiveOpen; }
  get compareNavigationDisabled() { return !this.compareOpen; }
  get layoutClass() { return this.detailExpanded ? "cd-layout cd-layout_focus" : "cd-layout"; }
  get hasArchiveEntries() { return (this.archiveData?.entries || []).length > 0; }
  get hasPreviewableArchiveEntries() {
    return (this.archiveData?.entries || []).some(entry => entry.previewable);
  }
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
  get traceabilityEntries() { return componentEvidence(this.detail); }
  get detailType() { return this.detail?.component?.componentType || "Não informado"; }
  get noMatches() { return this.searched && !this.loading && !this.error && !this.hasResults; }

  resetResults() {
    this.handleCompareClose();
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
  handleRetrySearch() {
    if (this.eligible && !this.loading) this.load(false);
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
  get isNarrowViewport() {
    // Match the stylesheet breakpoint; Jest and non-browser contexts stay desktop by default.
    return typeof window !== "undefined" && typeof window.matchMedia === "function" &&
      window.matchMedia("(max-width: 48rem)").matches;
  }
  handleToggleDetailFocus() {
    if (!this.hasDetail) return;
    this.detailExpanded = !this.detailExpanded;
    this.workspaceTab = this.detailExpanded ?
      (this.compareOpen ? "comparar" : this.archiveOpen ? "arquivos" : "ficha") : "ficha";
  }
  handleBackToList() {
    this.detailExpanded = false;
    this.workspaceTab = "ficha";
  }
  handleNavigateWorkspace(event) {
    const next = event.currentTarget.dataset.tab;
    if (!this.detailExpanded) return;
    if (!["ficha","historicos","arquivos","comparar"].includes(next)) return;
    if (next === "arquivos" && !this.archiveOpen) return;
    if (next === "comparar" && !this.compareOpen) return;
    this.workspaceTab = next;
  }
  handleArchiveFilterChange(event) {
    this.archiveFilter = event.target.value || "";
  }
  handleArchiveClearFilter() {
    this.archiveFilter = "";
  }
  handleClose() {
    this.handleCompareClose();
    this.detailExpanded = false;
    this.workspaceTab = "ficha";
    this.handleArchiveClose();
    ++this._detailRequest;
    this.detail = undefined;
    this.selectedId = undefined;
    this.detailError = undefined;
  }
  handleOpenComponent(event) { this.open(event.currentTarget.dataset.id, "Flosum__Component__c"); }
  handleOpenBranch(event) { this.open(event.currentTarget.dataset.id, "Flosum__Branch__c"); }
  handleOpenHistory(event) { this.open(event.currentTarget.dataset.id, "Flosum__Component_History__c"); }

  handleRetryDetail() {
    if (this.selectedId && !this.detailLoading) this.loadDetail(this.selectedId);
  }
  handleArchiveClose() {
    if (this.workspaceTab === "arquivos") this.workspaceTab = "historicos";
    ++this._archiveRequest;
    this.archiveFilter = "";
    this.archiveOpen = false;
    this.archiveLoading = false;
    this.archiveData = undefined;
    this.archiveError = undefined;
    this.archiveHistoryId = undefined;
    this.archiveRetryPath = null;
  }
  handleExploreHistory(event) {
    const historyId = event.currentTarget.dataset.id;
    if (!historyId) return;
    this.archiveHistoryId = historyId;
    this.archiveFilter = "";
    this.archiveData = undefined;
    this.archiveOpen = true;
    if (this.detailExpanded) this.workspaceTab = "arquivos";
    this.loadArchive(null);
  }
  handleSelectArchiveFile(event) {
    const path = event.currentTarget.dataset.path;
    if (path) this.loadArchive(path);
  }
  handleRetryArchive() {
    if (this.archiveOpen && this.archiveHistoryId && !this.archiveLoading)
      this.loadArchive(this.archiveRetryPath);
  }
  async loadArchive(entryPath) {
    const request = ++this._archiveRequest;
    this.archiveRetryPath = entryPath;
    this.archiveLoading = true;
    this.archiveError = undefined;
    try {
      const response = await inspectHistoryArchive({historyId: this.archiveHistoryId, entryPath});
      if (request === this._archiveRequest) {
        // Reading one text member may return only selectedPath/text. Keep the
        // previously verified ZIP index rather than hiding the file list.
        this.archiveData = entryPath && Array.isArray(this.archiveData?.entries) &&
          !Array.isArray(response?.entries) ?
          {...this.archiveData, ...response} : response;
      }
    } catch (error) {
      if (request === this._archiveRequest) {
        this.archiveError = this.message(error, "Não foi possível abrir o ZIP acessível.");
      }
    } finally {
      if (request === this._archiveRequest) this.archiveLoading = false;
    }
  }
  handleCompareToggle() {
    if (this.compareOpen) {
      this.handleCompareClose();
      return;
    }
    if (!this.canCompareHistories) return;
    this.compareOpen = true;
    this.mobileDiffSide = "base";
    this.detailExpanded = true;
    this.workspaceTab = "comparar";
    this.diffOnlyChanges = false;
    // Histories are ordered by CreatedDate descending in the existing typed Apex query.
    this.compareBaseId = this.histories[1].id;
    this.compareTargetId = this.histories[0].id;
    this.loadCompareArchives();
  }
  handleRetryCompare() {
    if (this.compareOpen && !this.compareLoading) this.loadCompareArchives();
  }
  handleCompareInventoryFilterChange(event) {
    const value = event.detail.value;
    if (["all","common","base","target","blocked"].includes(value)) this.compareInventoryFilter = value;
  }
  handleCompareClose() {
    if (this.workspaceTab === "comparar") this.workspaceTab = "historicos";
    ++this._compareRequest;
    this.compareOpen = false;
    this.mobileDiffSide = "base";
    this.compareLoading = false;
    this.compareError = undefined;
    this.comparePaths = [];
    this.compareInventory = null;
    this.compareInventoryFilter = "all";
    this.comparePath = "";
    this.compareDiff = undefined;
    this.diffOnlyChanges = false;
    this.diffPage=0;
    this.diffPairsAll=[];
    this.diffPairsChanges=[];
    this.compareBaseId = "";
    this.compareTargetId = "";
  }
  handleMobileShowBase() { this.mobileDiffSide = "base"; }
  handleMobileShowTarget() { this.mobileDiffSide = "target"; }
  handleDiffModeAll() { this.diffOnlyChanges = false; this.diffPage = 0; this.resetDiffScroll(); }
  handleDiffModeChanged() { this.diffOnlyChanges = true; this.diffPage = 0; this.resetDiffScroll(); }
  handleDiffPrevious() { if(!this.diffPreviousDisabled){this.diffPage--;this.resetDiffScroll();} }
  handleDiffNext() { if(!this.diffNextDisabled){this.diffPage++;this.resetDiffScroll();} }
  resetDiffScroll() {
    const viewport = this.template.querySelector(".cd-diff-viewport");
    if (viewport) viewport.scrollTop = 0;
  }
  handleSwapHistories() {
    if (!this.compareOpen) return;
    const base = this.compareBaseId;
    this.compareBaseId = this.compareTargetId;
    this.compareTargetId = base;
    this.loadCompareArchives();
  }
  handleCompareHistoryChange(event) {
    const id = event.detail.value;
    if (!this.histories.some(x => x.id === id)) return;
    if (event.currentTarget.dataset.side === "base") this.compareBaseId = id;
    else if (event.currentTarget.dataset.side === "target") this.compareTargetId = id;
    else return;
    this.loadCompareArchives();
  }
  async loadCompareArchives() {
    const request = ++this._compareRequest;
    this.compareError = undefined;
    this.compareDiff = undefined;
    this.diffPage=0;
    this.diffPairsAll=[];
    this.diffPairsChanges=[];
    this.comparePaths = [];
    this.compareInventory = null;
    this.compareInventoryFilter = "all";
    this.comparePath = "";
    const allowedIds = new Set(this.histories.map(x => x.id));
    if (!this.compareOpen || !allowedIds.has(this.compareBaseId) ||
      !allowedIds.has(this.compareTargetId) || this.compareBaseId === this.compareTargetId) {
      this.compareLoading = false;
      this.compareError = "Selecione dois históricos diferentes do componente.";
      return;
    }
    this.compareLoading = true;
    try {
      const [base, target] = await Promise.all([
        inspectHistoryArchive({ historyId: this.compareBaseId, entryPath: null }),
        inspectHistoryArchive({ historyId: this.compareTargetId, entryPath: null })
      ]);
      if (request !== this._compareRequest) return;
      this.compareInventory = archivePathInventory(base, target);
      this.comparePaths = this.compareInventory.rows.filter(row => row.status === "common")
        .map(row => row.path);
    } catch (error) {
      if (request === this._compareRequest)
        this.compareError = this.message(error, "Não foi possível acessar os dois ZIPs.");
    } finally {
      if (request === this._compareRequest) this.compareLoading = false;
    }
  }
  async handleCompareFileChange(event) {
    const path = event.detail.value;
    if (!this.comparePaths.includes(path) || !this.compareOpen) return;
    const request = ++this._compareRequest;
    this.comparePath = path;
    this.compareDiff = undefined;
    this.diffPage=0;
    this.diffPairsAll=[];
    this.diffPairsChanges=[];
    this.compareError = undefined;
    this.compareLoading = true;
    try {
      const [base, target] = await Promise.all([
        inspectHistoryArchive({ historyId: this.compareBaseId, entryPath: path }),
        inspectHistoryArchive({ historyId: this.compareTargetId, entryPath: path })
      ]);
      if (request !== this._compareRequest) return;
      if (base?.selectedPath !== path || target?.selectedPath !== path) {
        this.compareError = "A correspondência do caminho não foi confirmada nos dois arquivos.";
        return;
      }
      this.compareDiff = lineDiff(base.text, target.text);
      this.diffPairsAll = sideBySideDiff(this.compareDiff);
      this.diffPairsChanges = this.diffPairsAll.filter(row => row.changed);
    } catch (error) {
      if (request === this._compareRequest)
        this.compareError = this.message(error, "Não foi possível comparar o conteúdo.");
    } finally {
      if (request === this._compareRequest) this.compareLoading = false;
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
    if (!append) this.handleCompareClose();
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
    this.handleCompareClose();
    this.detailExpanded = this.isNarrowViewport;
    this.workspaceTab = "ficha";
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
