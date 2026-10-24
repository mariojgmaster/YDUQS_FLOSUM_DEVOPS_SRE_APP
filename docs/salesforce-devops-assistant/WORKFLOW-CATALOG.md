# Catálogo de workflows aprovados — Salesforce DevOps/SRE

> Política operacional M5: o ChatOps **não cria arquivos de workflows**. Somente utiliza os entrypoints já versionados e revisados neste repositório. É proibido gerar YAML para atender a uma solicitação operacional, registrar triggers alternativos, contornar gates ou improvisar jobs dinâmicos. Evoluções estruturais de workflows existentes exigem solicitação de desenvolvimento específica, PR, revisão e CI.

## Fonte de verdade e contexto

- Repo: `mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP`.
- Branch de operação: `master` no SHA exato e atual.
- Salesforce: sandbox cadastrada `DevSreFeat` e os pacotes revisados no `config/salesforce-devops/catalog.json`.
- Credenciais: **GitHub Environment existente** `sf-devsrefeat-read`, nunca expostas no ChatGPT ou nas Issues.
- O repositório é **público**: nenhum JSON bruto da Salesforce, segredo, ID pessoal ou stack trace confidencial nos logs/artefatos.
- "Executável pelo ChatOps" depende das ações realmente presentes no conector; `workflow_dispatch` **não está exposto** como invocação direta. Não inventar atalhos.

## Operações prioritárias para uso diário

| Pedido operacional | Workflow existente | Disparo efetivo | O que entrega |
|---|---|---|---|
| PLAN / dry-run de pacote cadastrado | `.github/workflows/sf-m5-chatops-plan.yml` | Issue estrita `SDOA PLAN` criada pelo proprietário | Dry-run + testes Apex e artefato diagnóstico seguro; **nenhuma escrita** |
| DEPLOY real expressamente solicitado, de pacote cadastrado | Mesmo `sf-m5-chatops-plan.yml` | Issue estrita `SDOA DEPLOY`, com confirmação e SHA da master | Dry-run + testes + deploy, somente sandbox. Não repetir deploy automaticamente |
| PLAN ou DEPLOY manual de contingência | `.github/workflows/sf-universal-m4.yml` | `workflow_dispatch` manual na UI GitHub | Mesmas validações de Salesforce com confirmação de deploy |
| Diagnóstico de conexão, Tooling Apex e execução de testes | `.github/workflows/sf-devsrefeat-diagnostics.yml` | `workflow_dispatch` manual | `connection-check`, `tooling-apex-summary`, `apex-tests` |
| Consultar/validar metadados M3 | `.github/workflows/sf-devsrefeat-metadata.yml` | `workflow_dispatch` manual | `retrieve`, `compare`, `validate`, sem deploy real |
| Validação de Incidentes da DevSreFeat | `.github/workflows/sf-devsrefeat-incidents-validate.yml` | Issue `SDOA VALIDATE DevSreFeat incident-intake` pelo owner; ou `workflow_dispatch` manual | Dry-run de Incidentes e verificações específicas |
| Deploy real de Incidentes | `.github/workflows/sf-devsrefeat-incidents-deploy.yml` | **Somente** `workflow_dispatch` manual, owner, SHA e confirmação | Dry-run, proteções de master e deploy real do pacote Incidentes |

## CI automático pronto

| Finalidade | Workflow |
|---|---|
| Testes Jest da funcionalidade Clonar Pipeline | `.github/workflows/clone-pipeline-ui-ci.yml` |
| Testes de políticas e contratos M4/M5 | `.github/workflows/sf-m4-policy-ci.yml` |
| Testes, lint e guardrails dos Incidentes | `.github/workflows/devops-sre-incidents-ci.yml` |
| Testes de Pipeline Monitor | `.github/workflows/devops-sre-pipeline-monitor-ci.yml` |

Estes workflows de CI são disparados pelos eventos/escopos que já definem; o plugin **consulta** os resultados, distingue falhas, propõe correções em código por PR autorizado e nunca instala outro pipeline CI automaticamente.

## Workflows de piloto/legado: não escolher por padrão

- `.github/workflows/sf-devsrefeat-m4-preview.yml`
- `.github/workflows/sf-devsrefeat-m4-deploy.yml`

Eles permanecem versionados apenas para compatibilidade/auditoria até decisão explícita sobre retirada. Para tarefas novas, preferir M5 ou M4 Universal conforme operação e capacidade do conector.

## Política do assistente (comportamento obrigatório)

1. **Descobrir e selecionar:** interpretar solicitação, conferir master e os arquivos reais; escolher um workflow **existente** adequado ao escopo.
2. **Não gerar workflows:** não criar/editar `.github/workflows/*.yml` como parte de PLAN, diagnóstico, correção, retry, deploy ou consulta. Não converter pedido em configuração nova de GitHub Actions. Mudanças estruturais só em projeto de desenvolvimento separado e expressamente autorizado.
3. **Executar via canal suportado:** criar Issue estrita para o M5 (ou validar Incidentes) somente quando solicitada; para workflows `workflow_dispatch`, orientar preenchimento manual **se o conector não oferecer dispatch**. Jamais usar Issues genéricas/comentários para burlar esse limite.
4. **Investigar sem disfarçar resultados:** consultar execução real, jobs, logs e artefatos seguros. Indicar status, Apex tests, componentes, falhas e se houve escrita. Nunca inferir deploy a partir de Action verde.
5. **Retry controlado:** PLAN tem no máximo duas novas tentativas fundamentadas se o usuário delegou investigação. DEPLOY não é repetido automaticamente, e a autorização anterior não se estende a outro pacote, destino ou commit.
6. **Segurança:** permitir somente pacote/ambiente revisado e usuário proprietário; dry-run e testes precedem escrita; não vazar dados da Salesforce no GitHub público.
7. **Evolução futura:** quando uma capacidade não for coberta pelo catálogo, explicar a lacuna e propor **melhoria em workflow existente** como mudança de desenvolvimento separada, em vez de gerar YAML sob demanda.

Este catálogo descreve o que já existe; não modifica nem autoriza novos gatilhos. Sempre comparar contra os arquivos atuais da master antes de executar.
