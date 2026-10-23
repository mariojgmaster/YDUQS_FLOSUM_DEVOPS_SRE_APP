# M4.1 — Salesforce DevOps Assistant: deployments reutilizáveis

**Status:** M4.1 `plan` validado na DevSreFeat para Apex sem alterações (#1), LWC sem alterações (#2) e LWC com alteração intencional (#3). O deploy real universal ainda está pendente. O M4 piloto original continua homologado e não é alterado.

## Arquitetura

Este repositório passa a oferecer:
- `.github/workflows/sf-universal-m4.yml` — acionamento **somente manual** com operações `plan` e `deploy`;
- `config/salesforce-devops/catalog.json` — allowlist versionada dos destinos, GitHub Environments, manifestos e testes;
- `scripts/ci/sf-deploy-policy.py` — validação de manifesto, tipos de metadata e equivalência segura de pacotes Metadata API;
- `scripts/ci/sf-general-deploy.sh` — baseline por SHA, retrieve, preview, dry-run e deploy;
- `tests/test_sf_deploy_policy.py` — testes locais de política, comparação e proteção de ZIP.

A arquitetura mantém **uma ECA e um GitHub Environment por organização Salesforce**, independentemente da operação (consulta, testes, Metadata API, deploy). Para a DevSreFeat, continua sendo **o Environment existente** `sf-devsrefeat-read`; não é necessário criar outro ou habilitar aprovação humana adicional.

O backend é exclusivamente o GitHub Actions + Salesforce CLI. Não requer Node.js próprio, OpenBao, Salesforce Hosted MCP ou segunda VPS.

## Escopo do piloto M4.1

| Destino | GitHub Environment | My Domain |
|---|---|---|
| DevSreFeat | `sf-devsrefeat-read` | `https://yduqs--devsrefeat.sandbox.my.salesforce.com` |

| Pacote | Metadata | Manifesto | Testes |
|---|---|---|---|
| `security-apex` | ApexClass: CompareSecurityCode, CompareSecurityCodeTest | `manifest/sf-devsrefeat-m3.xml` | CompareSecurityCodeTest |
| `clone-pipeline-lwc` | LightningComponentBundle: clonePipelineAction | `manifest/sf-deploy-clone-pipeline-lwc.xml` | Jest do componente (pré-acesso Salesforce) + ClonePipelineControllerTest (dry-run/deploy) |

**Apex e LWC existentes** são suportados pela política. Outros tipos (Flow, PermissionSet, CustomObject, QuickAction, Flosum) exigem validação do formato, testes e extensão revisada. **Criação de metadados, exclusões e produção ainda não estão liberadas.** A leitura/planejamento do pacote LWC foi homologada; o deployment real ainda não.

## Gate Jest obrigatório para LWC

Para `package_id=clone-pipeline-lwc`, o job `resolve` executa `npm ci --ignore-scripts --no-audit --no-fund` utilizando `package-lock.json` e, depois, a suíte `force-app/main/default/lwc/clonePipelineAction/__tests__/clonePipelineAction.test.js` (`npm run test:unit -- --runInBand --runTestsByPath ...`). O marcador `SDOA_LWC_JEST_PASSED` aparece somente se todos os testes passarem. Esse job **não utiliza a ECA ou os segredos Salesforce**.

A verificação vale para ambas as operações: **plan** e **deploy**. Uma falha de Jest impede o job `execute`, e portanto o acesso Salesforce e qualquer implantação. Para `security-apex`, o gate Jest não roda; o mecanismo continua com testes Apex em dry-run/deploy.

O gate Jest foi adicionado depois das execuções M4.1 #1–#3 e **ainda não foi homologado em GitHub Actions**. Após o merge desta alteração, fazer um novo `plan` do LWC antes de qualquer `deploy` real.

## Interpretação do último plano LWC

Na execução `M4 Universal #3`, obtivemos `SDOA_REMOTE_BASELINE_OK`, `SDOA_PREVIEW: toDeploy=0 conflicts=1 toDelete=0 ignored=0` e `SDOA_PLAN_OK`. O comando `sf project deploy preview --manifest` reflete o Source Tracking do projeto local, não necessariamente a lista de arquivos que o deploy real enviará com `--metadata-dir`. Por isso **`toDeploy=0` não anula a diferença Git × baseline que o comparador identificou**. O `plan` foi aprovado, mas **não realizou** dry-run nem deploy real. O conflito não autoriza usar `--ignore-conflicts`; o deploy universal só pode seguir pelas comparações de baseline e pelo pacote Metadata API explícito.

## Conceito de baseline

O `commit_sha` é o commit da `master` que contém o **novo código que se deseja implantar**.

O `baseline_sha` é o commit que representa a **última versão efetivamente implantada desse pacote naquele destino**. Ele deve ser comprovado pelo histórico de deploy, e pode ser diferente por pacote e organização. Um merge nunca prova que o commit já foi implantado.

O workflow exige que o baseline seja um commit ancestral do commit atual. Converte ambos os estados do repositório para Metadata API com `sf project convert source`, e recupera os metadados atualmente existentes na Salesforce em ZIP, usando a mesma técnica homologada no M3. Compara o resultado da sandbox com o baseline. **Se houver qualquer diferença real ou estrutural, o deploy é bloqueado.**

Depois compara a versão nova com a baseline para determinar se existem alterações aprovadas. Assim, podemos autorizar diferenças **intencionais no GitHub** sem sobrescrever alterações inesperadas feitas diretamente na organização.

Caso o código novo seja idêntico à baseline, o resultado será `SDOA_NO_CHANGE` — nenhum deployment é realizado. Não marcar isso como deploy homologado.

## Proteções obrigatórias

1. Apenas `workflow_dispatch` na branch `master`, pelo proprietário do repositório piloto. Re-run do mesmo job é bloqueado.
2. SHA completo da `master` e baseline ancestral obrigatório.
3. Ambiente e pacote resolvidos exclusivamente do catálogo revisado; nunca aceitar URL de destino, comando ou manifesto arbitrário digitado pelo solicitante.
4. Para `deploy`, confirmação literal: `DEPLOY DevSreFeat security-apex` ou `DEPLOY DevSreFeat clone-pipeline-lwc`.
5. Comparação do estado atual da sandbox com baseline declarado, para evitar sobrescrita de alterações remotas.
6. Preview do manifesto sem exclusões e sem componentes ignorados.
7. Execução de `sf project deploy start --dry-run --metadata-dir ... --test-level RunSpecifiedTests` com as classes de teste permitidas no catálogo.
8. Recuperação do estado remoto **novamente** depois do dry-run. Se a org mudou, bloqueia.
9. Só então deployment real do **mesmo pacote Metadata API convertido**. Não se usa `--ignore-conflicts`, `--ignore-errors`, `--ignore-warnings`, bypass de testes ou deleções destrutivas.
10. Logs públicos contêm apenas marcadores e contagens; arquivos JSON, ZIPs, classes, tokens e dados da organização ficam temporários e são eliminados no encerramento do job.

A segunda verificação diminui, mas não elimina totalmente, uma condição de corrida entre a leitura remota e o deploy. Para cenários críticos, utilizar bloqueio operacional externo ou janela controlada de mudanças, além da governança de branch.

## Passo a passo do primeiro teste (sem deploy)

1. Revisar/mesclar o PR que criou o M4.1. Nada roda automaticamente no merge.
2. Confirmar que o Environment existente `sf-devsrefeat-read` continua com `SF_CLIENT_ID`, `SF_USERNAME`, `SF_JWT_KEY` e `SF_INSTANCE_URL` e restrição de branch `master`.
3. Descobrir o **SHA do commit realmente implantado** para o pacote escolhido, conferindo GitHub Actions e Salesforce Deployment Status. Não adivinhar nem usar um SHA antigo apenas por comodidade.
4. GitHub → Actions → **Salesforce DevOps - M4 Universal** → **Run workflow** → `master`.
5. Selecionar `operation=plan`, `target=DevSreFeat`, `package_id=security-apex`, preencher SHA atual e SHA baseline comprovado e deixar `confirmation` **vazio**.
6. Interpretar `SDOA_REMOTE_BASELINE_OK` e, havendo alteração intencional no candidato, `SDOA_PLAN_OK`; ou `SDOA_NO_CHANGE` se as versões forem idênticas.
7. Em caso de erro `SDOA_REMOTE_DRIFT`, não ignorar: há divergência entre org e baseline ou diferenças de serialização que precisam ser examinadas em ambiente autorizado.

**Somente depois da revisão do plano**, para um deploy efetivamente desejado, executar um **novo** workflow com `operation=deploy`, mesmos SHAs e confirmação literal adequada. Exigir `SDOA_DRY_RUN_PASSED`, `SDOA_REAL_DEPLOY_SUCCEEDED` e **Deploy: Succeeded** em Salesforce Setup → Deployment Status. Não repetir automaticamente um deploy inconclusivo.

Não modificar uma classe ou LWC produtivo apenas para forçar um teste. Um deploy real do M4.1 deverá usar uma alteração legítima revisada em PR.

## Adicionar novos projetos e ambientes

Para outro repositório Salesforce DX, copiar workflow, scripts, testes, catálogo e guide; ajustar `sfdx-project.json` e criar manifestos por pacote. Adicionar o pacote às escolhas `workflow_dispatch.inputs.package_id` e ao catálogo versionado. Para cada sandbox adicional:

1. Configurar ECA no ambiente Salesforce e uma integração JWT autorizada para as operações do projeto, com permissões de Metadata API e somente as capacidades necessárias.
2. Configurar um GitHub Environment **por organização** (não por operação). Adicionar seus secrets `SF_CLIENT_ID`, `SF_USERNAME`, `SF_JWT_KEY` e a variável `SF_INSTANCE_URL`, e restringir o deploy à branch protegida.
3. Registrar o alias, My Domain e o nome do GitHub Environment em `targets` e adicionar a escolha no workflow. Não usar credenciais da DevSreFeat para outras sandboxes.
4. Para novas categorias de metadados, implementar validador e testes antes de habilitar o tipo. O piloto permite apenas ApexClass e LightningComponentBundle.
5. Produção requer uma política de rollout própria, testes/cobertura, segregação de credenciais, avaliação de risco e autorização corporativa. **Esta versão bloqueia produção.**

Como o mesmo Environment fornece capacidade de escrita, proteger `master`, `.github/workflows/**`, `scripts/ci/**`, `manifest/**` e `config/salesforce-devops/**`. Dispensar Required reviewers para o deploy não equivale a dispensar revisão de código e controle de quem pode editar os workflows.

## Situação de homologação

- **M4 original:** deployment real já homologado na DevSreFeat.
- **M4.1 `plan`:** confirmado pela DevSreFeat para Apex e LWC; com LWC alterado, `SDOA_PLAN_OK` na execução #3.
- **M4.1 Jest gate:** introduzido neste PR, aguardando execução do workflow.
- **M4.1 deploy real:** ainda não homologado; requer nova autorização explícita com baseline válido após teste Jest.
- **M5 ChatOps:** posterior, preservando a exigência de solicitação inequívoca de deploy.

Documentação oficial: [Salesforce CLI convert source](https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_project_convert_source.html), [Salesforce CLI deploy start](https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_project_deploy_start.html) e [GitHub workflow_dispatch](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
