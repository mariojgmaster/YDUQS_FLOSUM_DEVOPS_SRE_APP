import {createElement} from "lwc";
import Describer from "c/devSreComponentDescriber";
import searchFilteredComponents from "@salesforce/apex/DevSreComponentDescriberController.searchFilteredComponents";
import getComponentTypes from "@salesforce/apex/DevSreComponentDescriberController.getComponentTypes";
import describeComponent from "@salesforce/apex/DevSreComponentDescriberController.describeComponent";
import inspectHistoryArchive from "@salesforce/apex/DevSreComponentDescriberController.inspectHistoryArchive";
import { commonPreviewPaths, archivePathInventory, lineDiff, sideBySideDiff } from "../historyDiff";

jest.mock("@salesforce/apex/DevSreComponentDescriberController.searchFilteredComponents",
  () => ({default: jest.fn()}), {virtual: true});
jest.mock("@salesforce/apex/DevSreComponentDescriberController.getComponentTypes",
  () => ({default: jest.fn()}), {virtual: true});
jest.mock("@salesforce/apex/DevSreComponentDescriberController.describeComponent",
  () => ({default: jest.fn()}), {virtual: true});
jest.mock("@salesforce/apex/DevSreComponentDescriberController.inspectHistoryArchive",
  () => ({default: jest.fn()}), {virtual: true});

const flush=async()=>{for(let i=0;i<15;i++)await Promise.resolve();};
const X={id:"a000001",name:"C-138803",componentName:"T_DefineFlowByObjectAPP",
  componentType:"ApexClass",source:"Snapshot",sourceDetails:"Snapshot 01",
  version:"1.00",branchId:"a0B0001",branchName:"Branch SIT"};
const Y={id:"a000002",name:"C-138804",componentName:"T_DefineFlowByObjectAPP",
  componentType:"ApexClass",source:"Commit",version:"2.00",
  branchId:"a0B0002",branchName:"Branch PROD"};
const PAGE={rows:[X,Y],hasMore:false,cursorName:Y.name,cursorId:Y.id,identityLevel:"REGISTERED_NAME_ONLY"};
const TYPES=[{label:"Apex Class",value:"ApexClass"},{label:"Flow",value:"Flow"}];
const HISTORY={id:"a0H00001",createdAt:"2026-10-24T10:00:00Z"};
const DETAIL={component:X,histories:[HISTORY],historiesHasMore:false,
  historyQuality:"TYPED_LINK_SAMPLE",deployEvidenceQuality:"UNVERIFIED"};
