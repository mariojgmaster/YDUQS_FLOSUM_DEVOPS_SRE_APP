# Contrato de entrada manual MVP-01

## Operador DevOps/SRE

Pode, se possuir `DevSreIncident_Operator` e acesso aos registros conforme sharing:
- Criar incidente com título, serviço informado (provisório), severidade, ambiente, status e horários conhecidos.
- Editar campos operacionais; não pode editar campos `CauseType__c`, `CauseReviewStatus__c`, `CauseJustification__c`.
- Registrar várias ações vinculadas ao incidente, identificando tipo e estado sem disparar Flosum.
- Consultar a fila e abrir a página nativa de registro.

Não pode: atestar vínculo causal, certificar cobertura, publicar indicadores DORA ou disparar rollback.

## Leitor

`DevSreIncident_Reader` dá permissão de leitura aos dois objetos e campos listados, **sem contornar OWD Private**. A criação por UI API deverá ser negada pelo servidor a usuários sem Create.

## Read APIs

- `DevSreIncidentController.listIncidents(searchTerm)` retorna até 50, `hasMore` e campos operacionais mais `CauseReviewStatus__c`.
- `DevSreIncidentController.listRecoveryActions(incidentId)` retorna até 100, `hasMore`, após verificar acesso ao incidente pai.
- Apex `with sharing`, acesso explícito CRUD/FLS e `WITH USER_MODE`.
- Erros sanitizados, sem stack ou IDs sensíveis; não usar cache Apex para essas consultas imperativas.

## Write APIs

- `lightning-record-edit-form` delega create/update à Lightning Data Service e aplica CRUD/FLS do usuário.
- Save com defaults Salesforce `Source=Manual`, `CauseType=Unconfirmed`, `CauseReviewStatus=Pending`.
- Nenhuma classe Apex de escrita ou atualização de objetos Flosum.
- Validações temporais no metadata do objeto, não apenas no browser.

## DORA

Qualquer contagem dessa fila pode ser exibida como **volumetria operacional da fila**, nunca como número certificado de falhas de deployment. KPI DORA: `Não mensurável` até cobertura e vínculos revisados.

## DevOps/SRE (RMs) — revisão causal (MVP-02)

- Recebe `DevSreIncident_Operator` (inclui a Custom Permission de revisão), com acesso a incidentes conforme compartilhamento Private.
- Custom Permission `DevSre_ReviewIncidentCausality` permite acessar os campos `CauseType__c`, `CauseReviewStatus__c`, `CauseJustification__c` via Lightning Data Service; não concede acesso amplo ou alteração em Flosum.
- Regra de validação impede qualquer alteração de campos de causa por usuários sem a Custom Permission; cadastro inicial sempre `Unconfirmed/Pending`.
- RM pode confirmar ou rejeitar classificação **não associada a deployment**, fornecendo justificativa auditável.
- `CauseType=DeploymentRelated` e `CauseReviewStatus=Confirmed` estão expressamente bloqueados para **todos**, inclusive RMs, até uma SPEC que confira vínculo real com implantação concluída em produção.
- Após mudança de revisão, a interface recarrega a consulta; alteração fica sujeita a auditoria do objeto.
- Confirmações do COE não são exigidas por este MVP.

## Retificação — RMs são toda a equipe DevOps/SRE

A mesma equipe registra, gere e revisa. Conceder `DevSreIncident_Operator` e pertencer ao `DevSre_Incident_RMs` são as duas condições necessárias para acesso operacional ao conjunto de incidentes, sem uma permissão de revisor separada. A Custom Permission `DevSre_ReviewIncidentCausality` está no permission set de Operador; regras no servidor protegem as alterações. COE não aprova nessa etapa. `DeploymentRelated + Confirmed` segue bloqueado.

`DevSreIncident_Reader` não recebe Custom Permission nem CRUD de escrita. Membership do grupo é gerenciada em Setup → Public Groups e não é codificada como usuário em metadata. É obrigatório testar sharing com pelo menos dois membros distintos e um não-membro. Sem membros, o sharing rule não concede visibilidade cruzada.
