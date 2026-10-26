import {createElement} from "lwc";
import Describer from "c/devSreComponentDescriber";
import searchFilteredComponents from "@salesforce/apex/DevSreComponentDescriberController.searchFilteredComponents";
import getComponentTypes from "@salesforce/apex/DevSreComponentDescriberController.getComponentTypes";
import describeComponent from "@salesforce/apex/DevSreComponentDescriberController.describeComponent";
import inspectHistoryArchive from "@salesforce/apex/DevSreComponentDescriberController.inspectHistoryArchive";

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
});