function mount(){const el=createElement("c-dev-sre-component-describer",{is:Describer});document.body.appendChild(el);return el;}
function text(el){return el.shadowRoot.textContent;}
function field(el,index=0){return el.shadowRoot.querySelectorAll("lightning-input")[index];}
async function nameSearch(el,term){
  const input=field(el);input.value=term;
  input.dispatchEvent(new CustomEvent("change"));jest.advanceTimersByTime(350);await flush();
}
async function typeChoices(el,term=""){
  const input=field(el,1);input.value=term;
  input.dispatchEvent(new CustomEvent("focus"));
  input.dispatchEvent(new CustomEvent("change"));
  jest.advanceTimersByTime(250);await flush();
}
describe("Branch Monitor M2 — inventário e lookup Component Type",()=>{
  beforeEach(()=>{jest.clearAllMocks();jest.useFakeTimers();
    searchFilteredComponents.mockResolvedValue(PAGE);
    getComponentTypes.mockResolvedValue(TYPES);
    describeComponent.mockResolvedValue(DETAIL);
    inspectHistoryArchive.mockResolvedValue({
      attachmentName:"ApexClass",matchingArchives:1,entries:[
        {path:"classes/T_DefineFlowByObjectAPP.cls",size:37,previewable:true},
        {path:"binary/icon.png",size:100,previewable:false}
      ],selectedPath:null,text:null
    });});
  afterEach(()=>{document.body.innerHTML="";jest.useRealTimers();});
  it("lista registros de modo paginado mesmo com nome vazio",async()=>{
    const el=mount();await flush();
    expect(searchFilteredComponents).toHaveBeenCalledWith({
      search:null,componentType:null,cursorName:null,cursorId:null});
    expect(el.shadowRoot.querySelectorAll(".cd-table tbody tr")).toHaveLength(2);
    expect(text(el)).toContain("Component Type");
    expect(text(el)).toContain("ApexClass");
    expect(text(el)).toContain("T_DefineFlowByObjectAPP");
    expect(text(el)).toContain("C-138803");
    expect(text(el)).toContain("Snapshot");
  });
  it("não pesquisa com nome de um caractere nem um nome longo",async()=>{
    const el=mount();await flush();
    await nameSearch(el,"a");
    expect(searchFilteredComponents).toHaveBeenCalledTimes(1);
    expect(text(el)).toContain("pelo menos 2 caracteres");
    await nameSearch(el,"a".repeat(81));
    expect(searchFilteredComponents).toHaveBeenCalledTimes(1);
    expect(text(el)).toContain("até 80 caracteres");
  });
  it("filtra pelo nome e preserva ocorrências homônimas de Branches distintas",async()=>{
    const el=mount();await flush();await nameSearch(el,"Flow_");
    expect(searchFilteredComponents).toHaveBeenLastCalledWith({
      search:"Flow_",componentType:null,cursorName:null,cursorId:null});
    expect(el.shadowRoot.querySelectorAll(".cd-table tbody tr")).toHaveLength(2);
    expect(text(el)).toContain("Branch SIT");
    expect(text(el)).toContain("Branch PROD");
    expect(text(el)).toContain("não comprova, sozinho, o FullName canônico");
  });
  it("exibe sugestões reais de picklist e combina Component Type e Nome",async()=>{
    const el=mount();await flush();
    await typeChoices(el,"Apex");
    expect(getComponentTypes).toHaveBeenLastCalledWith({searchTerm:"Apex"});
    const option=el.shadowRoot.querySelector(".cd-type-option");
    expect(option.textContent).toContain("Apex Class");
    option.click();await flush();
    expect(searchFilteredComponents).toHaveBeenLastCalledWith({
      search:null,componentType:"ApexClass",cursorName:null,cursorId:null});
    await nameSearch(el,"Flow");
    expect(searchFilteredComponents).toHaveBeenLastCalledWith({
      search:"Flow",componentType:"ApexClass",cursorName:null,cursorId:null});
    const clear=[...el.shadowRoot.querySelectorAll("lightning-button")].find(b=>b.label==="Limpar tipo");
    clear.click();await flush();
    expect(searchFilteredComponents).toHaveBeenLastCalledWith({
      search:"Flow",componentType:null,cursorName:null,cursorId:null});
  });
  it("consulta histórico sem inferir versões nem deploys",async()=>{
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    expect(describeComponent).toHaveBeenCalledWith({componentId:X.id});
    expect(text(el)).toContain("Component Histories relacionados");
    expect(text(el)).toContain("Snapshot 01");
    expect(text(el)).toContain("T_DefineFlowByObjectAPP");
    expect(text(el)).toContain("Abrir no Flosum");
    expect(text(el)).toContain("Não exibir histórico de deploy sem evidência direta");
  });
  it("apresenta fonte indisponível de maneira explícita",async()=>{
    describeComponent.mockResolvedValue({...DETAIL,historyQuality:"UNAVAILABLE",histories:[]});
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    expect(text(el)).toContain("fonte histórica não está acessível");
    expect(text(el)).not.toContain("Nenhum histórico acessível");
  });
  it("página seguinte preserva filtros e mostra erros Apex",async()=>{
    searchFilteredComponents.mockResolvedValueOnce({...PAGE,hasMore:true});
    const el=mount();await flush();
    const more=[...el.shadowRoot.querySelectorAll("lightning-button")].find(b=>b.label==="Carregar mais");
    more.click();await flush();
    expect(searchFilteredComponents).toHaveBeenLastCalledWith({
      search:null,componentType:null,cursorName:Y.name,cursorId:Y.id});
    searchFilteredComponents.mockRejectedValueOnce({body:{message:"Sem permissão"}});
    await nameSearch(el,"Outro");
    expect(el.shadowRoot.querySelector('[role="alert"]').textContent).toContain("Sem permissão");
  });
  it("sem dados distingue lista inicial e filtros sem correspondência",async()=>{
    searchFilteredComponents.mockResolvedValue({rows:[],hasMore:false});
    const el=mount();await flush();
    expect(text(el)).toContain("Nenhum componente acessível nesta consulta");
    await nameSearch(el,"xyz");
    expect(text(el)).toContain("Nenhum componente acessível corresponde");
  });
  it("limpa filtros e retorna ao inventário",async()=>{
    const el=mount();await flush();
    await nameSearch(el,"Flow");
    const clear=[...el.shadowRoot.querySelectorAll("lightning-button")].find(b=>b.label==="Limpar filtros");
    clear.click();await flush();
    expect(searchFilteredComponents).toHaveBeenLastCalledWith({
      search:null,componentType:null,cursorName:null,cursorId:null});
  });
  it("explora arquivo texto de ZIP sem tentar executar binários",async()=>{
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    const button=[...el.shadowRoot.querySelectorAll("lightning-button")].find(x=>x.label==="Explorar ZIP");
    expect(button).toBeDefined();button.click();await flush();
    expect(inspectHistoryArchive).toHaveBeenCalledWith({
      historyId:HISTORY.id,entryPath:null});
    expect(text(el)).toContain("classes/T_DefineFlowByObjectAPP.cls");
    const files=el.shadowRoot.querySelectorAll(".cd-archive-item");
    expect(files).toHaveLength(2);expect(files[1].disabled).toBe(true);
    inspectHistoryArchive.mockResolvedValueOnce({
      attachmentName:"ApexClass",matchingArchives:1,entries:[
        {path:"classes/T_DefineFlowByObjectAPP.cls",size:37,previewable:true}
      ],selectedPath:"classes/T_DefineFlowByObjectAPP.cls",text:"public class Foo {}"
    });
    files[0].click();await flush();
    expect(inspectHistoryArchive).toHaveBeenLastCalledWith({
      historyId:HISTORY.id,entryPath:"classes/T_DefineFlowByObjectAPP.cls"});
    expect(text(el)).toContain("public class Foo {}");
    el.shadowRoot.querySelector("lightning-button-icon[title='Fechar ZIP']").click();
    await flush();expect(el.shadowRoot.querySelector(".cd-archive-panel")).toBeNull();
  });
  it("expande a leitura do componente e retorna à lista sem nova consulta",async()=>{
    const el=mount();await flush();
    await nameSearch(el,"Flow");
    const previousCalls=searchFilteredComponents.mock.calls.length;
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();
    await flush();
    const expand=[...el.shadowRoot.querySelectorAll("lightning-button")].find(b=>b.label==="Expandir detalhes");
    expect(expand).toBeDefined();
    expand.click();await flush();
    expect(el.shadowRoot.querySelector(".cd-layout_focus")).not.toBeNull();
    expect(el.shadowRoot.querySelector(".cd-table")).toBeNull();
    const back=[...el.shadowRoot.querySelectorAll("lightning-button")].find(b=>b.label==="Voltar à lista");
    back.click();await flush();
    expect(el.shadowRoot.querySelector(".cd-layout_focus")).toBeNull();
    expect(el.shadowRoot.querySelectorAll(".cd-table tbody tr")).toHaveLength(2);
    expect(text(el)).toContain("T_DefineFlowByObjectAPP");
    expect(searchFilteredComponents).toHaveBeenCalledTimes(previousCalls);
  });
  it("filtra caminhos internos do ZIP no cliente sem recarregar anexo",async()=>{
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    const explore=[...el.shadowRoot.querySelectorAll("lightning-button")].find(b=>b.label==="Explorar ZIP");
    explore.click();await flush();
    expect(inspectHistoryArchive).toHaveBeenCalledTimes(1);
    const box=[...el.shadowRoot.querySelectorAll("lightning-input")]
      .find(x=>x.label==="Localizar arquivo no ZIP");
    expect(box).toBeDefined();
    box.value="T_Define";
    box.dispatchEvent(new CustomEvent("change"));await flush();
    expect(el.shadowRoot.querySelectorAll(".cd-archive-item")).toHaveLength(1);
    expect(inspectHistoryArchive).toHaveBeenCalledTimes(1);
    box.value="inexistente";
    box.dispatchEvent(new CustomEvent("change"));await flush();
    expect(text(el)).toContain("Nenhum arquivo corresponde ao filtro informado");
    box.value="";
    box.dispatchEvent(new CustomEvent("change"));await flush();
    expect(el.shadowRoot.querySelectorAll(".cd-archive-item")).toHaveLength(2);
  });

  it("organiza dados Flosum em ficha sem inferir deploy ou FullName", async()=>{
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    const facts=el.shadowRoot.querySelector(".cd-facts");
    expect(facts).not.toBeNull();
    expect(facts.querySelectorAll("dt")).toHaveLength(5);
    expect(facts.textContent).toContain("Snapshot 01");
    expect(facts.textContent).toContain("1.00");
    expect(facts.textContent).toContain("Branch SIT");
    expect(facts.textContent).toContain("não comprovam implantação");
    expect(text(el)).toContain("Component Histories relacionados");
    expect(text(el)).toContain("1 histórico nesta consulta");
    expect(text(el)).toContain("Histórico 1");
    expect(describeComponent).toHaveBeenCalledTimes(1);
  });
  it("enumera históricos sem alegar histórico global e destaca o ZIP aberto",async()=>{
    const later={id:"a0H00002",createdAt:"2026-10-23T10:00:00Z"};
    describeComponent.mockResolvedValue({...DETAIL,histories:[HISTORY,later],historiesHasMore:true});
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    expect(text(el)).toContain("2 históricos nesta consulta");
    expect(text(el)).toContain("Histórico 2");
    expect(text(el)).toContain("Mais registros existem além dos 20 históricos exibidos");
    const first=el.shadowRoot.querySelector(".cd-history-list .cd-history");
    expect(first.classList.contains("cd-history_selected")).toBe(false);
    [...first.querySelectorAll("lightning-button")].find(b=>b.label==="Explorar ZIP").click();
    await flush();
    expect(el.shadowRoot.querySelectorAll(".cd-history_selected")).toHaveLength(1);
    expect(inspectHistoryArchive).toHaveBeenCalledWith({historyId:HISTORY.id,entryPath:null});
    expect(describeComponent).toHaveBeenCalledTimes(1);
  });
  it("não exibe contagem fictícia quando acesso ao histórico está indisponível",async()=>{
    describeComponent.mockResolvedValue({...DETAIL,historyQuality:"UNAVAILABLE",histories:[]});
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    expect(el.shadowRoot.querySelector(".cd-history-count")).toBeNull();
    expect(text(el)).toContain("fonte histórica não está acessível");
  });

  it("encontra caminhos exatos e somente arquivos permitidos nos dois arquivos",()=>{
    const paths=commonPreviewPaths(
      {entries:[{path:"classes/Example.cls",previewable:true},
        {path:"images/logo.png",previewable:false},{path:"classes/OnlyBase.cls",previewable:true}]},
      {entries:[{path:"classes/Example.cls",previewable:true},
        {path:"classes/onlybase.cls",previewable:true},{path:"images/logo.png",previewable:false}]});
    expect(paths).toEqual(["classes/Example.cls"]);
  });
  it("calcula diff de linhas preservando diferenças e conteúdo literal",()=>{
    const output=lineDiff("same\nold", "same\nnew");
    expect(output).toMatchObject({added:1,removed:1,unchanged:false});
    expect(output.rows.map(x=>x.text)).toContain("old");
    expect(output.rows.map(x=>x.text)).toContain("new");
    expect(lineDiff("<script>", "<script>").unchanged).toBe(true);
    const longer=lineDiff("a\n".repeat(1000),"b");
    expect(longer.error).toBeUndefined();
    expect(longer.removed).toBe(1001);
    expect(longer.added).toBe(1);
  });
  it("compara dois ZIPs do mesmo Component e não expõe código como HTML",async()=>{
    const older={id:"a0H00002",createdAt:"2026-10-23T10:00:00Z"};
    describeComponent.mockResolvedValue({...DETAIL,histories:[HISTORY,older]});
    const common="classes/Example.cls";
    inspectHistoryArchive.mockImplementation(({historyId,entryPath})=>{
      if (!entryPath) return Promise.resolve({entries:[
        {path:common,previewable:true},
        {path:historyId===older.id?"only-old.cls":"only-new.cls",previewable:true},
        {path:"image.png",previewable:false}
      ]});
      return Promise.resolve({
        selectedPath:entryPath,
        text:historyId===older.id?"same\nold":'same\n<img src=x onerror=alert(1)>'
      });
    });
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    const compare=[...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Comparar históricos");
    expect(compare).toBeDefined();
    compare.click();await flush();
    expect(inspectHistoryArchive).toHaveBeenCalledWith({historyId:older.id,entryPath:null});
    expect(inspectHistoryArchive).toHaveBeenCalledWith({historyId:HISTORY.id,entryPath:null});
    const selector=[...el.shadowRoot.querySelectorAll("lightning-combobox")]
      .find(b=>b.label==="Arquivo de texto presente nos dois ZIPs");
    expect(selector.options).toEqual([{label:common,value:common}]);
    selector.dispatchEvent(new CustomEvent("change",{detail:{value:common}}));await flush();
    expect(text(el)).toContain("1 linhas adicionadas");
    expect(text(el)).toContain("1 linhas removidas");
    expect(text(el)).toContain("<img src=x onerror=alert(1)>");
    expect(el.shadowRoot.querySelector(".cd-diff-panes img")).toBeNull();
    expect(el.shadowRoot.querySelectorAll(".cd-diff-pane[data-side='base'] .cd-diff-cell")).toHaveLength(2);
    expect(text(el)).toContain("Não estabelece identidade canônica");
  });
  it("não disponibiliza comparação com apenas um History e respeita reset",async()=>{
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    expect([...el.shadowRoot.querySelectorAll("lightning-button")]
      .some(b=>b.label==="Comparar históricos")).toBe(false);
    expect(inspectHistoryArchive).not.toHaveBeenCalled();
  });

  it("alinha trocas de código em painéis distintos Base e Destino",()=>{
    const original=lineDiff("inicio\nlinha antiga\nfim", "inicio\nlinha nova\nfim");
    const rows=sideBySideDiff(original);
    expect(rows).toHaveLength(3);
    expect(rows[0]).toMatchObject({changed:false,left:{text:"inicio"},right:{text:"inicio"}});
    expect(rows[1]).toMatchObject({
      changed:true,
      left:{text:"linha antiga",line:2},
      right:{text:"linha nova",line:2}
    });
    expect(rows[1].left.className).toContain("removed");
    expect(rows[1].right.className).toContain("added");
    expect(rows[2].changed).toBe(false);
  });
  it("suporta arquivo apenas adicionado e Diff idêntico",()=>{
    const added=sideBySideDiff(lineDiff("inicio","inicio\nnova"));
    expect(added[1].left.className).toContain("empty");
    expect(added[1].right.text).toBe("nova");
    const equal=sideBySideDiff(lineDiff("sem mudancas","sem mudancas"));
    expect(equal.every(x=>!x.changed)).toBe(true);
  });
  it("mostra apenas alterações e permite inverter os históricos mantendo restrição de escopo",async()=>{
    const older={id:"a0H00002",createdAt:"2026-10-23T10:00:00Z"};
    describeComponent.mockResolvedValue({...DETAIL,histories:[HISTORY,older]});
    const common="classes/Example.cls";
    inspectHistoryArchive.mockImplementation(({historyId,entryPath})=>Promise.resolve(
      entryPath
        ? {selectedPath:entryPath,text:historyId===older.id?"inicio\nantigo":"inicio\nnovo"}
        : {entries:[{path:common,previewable:true}]}
    ));
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    const compare=[...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Comparar históricos");
    compare.click();await flush();
    expect(el.shadowRoot.querySelector(".cd-layout_focus")).not.toBeNull();
    expect(el.shadowRoot.querySelectorAll(".cd-compare-selectors lightning-combobox")).toHaveLength(2);
    const file=el.shadowRoot.querySelector(".cd-compare-file lightning-combobox");
    file.dispatchEvent(new CustomEvent("change",{detail:{value:common}}));await flush();
    expect(el.shadowRoot.querySelectorAll(".cd-diff-pane[data-side='base'] .cd-diff-cell")).toHaveLength(2);
    const only=[...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Apenas alterações");
    only.click();await flush();
    expect(el.shadowRoot.querySelectorAll(".cd-diff-pane[data-side='base'] .cd-diff-cell")).toHaveLength(1);
    const all=[...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Lado a lado");
    all.click();await flush();
    expect(el.shadowRoot.querySelectorAll(".cd-diff-pane[data-side='base'] .cd-diff-cell")).toHaveLength(2);
    el.shadowRoot.querySelector("lightning-button-icon[title='Inverter base e destino']").click();await flush();
    expect(inspectHistoryArchive).toHaveBeenCalledWith({historyId:HISTORY.id,entryPath:null});
    expect(inspectHistoryArchive).toHaveBeenCalledWith({historyId:older.id,entryPath:null});
  });

  it("usa uma única rolagem vertical e horizontais independentes, sem espelhar scrollTop",async()=>{
    const older={id:"a0H00002",createdAt:"2026-10-23T10:00:00Z"};
    describeComponent.mockResolvedValue({...DETAIL,histories:[HISTORY,older]});
    const common="classes/Example.cls";
    inspectHistoryArchive.mockImplementation(({historyId,entryPath})=>Promise.resolve(
      entryPath
        ? {selectedPath:entryPath,text:historyId===older.id?"inicio\\nante":"inicio\\ndepois"}
        : {entries:[{path:common,previewable:true}]}
    ));
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    const compare=[...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Comparar históricos");
    compare.click();await flush();
    el.shadowRoot.querySelector(".cd-compare-file lightning-combobox")
      .dispatchEvent(new CustomEvent("change",{detail:{value:common}}));await flush();
    const viewport=el.shadowRoot.querySelector(".cd-diff-viewport");
    const panes=el.shadowRoot.querySelectorAll(".cd-diff-pane");
    expect(viewport).not.toBeNull();
    expect(viewport.getAttribute("role")).toBe("region");
    expect(viewport.getAttribute("aria-label")).toContain("uma única rolagem vertical");
    expect(panes).toHaveLength(2);
    expect(viewport.contains(panes[0]) && viewport.contains(panes[1])).toBe(true);
    expect(panes[0].hasAttribute("onscroll")).toBe(false);
    expect(panes[1].hasAttribute("onscroll")).toBe(false);
    panes[0].scrollLeft=50;panes[1].scrollLeft=26;
    viewport.scrollTop=80;
    expect(panes[0].scrollLeft).toBe(50);
    expect(panes[1].scrollLeft).toBe(26);
    const left=panes[0].querySelectorAll(".cd-diff-cell");
    const right=panes[1].querySelectorAll(".cd-diff-cell");
    expect(left.length).toBe(right.length);
    expect(panes[0].textContent).toContain("ante");
    expect(panes[1].textContent).toContain("depois");
    const only=[...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Apenas alterações");
    only.click();await flush();
    expect(viewport.scrollTop).toBe(0);
  });
  it("mantém um placeholder por linha removida no lado oposto (regressão do print)",()=>{
    const before=["<fieldPermissions>","<enabled>true</enabled>","<pageAccesses>",
      "<apexPage>FileNotFound</apexPage>","<enabled>true</enabled>",
      "</pageAccesses>","<pageAccesses>","<apexPage>StoreParentPageOut</apexPage>"].join("\n");
    const after=["<fieldPermissions>","<enabled>true</enabled>","<pageAccesses>",
      "<apexPage>StoreParentPageOut</apexPage>"].join("\n");
    const pairs=sideBySideDiff(lineDiff(before,after));
    expect(pairs).toHaveLength(8);
    expect(pairs.filter(p=>p.right.className.includes("empty")).length).toBe(4);
    expect(pairs.every(p=>p.left && p.right && p.key)).toBe(true);
    expect(pairs[3].left.text).toContain("FileNotFound");
    expect(pairs[3].right.text).toBe("");
    expect(pairs[7].right.text).toContain("StoreParentPageOut");
  });
  it("navega da ficha aos históricos e ao ZIP, volta à lista sem perder filtros",async()=>{
    const el=mount();await flush();
    await nameSearch(el,"Flow");
    const initialCalls=searchFilteredComponents.mock.calls.length;
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    const expand=[...el.shadowRoot.querySelectorAll("lightning-button")].find(b=>b.label==="Expandir detalhes");
    expand.click();await flush();
    const nav=el.shadowRoot.querySelector(".cd-workspace-nav");
    expect(nav).not.toBeNull();
    expect(el.shadowRoot.querySelector(".cd-facts")).not.toBeNull();
    expect(el.shadowRoot.querySelector(".cd-history-list")).toBeNull();
    expect([...nav.querySelectorAll("lightning-button")].find(b=>b.label==="Arquivos ZIP").disabled).toBe(true);
    expect([...nav.querySelectorAll("lightning-button")].find(b=>b.label==="Comparar").disabled).toBe(true);
    [...nav.querySelectorAll("lightning-button")].find(b=>b.label==="Históricos").click();await flush();
    expect(el.shadowRoot.querySelector(".cd-history-list")).not.toBeNull();
    expect(el.shadowRoot.querySelector(".cd-facts")).toBeNull();
    const explore=[...el.shadowRoot.querySelectorAll("lightning-button")].find(b=>b.label==="Explorar ZIP");
    explore.click();await flush();
    expect(el.shadowRoot.querySelector(".cd-archive-panel")).not.toBeNull();
    expect(el.shadowRoot.querySelector(".cd-history-list")).toBeNull();
    expect(el.shadowRoot.querySelector(".cd-workspace-path").textContent).toContain("Arquivos ZIP");
    expect(el.shadowRoot.querySelector(".cd-archive-preview")).not.toBeNull();
    [...nav.querySelectorAll("lightning-button")].find(b=>b.label==="Históricos").click();await flush();
    expect(el.shadowRoot.querySelector(".cd-history-list")).not.toBeNull();
    el.shadowRoot.querySelector(".cd-workspace-path .cd-link").click();await flush();
    expect(el.shadowRoot.querySelectorAll(".cd-table tbody tr")).toHaveLength(2);
    expect(searchFilteredComponents).toHaveBeenCalledTimes(initialCalls);
    expect(describeComponent).toHaveBeenCalledTimes(1);
  });

  it("permite milhares de linhas sem limite fixo e navega por blocos alinhados",async()=>{
    const many=Array.from({length:740},(_,i)=>"linha "+i).join("\n");
    const original=many.replace("linha 650","linha antiga 650");
    const updated=many.replace("linha 650","linha nova 650");
    const result=lineDiff(original,updated);
    expect(result.error).toBeUndefined();
    expect(result.added).toBe(1);
    expect(result.removed).toBe(1);
    expect(result.rows.length).toBeGreaterThan(740);
    const pairs=sideBySideDiff(result);
    expect(pairs).toHaveLength(740);
    expect(pairs[650]).toMatchObject({left:{text:"linha antiga 650"},right:{text:"linha nova 650"}});

    const older={id:"a0H00002",createdAt:"2026-10-23T10:00:00Z"};
    describeComponent.mockResolvedValue({...DETAIL,histories:[HISTORY,older]});
    inspectHistoryArchive.mockImplementation(({historyId,entryPath})=>Promise.resolve(
      entryPath
        ? {selectedPath:entryPath,text:historyId===older.id?original:updated}
        : {entries:[{path:"classes/Example.cls",previewable:true}]}
    ));
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    [...el.shadowRoot.querySelectorAll("lightning-button")].find(b=>b.label==="Comparar históricos").click();
    await flush();
    el.shadowRoot.querySelector(".cd-compare-file lightning-combobox")
      .dispatchEvent(new CustomEvent("change",{detail:{value:"classes/Example.cls"}}));
    await flush();
    expect(el.shadowRoot.querySelectorAll(".cd-diff-pane[data-side='base'] .cd-diff-cell")).toHaveLength(250);
    expect(text(el)).toContain("Bloco 1 de 3");
    const next=[...el.shadowRoot.querySelectorAll("lightning-button")].find(b=>b.label==="Próximo bloco");
    next.click();await flush();
    expect(text(el)).toContain("Bloco 2 de 3");
    next.click();await flush();
    expect(text(el)).toContain("Bloco 3 de 3");
    expect(text(el)).toContain("linha nova 650");
  });


  it("V3.3: apresenta skeleton acessível durante consulta pendente", async () => {
    searchFilteredComponents.mockImplementationOnce(() => new Promise(() => {}));
    const el=mount(); await flush();
    expect(el.shadowRoot.querySelector(".cd-loading_skeleton")).not.toBeNull();
    expect(el.shadowRoot.querySelector(".cd-skeleton[aria-hidden='true']")).not.toBeNull();
  });

  it("V3.3: recupera pesquisa com erro sem recarregar a página", async () => {
    searchFilteredComponents.mockRejectedValueOnce({body:{message:"Falha de leitura"}});
    const el=mount(); await flush();
    expect(el.shadowRoot.querySelector(".cd-state_error")).not.toBeNull();
    expect(text(el)).toContain("Falha de leitura");
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Tentar pesquisa novamente").click();
    await flush();
    expect(searchFilteredComponents).toHaveBeenCalledTimes(2);
    expect(el.shadowRoot.querySelectorAll(".cd-table tbody tr")).toHaveLength(2);
  });

  it("V3.3: permite reconsultar ficha após erro de acesso", async () => {
    describeComponent.mockRejectedValueOnce({body:{message:"Acesso negado"}});
    const el=mount(); await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click(); await flush();
    expect(text(el)).toContain("Não foi possível carregar a ficha");
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Tentar carregar ficha novamente").click();
    await flush();
    expect(describeComponent).toHaveBeenCalledTimes(2);
    expect(el.shadowRoot.querySelector(".cd-facts")).not.toBeNull();
  });

  it("V3.3: diferencia ZIP sem arquivos textuais de ZIP sem entradas", async () => {
    inspectHistoryArchive.mockResolvedValueOnce({
      attachmentName:"only-binary.zip",
      entries:[{path:"images/photo.png",previewable:false}],selectedPath:null,text:null
    });
    const el=mount(); await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click(); await flush();
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Explorar ZIP").click(); await flush();
    expect(text(el)).toContain("ZIP sem texto compatível");
    expect(el.shadowRoot.querySelector(".cd-archive-preview")).toBeNull();
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Voltar aos históricos").click(); await flush();
    expect(el.shadowRoot.querySelector(".cd-archive-panel")).toBeNull();
  });

  it("V3.3: permite limpar filtro ZIP sem repetir leitura do anexo", async () => {
    const el=mount(); await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click(); await flush();
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Explorar ZIP").click(); await flush();
    const input=[...el.shadowRoot.querySelectorAll("lightning-input")]
      .find(b=>b.label==="Localizar arquivo no ZIP");
    input.value="arquivo-que-nao-existe";
    input.dispatchEvent(new CustomEvent("change")); await flush();
    expect(text(el)).toContain("Nenhum arquivo corresponde ao filtro");
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Limpar filtro do ZIP").click(); await flush();
    expect(el.shadowRoot.querySelectorAll(".cd-archive-item")).toHaveLength(2);
    expect(inspectHistoryArchive).toHaveBeenCalledTimes(1);
  });

  it("V3.3: repete a leitura do mesmo caminho ZIP após falha", async () => {
    const el=mount(); await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click(); await flush();
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Explorar ZIP").click(); await flush();
    const path="classes/T_DefineFlowByObjectAPP.cls";
    inspectHistoryArchive.mockRejectedValueOnce({body:{message:"Limite de heap atingido"}});
    inspectHistoryArchive.mockResolvedValueOnce({
      attachmentName:"ApexClass",entries:[{path,previewable:true}],
      selectedPath:path,text:"public class RetryOk {}"
    });
    el.shadowRoot.querySelector(".cd-archive-item").click(); await flush();
    expect(text(el)).toContain("Limite de heap atingido");
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Tentar abrir ZIP novamente").click(); await flush();
    expect(inspectHistoryArchive).toHaveBeenLastCalledWith({historyId:HISTORY.id,entryPath:path});
    expect(text(el)).toContain("public class RetryOk {}");
  });

  it("V3.3: tenta novamente consulta dos ZIPs para Diff sem mudar os históricos", async () => {
    const older={id:"a0H00002",createdAt:"2026-10-23T10:00:00Z"};
    describeComponent.mockResolvedValue({...DETAIL,histories:[HISTORY,older]});
    inspectHistoryArchive.mockRejectedValueOnce({body:{message:"Consulta temporariamente indisponível"}});
    const el=mount(); await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click(); await flush();
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Comparar históricos").click(); await flush();
    expect(text(el)).toContain("Consulta temporariamente indisponível");
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Reconsultar arquivos para comparação").click(); await flush();
    expect(el.shadowRoot.querySelector(".cd-compare-file lightning-combobox")).not.toBeNull();
    expect(inspectHistoryArchive).toHaveBeenCalledTimes(4);
  });


  it("V3.4: em tela estreita abre a ficha focada e volta ao inventário sem nova busca",async()=>{
    const original=window.matchMedia;
    window.matchMedia=jest.fn().mockImplementation(query=>({matches:query==="(max-width: 48rem)"}));
    try {
      const el=mount();await flush();
      const searchCount=searchFilteredComponents.mock.calls.length;
      el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
      expect(window.matchMedia).toHaveBeenCalledWith("(max-width: 48rem)");
      expect(el.shadowRoot.querySelector(".cd-layout_focus")).not.toBeNull();
      expect(el.shadowRoot.querySelector(".cd-workspace-nav")).not.toBeNull();
      expect(el.shadowRoot.querySelector(".cd-table")).toBeNull();
      el.shadowRoot.querySelector(".cd-workspace-path .cd-link").click();await flush();
      expect(el.shadowRoot.querySelectorAll(".cd-table tbody tr")).toHaveLength(2);
      expect(searchFilteredComponents).toHaveBeenCalledTimes(searchCount);
    } finally {
      window.matchMedia=original;
    }
  });

  it("V3.4: mobile alterna Base/Destino sem perder linhas, paginação ou rolagem vertical",async()=>{
    const older={id:"a0H00002",createdAt:"2026-10-23T10:00:00Z"};
    describeComponent.mockResolvedValue({...DETAIL,histories:[HISTORY,older]});
    const path="classes/Example.cls";
    inspectHistoryArchive.mockImplementation(({historyId,entryPath})=>Promise.resolve(
      entryPath
        ? {selectedPath:entryPath,text:historyId===older.id?"igual\nbase":"igual\ndestino"}
        : {entries:[{path,previewable:true}]}
    ));
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(b=>b.label==="Comparar históricos").click();await flush();
    el.shadowRoot.querySelector(".cd-compare-file lightning-combobox")
      .dispatchEvent(new CustomEvent("change",{detail:{value:path}}));await flush();
    const viewport=el.shadowRoot.querySelector(".cd-diff-viewport");
    const controls=el.shadowRoot.querySelectorAll(".cd-mobile-compare-switch button");
    expect(controls).toHaveLength(2);
    expect(controls[0].getAttribute("aria-pressed")).toBe("true");
    expect(controls[1].getAttribute("aria-pressed")).toBe("false");
    expect(el.shadowRoot.querySelectorAll(".cd-diff-pane[data-side='base'] .cd-diff-cell")).toHaveLength(2);
    expect(el.shadowRoot.querySelectorAll(".cd-diff-pane[data-side='target'] .cd-diff-cell")).toHaveLength(2);
    viewport.scrollTop=70;
    controls[1].click();await flush();
    expect(viewport.scrollTop).toBe(70);
    expect(controls[1].getAttribute("aria-pressed")).toBe("true");
    expect(el.shadowRoot.querySelector(".cd-diff-col_mobile-hidden .cd-diff-pane[data-side='base']")).not.toBeNull();
    expect(el.shadowRoot.querySelector(".cd-diff-pane[data-side='target']").textContent).toContain("destino");
    expect(inspectHistoryArchive).toHaveBeenCalledTimes(4);
    controls[0].click();await flush();
    expect(el.shadowRoot.querySelector(".cd-diff-col_mobile-hidden .cd-diff-pane[data-side='target']")).not.toBeNull();
    expect(el.shadowRoot.querySelector(".cd-diff-pane[data-side='base']").textContent).toContain("base");
    expect(viewport.scrollTop).toBe(70);
  });


  it("V3.5: classifica caminhos comuns, exclusivos e indisponíveis sem inferir igualdade",()=>{
    const inventory=archivePathInventory({
      entries:[{path:"classes/shared.cls",previewable:true},
        {path:"classes/old.cls",previewable:true},{path:"images/logo.png",previewable:false}]
    },{
      entries:[{path:"classes/shared.cls",previewable:true},
        {path:"classes/new.cls",previewable:true},{path:"images/logo.png",previewable:false}]
    });
    expect(inventory.counts).toEqual({common:1,base:1,target:1,blocked:1});
    expect(inventory.rows.find(x=>x.path==="classes/shared.cls").label)
      .toContain("conteúdo ainda não comparado");
    expect(inventory.rows.map(x=>x.path)).toEqual([
      "classes/new.cls","classes/old.cls","classes/shared.cls","images/logo.png"
    ]);
    expect(inventory.rows.find(x=>x.path==="images/logo.png").status).toBe("blocked");
    expect(archivePathInventory({entries:[{path:"same.cls",previewable:true},
      {path:"same.cls",previewable:true}]},{entries:[{path:"same.cls",previewable:true}]}).counts.blocked).toBe(1);
  });

  it("V3.5: apresenta inventário e permite filtrar caminhos sem ler os arquivos",async()=>{
    const old={id:"a0H00002",createdAt:"2026-10-23T10:00:00Z"};
    describeComponent.mockResolvedValue({...DETAIL,histories:[HISTORY,old]});
    inspectHistoryArchive.mockImplementation(({historyId,entryPath})=>Promise.resolve(
      entryPath ? {selectedPath:entryPath,text:"Conteúdo só deve ser lido após seleção"} :
      {entries: historyId===old.id ?
        [{path:"classes/shared.cls",previewable:true},{path:"classes/deleted.cls",previewable:true},
          {path:"binary/blob.bin",previewable:false}] :
        [{path:"classes/shared.cls",previewable:true},{path:"classes/new.cls",previewable:true},
          {path:"binary/blob.bin",previewable:false}]}
    ));
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(x=>x.label==="Comparar históricos").click();await flush();
    const index=el.shadowRoot.querySelector(".cd-zip-index");
    expect(index).not.toBeNull();
    expect(index.querySelectorAll(".cd-zip-index-row")).toHaveLength(4);
    expect(index.textContent).toContain("1 somente base");
    expect(index.textContent).toContain("1 somente destino");
    expect(index.textContent).toContain("1 indisponíveis");
    expect(el.shadowRoot.querySelectorAll(".cd-compare-file lightning-combobox")).toHaveLength(1);
    expect(inspectHistoryArchive).toHaveBeenCalledTimes(2);
    const filter=index.querySelector("lightning-combobox");
    filter.dispatchEvent(new CustomEvent("change",{detail:{value:"base"}}));await flush();
    expect(index.querySelectorAll(".cd-zip-index-row")).toHaveLength(1);
    expect(index.textContent).toContain("classes/deleted.cls");
    filter.dispatchEvent(new CustomEvent("change",{detail:{value:"target"}}));await flush();
    expect(index.textContent).toContain("classes/new.cls");
    expect(index.textContent).not.toContain("classes/deleted.cls");
    filter.dispatchEvent(new CustomEvent("change",{detail:{value:"common"}}));await flush();
    expect(index.querySelectorAll(".cd-zip-index-row")).toHaveLength(1);
    expect(index.textContent).toContain("classes/shared.cls");
    expect(inspectHistoryArchive).toHaveBeenCalledTimes(2);
    el.shadowRoot.querySelector(".cd-compare-file lightning-combobox")
      .dispatchEvent(new CustomEvent("change",{detail:{value:"classes/shared.cls"}}));await flush();
    expect(inspectHistoryArchive).toHaveBeenCalledTimes(4);
    expect(el.shadowRoot.querySelector(".cd-diff-viewport")).not.toBeNull();
  });

  it("V3.5: sem caminhos comuns ainda exibe os exclusivos sem abrir conteúdo",async()=>{
    const old={id:"a0H00002",createdAt:"2026-10-23T10:00:00Z"};
    describeComponent.mockResolvedValue({...DETAIL,histories:[HISTORY,old]});
    inspectHistoryArchive.mockImplementation(({historyId})=>Promise.resolve({
      entries:[{path:historyId===old.id?"old/a.cls":"new/b.cls",previewable:true}]
    }));
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(x=>x.label==="Comparar históricos").click();await flush();
    expect(el.shadowRoot.querySelector(".cd-zip-index")).not.toBeNull();
    expect(text(el)).toContain("Nenhum caminho está disponível para comparação textual");
    expect(el.shadowRoot.querySelector(".cd-compare-file")).toBeNull();
    expect(el.shadowRoot.querySelectorAll(".cd-zip-index-row")).toHaveLength(2);
    expect(inspectHistoryArchive).toHaveBeenCalledTimes(2);
  });

  it("V3.5: mantém a lista de arquivos ao selecionar um ZIP com resposta só de conteúdo",async()=>{
    const el=mount();await flush();
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    [...el.shadowRoot.querySelectorAll("lightning-button")]
      .find(x=>x.label==="Explorar ZIP").click();await flush();
    expect(el.shadowRoot.querySelectorAll(".cd-archive-item")).toHaveLength(2);
    inspectHistoryArchive.mockResolvedValueOnce({
      selectedPath:"classes/T_DefineFlowByObjectAPP.cls",text:"public class MyClass {}"
    });
    el.shadowRoot.querySelector(".cd-archive-item").click();await flush();
    expect(el.shadowRoot.querySelectorAll(".cd-archive-item")).toHaveLength(2);
    expect(text(el)).toContain("public class MyClass {}");
  });

});
