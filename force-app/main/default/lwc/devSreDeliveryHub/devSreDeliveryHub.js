import { LightningElement } from "lwc";

const TABS = ["overview", "deployments", "environments"];

export default class DevSreDeliveryHub extends LightningElement {
  activeTab = "overview";

  get isOverview() {
    return this.activeTab === "overview";
  }
  get isDeployments() {
    return this.activeTab === "deployments";
  }
  get isEnvironments() {
    return this.activeTab === "environments";
  }
  get activeTabLabel() {
    return {
      overview: "Visão geral",
      deployments: "Deployments",
      environments: "Ambientes"
    }[this.activeTab];
  }
  get activePanelLabel() {
    return "pm-tab-" + this.activeTab;
  }
  get overviewTabClass() {
    return this.tabClass("overview");
  }
  get deploymentsTabClass() {
    return this.tabClass("deployments");
  }
  get environmentsTabClass() {
    return this.tabClass("environments");
  }
  get overviewTabIndex() {
    return this.isOverview ? "0" : "-1";
  }
  get deploymentsTabIndex() {
    return this.isDeployments ? "0" : "-1";
  }
  get environmentsTabIndex() {
    return this.isEnvironments ? "0" : "-1";
  }
  tabClass(name) {
    return name === this.activeTab ? "pm-tab pm-tab_active" : "pm-tab";
  }
  handleTabChange(event) {
    const next = event.currentTarget.dataset.tab;
    if (TABS.includes(next)) this.activeTab = next;
  }
  handleTabKeydown(event) {
    const current = TABS.indexOf(event.currentTarget.dataset.tab);
    if (current < 0) return;
    let next = current;
    if (event.key === "ArrowRight") next = (current + 1) % TABS.length;
    else if (event.key === "ArrowLeft") next = (current + TABS.length - 1) % TABS.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = TABS.length - 1;
    else return;
    event.preventDefault();
    this.activeTab = TABS[next];
    this.template.querySelector('[data-tab="' + TABS[next] + '"]')?.focus();
  }
  handleMappingChange() {
    // Views are mutually exclusive and remount on navigation. Both consult
    // the live Apex source when opened, so no hidden duplicate refresh is needed.
  }
}