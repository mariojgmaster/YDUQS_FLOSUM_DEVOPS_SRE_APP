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
2. A revisão é realizada pela equipe DevOps/SRE (os RMs); ainda falta política de sharing, vínculo Flosum e certificação de cobertura.
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

## ChatOps de validação sem deploy (autonomia autorizada para a DevSreFeat)

O conector GitHub não oferece uma ação `workflow_dispatch` direta. Como o M5 já comprovou o disparo de GitHub Actions a partir de Issues do proprietário, este incremento habilita uma segunda solicitação **estritamente fixa** de validação, que o assistente pode criar pelo conector, consultar os runs e analisar os logs.

**Título exato da Issue:**
```text
SDOA VALIDATE DevSreFeat incident-intake
```

**Corpo exato:**
```text
SDOA-INCIDENT-VALIDATE/1
operation=validate
target=DevSreFeat
package_id=incident-intake
```

O workflow de `issues.opened` somente executa se o autor, ator e emissor da Issue forem o dono do repositório; ref `master`, SHA de checkout fixo, `run_attempt=1`, manifest fixo e ambiente JWT existente. A intenção é revalidada **também no job privilegiado**. Não aceita scripts, parâmetros de comando, manifests arbitrários, produção ou deployment. A Issue é pedido auditável, **não é prova de execução**: depois da criação, localizar o run, job e logs reais.

Se a integração do conector não produzir uma Issue como o proprietário ou se não houver run, usar o `workflow_dispatch` manual já existente; nunca inferir sucesso.

**Diagnóstico:** em falhas de dry-run, emitir `SDOA_M42_DRY_RUN_DIAG` com contagens agregadas e categorias enumeradas de erro; nenhum erro bruto ou identificador da org em logs de repositório público. O prefixo é do utilitário genérico M4 reutilizado, embora a operação seja a validação de incidentes. O diagnóstico mais detalhado segue disponível exclusivamente no Deployment Status da DevSreFeat.

O diagnóstico categórico também emite `INCIDENT_COMPONENT_DIAG: type=... category=... count=N`, onde o tipo vem de uma allowlist de metadados e a categoria é uma enumeração estática. **Nunca** expõe componentes de outras partes da org, erros brutos ou IDs de cliente; resultados detalhados ficam no Deployment Status da sandbox.

## Correções guiadas pelo Deployment Status #40053356943 (23/10/2026)

- Dez regras de validação não declaravam `fullName` na Metadata API. Foi adicionado o nome exato de cada regra conforme o caminho dos arquivos, sem alterar as fórmulas.
- A classe Apex `DevSreIncidentController` usava o identificador reservado `number`. O DTO passou a fornecer `recordNumber` para incidentes e ações; JS/LWC e testes atualizados.
- Dois Permission Sets tentavam declarar Field-Level Security para campos obrigatórios. A Salesforce rejeita esse metadado; eliminamos as permissões de campo referentes a `Title__c`, `ServiceKey__c` e `Incident__c`, mas **os três continuam obrigatórios** no schema, preservando a integridade.
- Os erros subsequentes no LWC e na classe de teste eram consequência provável da classe Apex inválida; validar novamente o conjunto antes de encerrar.
- Reforçado o CI com assertivas específicas que evitam essas regressões.
- A alteração fica em PR separado, sem deploy real. Após merge, solicitar novo dry-run via Issue ChatOps do proprietário e inspecionar o run Salesforce.

## Debug de falhas Apex: após component_errors=0

No dry-run #40054058870, todos os metadados passaram (`component_errors=0`), porém os testes Apex retornaram `test_errors=5`. O diagnóstico de componentes não pode revelar a causa dos testes. Foi acrescentado parser de `runTestResult.failures` que publica só categorias enumeradas e contagens agregadas (`INCIDENT_APEX_TEST_DIAG`) e nunca expõe usernames, IDs, mensagens/stack traces ou nomes de métodos em logs públicos.

## Fix dos testes Apex — API 67.0 (Deployment Details 0AfV900000Eh9nx)

- O `@TestSetup` falhava na linha de `insert incidents` com `fields being inaccessible` antes de qualquer método; por isso os cinco testes falhavam e a cobertura aparecia em 0%.
- Desde Summer '26 / API 67.0, **DML e SOQL sem modo explícito usam USER_MODE**. A ECA/JWT conectou como usuário de integração sem FLS suficiente para construir as fixtures.
- **Somente na classe de testes**: `Database.insert(..., AccessLevel.SYSTEM_MODE)` e `Database.update(..., false, AccessLevel.SYSTEM_MODE)`, com SOQL de preparação `WITH SYSTEM_MODE`. O teste preserva Validation Rules e verifica tanto o bloqueio da confirmação de deployment quanto a sequência temporal.
- Para testar consultas do controller **em usuário autorizado**, `@TestSetup` atribui temporariamente a `DevSreIncident_Operator` ao usuário de teste dentro de `System.runAs`, isolando PermissionSetAssignment (setup-object DML) dos objetos de negócio; dados test-only são revertidos após execução.
- O controller em produção não muda: `WITH USER_MODE`, `with sharing` e verificações CRUD/FLS seguem obrigatórios. Nenhuma permissão foi adicionada a usuários reais na org.
- CI protege os modos e as permissões e o processo precisa do novo `--dry-run` com Apex tests na DevSreFeat antes de chamar homologado.

## Diagnóstico seguro de métodos de teste Apex
O dry-run #40055155347 alcançou 3 testes aprovados e 2 falhas `OTHER_APEX_EXCEPTION`. O parser agora registra somente nomes de métodos que já existem na classe pública `DevSreIncidentControllerTest` e nomes de exceções de uma enumeração fechada, sem publicar mensagens, linhas de stack ou identificadores privados. Usar esse resultado para corrigir o contrato de acesso ou a asserção precisa, sem rebaixar `WITH USER_MODE` no controller.

## Testes de consulta na API 67 — DevSreFeat #40055376602

O controller compilou e 3 testes Apex passaram; os dois testes de consulta falharam com `AuraHandledException`. Os métodos chamavam o controller fora do contexto de `System.runAs`, apesar de o Permission Set ser atribuído em `@TestSetup`. Agora o grant de `DevSreIncident_Operator` é realizado **dentro de cada método de teste positivo**, e as chamadas reais são feitas em `System.runAs`. Isto exerce `WITH USER_MODE` com perfil operacional e não altera o controller nem acessos permanentes na org. Os testes negativos de parâmetros também usam o contexto de operador para não confundir falta de acesso com entrada inválida.
