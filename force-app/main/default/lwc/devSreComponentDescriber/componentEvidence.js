/**
 * SPEC-006 V3.6-A — source-constrained provenance for one Flosum Component.
 *
 * The Apex DTO currently provides a typed link to Branch and, when readable,
 * a sampled typed link to Component History. It does NOT establish canonical
 * Metadata FullName or bind a Metadata Log deployment to this Component.
 *
 * This classifier fails closed: future/unknown quality flags do not silently
 * upgrade evidence. Presentation-only; no data access or mutation.
 */
export function componentEvidence(detail) {
  if (!detail?.component?.id) return [];
  const component=detail.component;
  const typedHistory=detail.historyQuality==="TYPED_LINK_SAMPLE";
  const count=Array.isArray(detail.histories)?detail.histories.length:0;
  const limited=Boolean(detail.historiesHasMore);
  return [
    {
      key:"record",
      title:"Registro Flosum",
      status:"Confirmado na consulta",
      statusClass:"cd-evidence-status cd-evidence-status_confirmed",
      description:"O Id identifica este registro Flosum__Component__c acessível. Name é o número do registro, não o Metadata FullName."
    },
    {
      key:"branch",
      title:"Branch vinculada",
      status:component.branchId?"Vínculo tipado acessível":"Vínculo não confirmado",
      statusClass:component.branchId?"cd-evidence-status cd-evidence-status_confirmed":"cd-evidence-status",
      description:component.branchId?
        "A referência tipada à Flosum__Branch__c foi consultada com acesso do usuário. Não prova implantação ou ambiente de destino.":
        "O registro não expõe uma Branch acessível nesta consulta. Não é evidência de ausência de Branch em outras fontes."
    },
    {
      key:"history",
      title:"Component Histories",
      status:typedHistory?"Relação tipada consultada":"Fonte histórica indisponível",
      statusClass:typedHistory?"cd-evidence-status cd-evidence-status_confirmed":"cd-evidence-status",
      description:typedHistory?
        `${count} histórico(s) acessível(is) na consulta${limited?"; existem registros além da amostra":""}. A relação não comprova revisão Git nem deploy.`:
        "A relação de histórico não pôde ser lida; não afirmar que existem zero versões."
    },
    {
      key:"canonical",
      title:"FullName canônico",
      status:"Não verificado",
      statusClass:"cd-evidence-status",
      description:"Flosum__Component_Name__c, tipo, Source e versão são valores registrados. Esta API não devolve um Metadata FullName comprovado."
    },
    {
      key:"deploy",
      title:"Implantação em ambiente",
      status:"Não comprovada",
      statusClass:"cd-evidence-status",
      description:"Não há correlação validada com Flosum__Metadata_Log__c ou o destino da operação. Committed On, Version e Last Commit não provam deploy."
    }
  ];
}
