# MVP-01 — Registro manual de incidentes (preparado, não implantado)

## Decisão do processo (aprovada)

- A equipe de DevOps/SRE cadastra incidentes manualmente no Salesforce.
- Causalidade não é inferida por automação; operador não tem escrita em `CauseType__c` ou `CauseReviewStatus__c`.
- Um vínculo causal só será usado em DORA após confirmação por revisor autorizado (método e pessoa exatos **a definir**).
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
2. O papel revisor, trilha de aprovação causal e modelo de deployment Flosum ainda estão em aberto.
3. Field History Tracking padrão tem limites/retenção próprios; a auditoria formal pode requerer política de retenção adicional.
4. O CustomObject XML e os testes Apex precisam de validação contra a versão instalada na org. Ninguém afirmou que a metadata já compilou ou foi instalada.
