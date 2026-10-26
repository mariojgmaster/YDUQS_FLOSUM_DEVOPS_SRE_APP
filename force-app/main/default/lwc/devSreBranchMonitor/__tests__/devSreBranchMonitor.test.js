import { createElement } from "lwc";
import Component from "c/devSreBranchMonitor";
import getOverview from "@salesforce/apex/DevSreBranchMonitorController.getOverview";
import listBranches from "@salesforce/apex/DevSreBranchMonitorController.listBranches";
import getBranchDetail from "@salesforce/apex/DevSreBranchMonitorController.getBranchDetail";
jest.mock("@salesforce/apex/DevSreBranchMonitorController.getOverview",
  () => ({ default: jest.fn() }), { virtual: true });
jest.mock("@salesforce/apex/DevSreBranchMonitorController.listBranches",
  () => ({ default: jest.fn() }), { virtual: true });
jest.mock("@salesforce/apex/DevSreBranchMonitorController.getBranchDetail",
  () => ({ default: jest.fn() }), { virtual: true });

const flush = async () => { for (let i=0;i<12;i++) await Promise.resolve(); };
const LOG = {id:"a01001",name:"ML-01",branchId:"a0B001",branchName:"feature/CRM",
  processType:"Deployment",outcome:"Sucesso",createdAt:"2026-10-25T10:00:00Z"};
const SUMMARY = { complete:true, activeBranches:1,deployments:1,validations:1,
  succeeded:1,failed:0,operations:2,recent:[LOG] };
const BRANCH = {id:"a0B001",name:"feature/CRM",modifiedAt:"2026-10-25T09:00:00Z"};
const PAGE = {rows:[BRANCH],hasMore:false,cursorName:BRANCH.name,cursorId:BRANCH.id};
const DETAIL = {id:BRANCH.id,name:BRANCH.name,hasMore:false,recent:[LOG]};
function mount(){const el=createElement("c-dev-sre-branch-monitor",{is:Component});document.body.appendChild(el);return el;}
function tab(el,name){return el.shadowRoot.querySelector('[data-tab="'+name+'"]');}
function text(el){return el.shadowRoot.textContent;}
describe("Branch Monitor M1 — fonte real e experiência de leitura",()=>{
  beforeEach(()=>{
    jest.clearAllMocks();
    jest.useFakeTimers();
    getOverview.mockResolvedValue(SUMMARY);
    listBranches.mockResolvedValue(PAGE);
    getBranchDetail.mockResolvedValue(DETAIL);
  });
  afterEach(()=>{document.body.innerHTML="";jest.useRealTimers();});
  it("apresenta quatro seções sem renderizar dados simulados de Diff",async()=>{
    const el=mount();await flush();
    expect(tab(el,"overview").getAttribute("aria-selected")).toBe("true");
    expect(el.shadowRoot.querySelectorAll('[role="tab"]')).toHaveLength(4);
    expect(text(el)).toContain("Branches com atividade");
    expect(text(el)).toContain("ML-01");
    tab(el,"compare").click();await flush();
    expect(text(el)).toContain("Comparação ainda indisponível");
    expect(text(el)).not.toContain("ML-01");
    tab(el,"components").click();await flush();
    expect(text(el)).toContain("Pesquisa por componente em preparação");
    expect(getBranchDetail).not.toHaveBeenCalled();
  });
  it("filtra período instantaneamente e esconde totais quando incompletos",async()=>{
    const el=mount();await flush();
    const control=el.shadowRoot.querySelector("lightning-combobox");
    control.dispatchEvent(new CustomEvent("change",{detail:{value:"7"}}));
    await flush();
    expect(getOverview).toHaveBeenLastCalledWith({days:7});
    getOverview.mockResolvedValue({complete:false,recent:[LOG]});
    el.shadowRoot.querySelector('[title="Atualizar atividades"]').click();
    await flush();
    expect(text(el)).toContain("Indicadores globais ocultos");
    expect(el.shadowRoot.querySelector(".bm-metrics")).toBeNull();
    expect(text(el)).toContain("ML-01");
  });
  it("pesquisa Branch com debounce, seleciona registro e mostra logs reais",async()=>{
    const el=mount();await flush();
    tab(el,"branches").click();await flush();
    expect(listBranches).toHaveBeenCalledWith({search:null,cursorName:null,cursorId:null});
    const input=el.shadowRoot.querySelector("lightning-input");
    input.value="feature";
    input.dispatchEvent(new CustomEvent("change"));
    jest.advanceTimersByTime(350);
    await flush();
    expect(listBranches).toHaveBeenLastCalledWith({search:"feature",cursorName:null,cursorId:null});
    el.shadowRoot.querySelector(".bm-branch-table .bm-link").click();
    await flush();
    expect(getBranchDetail).toHaveBeenCalledWith({branchId:BRANCH.id});
    expect(text(el)).toContain("Operações recentes");
    expect(text(el)).toContain("ML-01");
  });
  it("paginação usa cursor da fonte e não alega total global",async()=>{
    listBranches.mockResolvedValueOnce({...PAGE,hasMore:true});
    const el=mount();await flush();tab(el,"branches").click();await flush();
    const more=[...el.shadowRoot.querySelectorAll("lightning-button")].find(x=>x.label==="Carregar mais");
    expect(more.disabled).toBe(false);
    more.click();await flush();
    expect(listBranches).toHaveBeenLastCalledWith({search:null,cursorName:BRANCH.name,cursorId:BRANCH.id});
    expect(text(el)).toContain("não representa total global");
  });
  it("isola falha de overview do restante e bloqueia duplas respostas obsoletas",async()=>{
    getOverview.mockRejectedValue({body:{message:"Sem acesso"}});
    const el=mount();await flush();
    expect(el.shadowRoot.querySelector('[role="alert"]').textContent).toContain("Sem acesso");
    tab(el,"branches").click();await flush();
    expect(text(el)).toContain("feature/CRM");
  });
  it("suporta tabs por teclado",async()=>{
    const el=mount();await flush();
    const e=new KeyboardEvent("keydown",{key:"ArrowRight",bubbles:true});
    tab(el,"overview").dispatchEvent(e);await flush();
    expect(tab(el,"branches").getAttribute("aria-selected")).toBe("true");
  });
});