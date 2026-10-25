import { createElement } from "lwc";
import DevSreDeliveryHub from "c/devSreDeliveryHub";
import listMonitorDeployments from "@salesforce/apex/DevSreDeploymentController.listMonitorDeployments";
import getMonitorSummary from "@salesforce/apex/DevSreDeploymentController.getMonitorSummary";
import listDeployments from "@salesforce/apex/DevSreDeploymentController.listDeployments";
import searchOrganizations from "@salesforce/apex/DevSreEnvironmentController.searchOrganizations";
import listMappings from "@salesforce/apex/DevSreEnvironmentController.listMappings";

jest.mock(
  "@salesforce/apex/DevSreDeploymentController.listMonitorDeployments",
  () => ({ default: jest.fn() }), { virtual: true }
);
jest.mock(
  "@salesforce/apex/DevSreDeploymentController.getMonitorSummary",
  () => ({ default: jest.fn() }), { virtual: true }
);
jest.mock(
  "@salesforce/apex/DevSreDeploymentController.listDeployments",
  () => ({ default: jest.fn() }), { virtual: true }
);
jest.mock(
  "@salesforce/apex/DevSreEnvironmentController.searchOrganizations",
  () => ({ default: jest.fn() }), { virtual: true }
);
jest.mock(
  "@salesforce/apex/DevSreEnvironmentController.listMappings",
  () => ({ default: jest.fn() }), { virtual: true }
);

const flush = async () => {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
};

const openHub = () => {
  const element = createElement("c-dev-sre-delivery-hub", {
    is: DevSreDeliveryHub
  });
  document.body.appendChild(element);
  return element;
};

const tab = (element, id) =>
  element.shadowRoot.querySelector('[data-tab="' + id + '"]');

const has = (element, selector) =>
  Boolean(element.shadowRoot.querySelector(selector));

describe("Pipeline Monitor — uma seção por vez", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    listMonitorDeployments.mockResolvedValue({
      rows: [], hasMore: false, cursorCreated: null, cursorId: null
    });
    getMonitorSummary.mockResolvedValue({
      complete: true, total: 0, succeeded: 0, failed: 0,
      pending: 0, partial: 0, notRun: 0, unknown: 0, successRate: null
    });
    listDeployments.mockResolvedValue({
      rows: [], hasMore: false, inspectedRows: 0, correlationIncomplete: false
    });
    searchOrganizations.mockResolvedValue({
      options: [], hasMore: false, canManage: false
    });
    listMappings.mockResolvedValue([]);
  });
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("abre apenas a visão geral e mantém o Shell branco", async () => {
    const element = openHub();
    await flush();

    expect(has(element, "c-dev-sre-pipeline-overview")).toBe(true);
    expect(has(element, "c-dev-sre-deployments")).toBe(false);
    expect(has(element, "c-dev-sre-environments")).toBe(false);
    expect(has(element, "c-pipeline-monitor")).toBe(false);
    expect(element.shadowRoot.querySelectorAll('[role="tabpanel"]')).toHaveLength(1);
    expect(element.shadowRoot.querySelectorAll('[role="tab"]')).toHaveLength(3);
    expect(tab(element, "overview").getAttribute("aria-selected")).toBe("true");
    expect(tab(element, "overview").className).toContain("pm-tab_active");
    expect(element.shadowRoot.querySelector(".pm-shell")).not.toBeNull();
  });

  it("troca de seção sem empilhar conteúdo ou perder o cabeçalho", async () => {
    const element = openHub();
    await flush();
    tab(element, "deployments").click();
    await flush();

    expect(has(element, "c-dev-sre-deployments")).toBe(true);
    expect(has(element, "c-dev-sre-pipeline-overview")).toBe(false);
    expect(has(element, "c-dev-sre-environments")).toBe(false);
    expect(tab(element, "deployments").getAttribute("aria-selected")).toBe("true");
    expect(tab(element, "overview").getAttribute("aria-selected")).toBe("false");

    tab(element, "environments").click();
    await flush();
    expect(has(element, "c-dev-sre-environments")).toBe(true);
    expect(has(element, "c-dev-sre-deployments")).toBe(false);
    expect(has(element, "c-dev-sre-pipeline-overview")).toBe(false);
    expect(element.shadowRoot.querySelector(".pm-breadcrumb-current").textContent)
      .toBe("Ambientes");

    tab(element, "overview").click();
    await flush();
    expect(has(element, "c-dev-sre-pipeline-overview")).toBe(true);
    expect(has(element, "c-dev-sre-environments")).toBe(false);
  });

  it("é navegável por teclado com setas, Home e End", async () => {
    const element = openHub();
    await flush();
    tab(element, "overview").dispatchEvent(new KeyboardEvent("keydown", {
      key: "ArrowRight",
      bubbles: true,
      composed: true
    }));
    await flush();
    expect(tab(element, "deployments").getAttribute("tabindex")).toBe("0");
    expect(has(element, "c-dev-sre-deployments")).toBe(true);

    tab(element, "deployments").dispatchEvent(new KeyboardEvent("keydown", {
      key: "End", bubbles: true, composed: true
    }));
    await flush();
    expect(has(element, "c-dev-sre-environments")).toBe(true);

    tab(element, "environments").dispatchEvent(new KeyboardEvent("keydown", {
      key: "Home", bubbles: true, composed: true
    }));
    await flush();
    expect(has(element, "c-dev-sre-pipeline-overview")).toBe(true);
  });
});
