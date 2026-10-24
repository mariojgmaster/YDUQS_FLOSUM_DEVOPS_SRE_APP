# MVP-01 — Registro manual de incidentes (preparado, não implantado)

## Decisão do processo (aprovada)

- A equipe de DevOps/SRE cadastra incidentes manualmente no Salesforce.
- Causalidade não é inferida por automação; operador não tem escrita em `CauseType__c` ou `CauseReviewStatus__c`.
- Os **RMs DevOps** são revisores iniciais da causa; confirmação COE é evolução futura. A revisão de deployment ainda requer vínculo verificado antes de qualquer DORA.
- Esta entrega não implementa `DevSre_IncidentDeployment__c`, `DevSre_MeasurementCoverage__c` nem qualquer KPI.

## Entregue no código (somente GitHub)

- Objetos: `DevSre_Incident__c` (AutoNumber INC) e `DevSre_RecoveryAction__c` (AutoNumber REC).
- Campos de contexto, datas de impacto/restauração/encerramento, Status e severidade; tipos de ações e datas.
- Regras de validação: restauração após impacto, restauração necessária para fechar, conclusão da ação após início.
- Auditoria: CreatedBy/Date, LastModifiedBy/Date, enableHistory e trackHistory para campos críticos.
- Permissões: `DevSreIncident_Operator` (cadastro/edição no próprio escopo), `DevSreIncident_Reader` (leitura); OWD Private, sem delete, sem elevação para todos os registros.
- LWC `devSreIncidentIntake` com cadastro via `lightning-record-edit-form` / Lightning Data Service, listagem via Apex seguro, ações vinculadas, pesquisa, refresh e navegação.
- Tab Lightning `DevSre_Incident_Intake`. Adicionar no App Manager depois da implantação homologada.
- Todos os registros novos têm `Source=Manual`, `CauseType=Unconfirmed`, `CauseReviewStatus=Pending` como defaults. Operadores não podem escrever em causalidade.

## Testes locais/CI planejados

```bash
npm ci --ignore-scripts --no-audit --no-fund
npx eslint force-app/main/default/lwc/devSreIncidentIntake/devSreIncidentIntake.js
npm run test:unit -- -- --runInBand --runTestsByPath force-app/main/default/lwc/devSreIncidentIntake/__tests__/devSreIncidentIntake.test.js
```

## Sandbox DevSreFeat — NÃO executado neste PR

- Ambiente: `DevSreFeat`, `sf-devsrefeat-read` no catálogo da `master`. O fato de estar catalogado **não comprova permissões nem disponibilidade atual de secrets**.
- Revisar manifesto `manifest/sf-devops-sre-incident-intake.xml`, dependências CustomObject/CustomField/ValidationRule, Package XML e SHA após merge.
- Validar compile/test `DevSreIncidentControllerTest` via workflow autorizado ou Salesforce CLI, **sem deploy** nesta etapa. O fluxo de M4 ainda NÃO possui allowlist para esta nova feature.
- Para deploy futuro, autorização explícita de escrita na sandbox, validação no mesmo fluxo e aprovação de metadata e estratégia de rollback.
- Verificar Reader/Operator com contas reais, FLS dos campos de causalidade, visibilidade Private, timestamps/regras, layout SLDS 2/Cosmos e comportamento do App Manager.
- O catálogo de serviços ainda falta: `ServiceKey__c` é provisório e **não autoriza** consolidação de DORA.

## Riscos que impedem homologação

1. OWD Private exige regra de compartilhamento ou processo de atribuição quando múltiplos operadores precisam colaborar num incidente.
2. O papel revisor está definido como RM DevOps; ainda falta política de sharing, vínculo Flosum e certificação de cobertura.
3. Field History Tracking padrão tem limites/retenção próprios; a auditoria formal pode requerer política de retenção adicional.
4. O CustomObject XML e os testes Apex precisam de validação contra a versão instalada na org. Ninguém afirmou que a metadata já compilou ou foi instalada.

## MVP-02 / permissão de revisor e testes

- Atribuir `DevSreIncident_Operator` + `DevSreIncident_RMReviewer` apenas a RMs aprovados. Não atribuir o segundo a operadores de rotina.
- Confirmar `$Permission.DevSre_ReviewIncidentCausality` e FLS `Cause*` em usuário real; não basta ocultar botão.
- Validar casos: operador tenta alterar causa via API (falha), incidente novo com causa não-pendente (falha), RM confirma `Other` com justificativa (sucesso), sem justificativa (falha), qualquer usuário confirma `DeploymentRelated` (falha).
- Confirmar que o objeto continua `Private`, e providenciar compartilhamento controlado para RMs conforme a política a aprovar; Permission Set não cria sharing.
- O manifesto novo `manifest/sf-devops-sre-rm-review.xml` é candidato a **validate** posterior. Não está na allowlist M4; nenhum deploy foi realizado.

## Homologação mandatória para cada incremento

1. Antes de alegar compilação/homologação, executar **Salesforce DevSreFeat - Incident Validation** em Actions → Run workflow → branch `master`; este workflow faz apenas dry-run e Apex tests, e não faz deploy.
2. Publicar o URL/ID da execução e o SHA de origem; analisar as falhas sem divulgar payloads protegidos (repositório público).
3. Uma implantação real na sandbox, quando autorizada separadamente, precisa atribuir `DevSreIncident_Operator` aos RMs e adicionar esses usuários ao Public Group `DevSre_Incident_RMs` (a associação de usuários não viaja em metadata).
4. Testar acesso a incidentes de outro membro e recusa de um não-membro; checar FLS de causa, histórico e status `DeploymentRelated + Confirmed` bloqueado.
5. Nenhuma aprovação do COE é exigida neste MVP.

**Status até haver execução de run:** código em GitHub não é validação Salesforce. Não declarar concluído.
