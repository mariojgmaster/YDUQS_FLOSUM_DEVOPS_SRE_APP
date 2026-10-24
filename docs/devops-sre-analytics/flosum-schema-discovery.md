# Inventário Flosum — descoberta controlada das fontes de deployment

**Situação inicial (24/10/2026):** o Pipeline Monitor conhece apenas `Flosum__Pipeline__c` e `Flosum__PipelineStep__c`, que são **configuração**, não execuções. A fundação de incidentes está homologada na `DevSreFeat` (deploy #40124487168 e limpeza #40128322847), mas não há contrato validado para métricas DORA.

## Incremento atual: descoberta sem leitura de registros

Sem criar outro workflow, a operação `flosum-schema-inventory` foi adicionada a `.github/workflows/sf-devsrefeat-diagnostics.yml`, reutilizando o Environment `sf-devsrefeat-read` e ECA/JWT existentes.

1. Ler **somente nomes técnicos dos objetos customizados** por `sf sobject list --sobject custom`, com saída JSON mantida em memória do runner; selecionar apenas objetos de namespaces `Flosum__` ou `git__` que tenham indícios de execução, release, commit, branch, mudança ou ambiente.
2. Descrever no máximo **seis objetos por categoria** (36 no total), por `sf sobject describe`, estritamente metadados, jamais `SELECT`, DML, deploy, triggers ou registros Flosum.
3. Logs **públicos sanitizados**: contagens, slots por categoria e marcadores booleanos de campos de lifecycle, ambiente, timestamp, commit e release. Não publicar nomes reais de objetos/campos da org, IDs, labels, usuários, valores, fonte Apex ou payload bruto. Falhas e schema desconhecido não são convertidos em zero elegível.
4. A operação nunca certifica KPI; `metric_status=NOT_MEASURABLE` até validar fonte, identidade, timestamps, ambiente PROD, relação commit-deployment, completude e reconciliação.
5. Autorização: execução manual em `master` pelo owner ou Issue owner criada no repositório com título e corpo fixos:
   - Title: `SDOA INVENTORY DevSreFeat Flosum`
   - Body: `SDOA-FLOSUM-SCHEMA/1\noperation=inventory\ntarget=DevSreFeat`
   - O workflow executa **somente leitura**, sem novo workflow, sem privilégios ampliados.

## Critérios para a próxima fase

- [ ] CI dos parser/guardrails PASS e PR mesclado na `master` protegida.
- [ ] Run real conclui e divulga somente sinalização sanitizada do inventário.
- [ ] Se há candidatos, cruzar o inventário com contratos documentados da versão Flosum e identificar **fonte de deployments efetivamente concluídos em PROD**, timestamps auditáveis, tipo de operação, relações com commit e serviço.
- [ ] Confirmar permissão/visibilidade das fontes e responsável pela certificação do período.
- [ ] Somente então SPEC para coleta/correlação de deployments e fórmula DORA. Nenhuma inferência de KPI pelos Pipeline Steps.

## Restrições

Fonte incompleta ou desconhecida → **Não mensurável**. Não criar custom object paralelo sem decisão de domínio; não modificar Flosum nem PROD.
## Corrigir cancelamento por concorrência na primeira execução

A [Issue #89](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/issues/89) disparou o run [#40130022909](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40130022909), que terminou `cancelled` sem iniciar job. A hipótese técnica é colisão na fila compartilhada com os workflows `M5 ChatOps` e `Incident Validation`, também disparados pelo evento de Issue. O diagnóstico **somente leitura** passa a usar grupo de concorrência distinto `sf-devsrefeat-read-diagnostics` e `queue: max`, sem tocar nas filas de escrita/Metadata API.

Nova Issue e novo run devem comprovar a hipótese; a execução cancelada **não representa** inventário nem consulta Salesforce.

## Evidência objetiva da primeira execução — 24/10/2026

O [PR #88](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/pull/88) incorporou a descoberta limitada ao workflow de diagnóstico já existente. O [PR #90](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/pull/90) isolou a fila read-only, evitando cancelamento por eventos simultâneos de Issue.

**Run REAL:** [#40130263390](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40130263390), gatilho owner Issue [#91](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/issues/91), sandbox `DevSreFeat`, SHA `4007c34aeed6f6cca9875ad342932114fb3fd856`. Final `SUCCESS`, `PASS: FLOSUM_SCHEMA_OWNER_ISSUE_INTENT`, autenticação JWT confirmada, `PASS: FLOSUM_SCHEMA_READ_ONLY_INVENTORY`. Sem consulta de registros nem escrita de metadata.

| Papel heurístico | Candidatos no namespace Flosum/git | Schemas inspecionados | Falhas de describe |
| --- | ---: | ---: | ---: |
| Deployment | 8 | 6 | 0 |
| Release | 0 | 0 | 0 |
| Commit | 2 | 2 | 0 |
| Ambiente | 0 | 0 | 0 |
| Mudança/PR | 3 | 3 | 0 |
| Branch | 3 | 3 | 0 |
| **Total** | **16** | **14** | **0** |

**Sinais técnicos:** entre os seis schemas selecionados de deployment, o slot `deployment-03` apresenta campos indicativos de status/lifecycle, destino e referência a commit, **mas não apresenta sinal detectado de timestamp de execução/conclusão**. Outros slots possuem sinais incompletos. O inventário não inclui APIs de terceiros não prefixadas, nem objetos com nomes fora das heurísticas, não confirma cardinalidade dos registros, ambientes efetivos ou cobertura de produção. `Release=0` e `Ambiente=0` **não significam** ausência dessas entidades na organização; somente ausência de correspondência nos critérios deste inventário.

**Veredito vinculante:** `metric_status=NOT_MEASURABLE`. Não há justificativa para contar pipelines, steps, incidentes de teste ou demais configurações como deployments de produção.

**Próximo incremento mínimo (ainda pendente):** mapear de maneira controlada a identidade exata do candidato de execução, relações com ambiente/commit/release e o carimbo temporal de fim (ou fonte alternativa auditável), sem publicar nomes internos, payloads ou registros em logs do repo público. Confirmar com equipe Flosum a semântica dos campos e o conjunto elegível de deploys PROD; só então especificar a correlação com incidentes/serviços. Não criar indicadores prematuramente.


## Branch e Metadata Log: leitura direcionada (investigação 24/10/2026)

O proprietário confirmou que a entidade candidata para deployments PROD é `Flosum__Metadata_Log__c`, associada à `Flosum__Branch__c`, e forneceu um URL de uma Branch específica na `DevSreFeat`. A heurística anterior baseada em "deploy" no nome dos objetos era incompleta e não encontrou essa fonte.

**Próximo teste:** o workflow existente `Salesforce DevSreFeat - Diagnostico Seguro` recebe opção manual `flosum-branch-inspect` e input `branch_id` (15/18 caracteres). Não há Issue com o ID nem código hardcoded num GitHub público. O usuário proprietário é o único ator autorizado (workflow_dispatch, master, primeira tentativa).

O teste obtém o schema real dos objetos Branch e Metadata Log; recupera **somente uma Branch pelo ID fornecido**, com até duas referências por tipo (organização, Branch, Commit, Release, Pipeline); e, havendo uma única referência Metadata Log → Branch validada por `referenceTo`, lê até oito logs associados à Branch (status/timestamp limitados por tipos de metadados). Toda saída é sanitizada em contagens e sinais; nenhuma linha com IDs, nomes de registros ou valores de negócio, e nenhum DML/deploy.

**Ainda por validar:** API name do relacionamento real, se a referência é direta/indireta, existência de logs associados, status e timestamps semânticos de implantação, mapeamento da organização Salesforce/Flosum para ambientes `PROD/UAT/SIT/DEV`. Regras DORA **não** são liberadas por simples presença de schema ou linhas.
