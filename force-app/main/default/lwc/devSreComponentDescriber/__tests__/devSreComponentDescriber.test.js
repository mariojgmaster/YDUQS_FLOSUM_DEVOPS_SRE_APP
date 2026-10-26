import {createElement} from "lwc";
import Describer from "c/devSreComponentDescriber";
import searchComponents from "@salesforce/apex/DevSreComponentDescriberController.searchComponents";
import describeComponent from "@salesforce/apex/DevSreComponentDescriberController.describeComponent";
jest.mock("@salesforce/apex/DevSreComponentDescriberController.searchComponents",
  () => ({ default: jest.fn() }), { virtual: true });
jest.mock("@salesforce/apex/DevSreComponentDescriberController.describeComponent",
  () => ({ default: jest.fn() }), { virtual: true });
const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
const X={id:"a000001",name:"Flow_Componente",branchId:"a0B0001",branchName:"Branch SIT"};
const Y={id:"a000002",name:"Flow_Componente",branchId:"a0B0002",branchName:"Branch PROD"};
const PAGE={rows:[X,Y],hasMore:false,cursorName:Y.name,cursorId:Y.id,identityLevel:"REGISTERED_NAME_ONLY"};
const HISTORY={id:"a0H00001",createdAt:"2026-10-24T10:00:00Z"};
const DETAIL={component:X,histories:[HISTORY],historiesHasMore:false,
  historyQuality:"TYPED_LINK_SAMPLE",deployEvidenceQuality:"UNVERIFIED"};
function mount(){const el=createElement("c-dev-sre-component-describer",{is:Describer});document.body.appendChild(el);return el;}
function text(el){return el.shadowRoot.textContent;}
async function search(el,term){
  const input=el.shadowRoot.querySelector("lightning-input");input.value=term;
  input.dispatchEvent(new CustomEvent("change"));jest.advanceTimersByTime(350);await flush();
}
describe("Branch Monitor M2 — Component Describer tipado e transparente",()=>{
  beforeEach(()=>{jest.clearAllMocks();jest.useFakeTimers();
    searchComponents.mockResolvedValue(PAGE);describeComponent.mockResolvedValue(DETAIL);});
  afterEach(()=>{document.body.innerHTML="";jest.useRealTimers();});
  it("não consulta todo o Flosum sem pelo menos dois caracteres",async()=>{
    const el=mount();await flush();expect(searchComponents).not.toHaveBeenCalled();
    expect(text(el)).toContain("pelo menos 2 caracteres");await search(el,"a");
    expect(searchComponents).not.toHaveBeenCalled();
  });
  it("preserva componentes homônimos em branches distintas e não inventa deploy",async()=>{
    const el=mount();await search(el,"Flow_");
    expect(searchComponents).toHaveBeenCalledWith({search:"Flow_",cursorName:null,cursorId:null});
    expect(el.shadowRoot.querySelectorAll(".cd-table tbody tr")).toHaveLength(2);
    expect(text(el)).toContain("Branch SIT");expect(text(el)).toContain("Branch PROD");
    expect(text(el)).toContain("Não é possível afirmar");
  });
  it("consulta históricos vinculados por identidade de registro e não os chama versões",async()=>{
    const el=mount();await search(el,"Flow");
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    expect(describeComponent).toHaveBeenCalledWith({componentId:X.id});
    expect(text(el)).toContain("Component Histories relacionados");
    expect(text(el)).toContain("Abrir histórico Flosum");
    expect(text(el)).toContain("Não exibir histórico de deploy sem evidência direta");
  });
  it("apresenta estado indisponível em vez de zero históricos inventado",async()=>{
    describeComponent.mockResolvedValue({...DETAIL,historyQuality:"UNAVAILABLE",histories:[]});
    const el=mount();await search(el,"Flow");
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    expect(text(el)).toContain("fonte histórica não está acessível");
    expect(text(el)).not.toContain("Nenhum histórico acessível");
  });
  it("pesquisa com debounce, bloqueia termos longos e não repete páginas sem cursor",async()=>{
    const el=mount();await search(el,"Flow");
    const input=el.shadowRoot.querySelector("lightning-input");
    input.value="a".repeat(81);input.dispatchEvent(new CustomEvent("change"));
    jest.advanceTimersByTime(500);await flush();
    expect(searchComponents).toHaveBeenCalledTimes(1);
    expect(text(el)).toContain("até 80 caracteres");
  });
  it("suporta cursor, busca incremental e estados de falha",async()=>{
    searchComponents.mockResolvedValueOnce({...PAGE,hasMore:true});
    const el=mount();await search(el,"Flow");
    const more=[...el.shadowRoot.querySelectorAll("lightning-button")].find(x=>x.label==="Carregar mais");
    more.click();await flush();
    expect(searchComponents).toHaveBeenLastCalledWith({
      search:"Flow",cursorName:Y.name,cursorId:Y.id});
    searchComponents.mockRejectedValueOnce({body:{message:"Sem permissão"}});
    const input=el.shadowRoot.querySelector("lightning-input");
    input.value="Outro";input.dispatchEvent(new CustomEvent("change"));
    jest.advanceTimersByTime(350);await flush();
    expect(el.shadowRoot.querySelector('[role="alert"]').textContent).toContain("Sem permissão");
  });
  it("não mostra histórico se o detalhe falhar",async()=>{
    describeComponent.mockRejectedValueOnce({body:{message:"Histórico indisponível"}});
    const el=mount();await search(el,"Flow");
    el.shadowRoot.querySelector(".cd-table tbody tr .cd-link").click();await flush();
    expect(el.shadowRoot.querySelector('[role="alert"]').textContent).toContain("Histórico indisponível");
  });
});
