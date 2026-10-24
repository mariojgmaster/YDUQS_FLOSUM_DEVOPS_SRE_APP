# SPEC-003 — Registro de Incidentes e Recuperações, com governança de evidência

- **Data:** 2026-10-23
- **Status:** registro manual DevOps/SRE aprovado pelo responsável; primeiro incremento em implementação, ainda não homologado
- **Relacionamentos:** `docs/devops-sre-analytics/adr/ADR-001-incidentes-e-confiabilidade-dora.md`; [PR #34](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/pull/34) implementa o Pipeline Monitor em trabalho independente.
- **Objetivo:** estabelecer um registro Salesforce próprio de incidentes e respostas operacionais para habilitar futuras métricas DORA confiáveis sem falsificar a origem dos eventos.

## Contexto

Não existe hoje uma tabela de incidentes. O aplicativo precisa criar o registro próprio em Salesforce. **Decisão do responsável em 23/10/2026: cadastro inicial manual pela equipe DevOps/SRE, com revisão da relação entre incidente e deployment antes de seu uso em DORA.** A informação do Flosum sobre execuções e deployments em produção será integrada apenas após inventário de objetos e carimbos temporais. Este incremento NÃO implementa cálculo DORA nem deploy/rollback via Flosum.

## US1 — Registrar ocorrência operacional (P1)

Como operador DevOps/SRE, quero registrar incidente ocorrido com serviço/aplicação, severidade, status, início do impacto, data de detecção e descrição de impacto, para preservar a evidência auditável.

**Aceite:**
- Identificador único gerado pela plataforma (`INC-...`) e `CreatedBy/CreatedDate` / `LastModifiedBy/LastModifiedDate`.
- Data/hora de início de impacto diferente da data de detecção, pois nem sempre coincidem.
- Origem `Manual` no MVP e indicação `Causalidade não confirmada` por padrão.
- Não exigir ID de deploy no cadastro inicial; pode haver incidente não relacionado a mudança.
- Restringir tipo de informação em campos narrativos (não inserir dados pessoais/segredos).
- CRUD/FLS e sharing conforme persona; históricos de campos relevantes sujeitos a configuração e retenção.

## US2 — Registrar ações de resposta e restauração (P1)

Como operador, quero registrar uma ou mais ações tomadas (rollback, hotfix, fix forward, mitigação, outra), seu estado e horário, e o momento em que o serviço foi restaurado.

**Aceite:**
- Muitas ações podem apontar para um incidente; rollback é **uma ação**, não um tipo exclusivo de incidente.
- Status `Restaurado` exige `RestoredAt >= ImpactStartedAt` quando início conhecido; caso contrário registrar lacuna e bloquear uso em métricas.
- Uma ação concluída não prova, por si, recuperação do serviço nem sucesso do deployment.
- Salvar a evidência de quem lançou/revisou os registros e quando, incluindo alterações relevantes.

## US3 — Associar incidentes a deployments (P2; bloqueado por mapeamento Flosum)

Como revisor COE, quero associar explicitamente um incidente a um ou mais deployments de produção, diferenciando `causador`, `corretivo` e `relacionado`, com justificativa e estado de verificação.

**Aceite:**
- Relação muitos-para-muitos; associação causal só entra em DORA após confirmação por papel autorizado.
- ID/objeto-fonte de deployment e endpoint navegado são validados contra contrato real de Flosum, nunca URL arbitrária.
- Sem contrato confirmado: associação fica planejada / não mensurável, sem inventar registros.
- Múltiplos incidentes do mesmo deployment contam uma única vez no numerador de falha.

## US4 — Certificar cobertura e liberar métricas (P2; bloqueado por governança)

Como revisor COE, quero atestar a completude das fontes por serviço/período, para impedir relatórios com números enganosos.

**Aceite:**
- Registro de cobertura identifica serviço, janela, escopo de ambientes, fontes, lacunas, verificador, data e versão da regra.
- Dashboard respeita três estados: `Não mensurável`, `Parcial`, `Certificado`.
- `0 incidentes` não significa zero falhas até existir confirmação independente de abrangência.
- Reabertura/alteração significativa de incidente, vínculo ou deployment requer revisão da certificação.

## US5 — Interface Incidents & Rollbacks (P2)

**Operacional (padrão, SLDS 2):** fila de incidentes, indicadores de triagem (não confundir com DORA), filtros por status, severidade, serviço, responsável e período, criação/edição e registro de ações, link de evidência.

**Analítica (posterior):** trilha temporal do impacto, recuperação, ações e vínculos verificados; cobertura do período e qualidade por métrica. Não mostrar gráfico com dataset incompleto sem rotular o limite.

## Requisitos de segurança

- Configuração Salesforce padrão: sharing `Private` por padrão, Permission Sets por papel, Apex `with sharing` + User Mode/CRUD/FLS, nenhum acesso de gravação para persona somente leitura.
- Sem integração Flosum de escrita; não editar registros de pacote gerenciado para executar rollback.
- Auditar mudanças em status, causalidade, timestamps, fonte e classificação, com plano de retenção; avaliar limites do Field History Tracking.
- Detecção de duplicidade e regras de validação para timestamps e encerramento após definir processo operacional.
- Testes de permissão e de ausência de dados suficientes são **critérios de aceite**, não opcionais.

## Fora de escopo neste momento

- Criar incidentes automaticamente de falha de job, Step ou deploy.
- Exibir KPIs DORA consolidados sem reconciliação.
- Executar rollback, hotfix ou deploy a partir da aba.
- Importar histórico sem evidências verificáveis.
- Integrar sistemas ITSM externos não confirmados.

## Escopo do incremento funcional atual (MVP-01)

- Criar `DevSre_Incident__c` e `DevSre_RecoveryAction__c` e suas validações de dados temporais, sem criar vínculos de deployment ainda.
- Operadores DevOps/SRE: formulário manual com Lightning Data Service, consultas em Apex `WITH USER_MODE`, auditoria padrão e Field History Tracking para campos selecionados.
- Operadores **não podem editar campos de causalidade** por FLS; registros novos iniciam `CauseType=Unconfirmed` e `CauseReviewStatus=Pending`.
- Permissões: Permission Sets `DevSreIncident_Reader` e `DevSreIncident_Operator`, OWD Private; compartilhamento entre operadores/revisores requer decisão posterior.
- `ServiceKey__c` é texto **provisório**, sem autoridade como catálogo de serviços para DORA.
- Revisão causal por responsável distinto, vínculos com deployments e certificação continuam **bloqueados** pelo inventário de Flosum e desenho de papel revisor.
- Pacote específico sob `manifest/sf-devops-sre-incident-intake.xml`; nenhum deploy sem autorização posterior.

## DoD

- Aprovação do catálogo de serviços, papéis operacionais e contrato dos deployments de produção.
- Metadados criados e testes implementados em PR distinto; lint/CI, validação Salesforce e autorização explícita antes de qualquer deploy.
- Interface Lightning usável e homologada com dados de teste em sandbox, sem números sintéticos apresentados como produção.
- Fluxo de registro→resposta→revisão causal→certificação verificado por personas reais.
