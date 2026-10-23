# M5 — Salesforce DevOps Assistant (ChatOps), v0.1.0

**Estado:** plugin privado criado; operações de leitura e preparação assistida via conector GitHub. **Não há chamada nativa de workflow_dispatch exposta no conector GitHub atual.** M5 ainda não executa deployments diretamente por uma frase no ChatGPT.

Plugin privado: https://chatgpt.com/plugins/plugins_6adae31dc0188191a7d6c1c1c1b347d0

## Objetivo e arquitetura

GitHub-first, sem backend Node.js próprio, OpenBao, VPS adicional ou Salesforce Hosted MCP. ECA/JWT permanecem exclusivamente em GitHub Environments (um por organização Salesforce). O plugin usa duas skills privadas:

1. `setup` — cadastra/valida o contexto dos repositórios e ambientes, examina os manifests e configurações já aprovados e orienta o setup ECA/JWT sem pedir credenciais.
2. `salesforce-chatops` — diagnostica Actions, inspeções de código/PRs, status de deploy, Tooling API e Metadata API **a partir de evidências no GitHub**, e prepara intenções verificáveis para `plan` e `deploy`.

A plataforma de ChatGPT só executará as ações que o **GitHub connector efetivamente expuser**. A versão 0.1.0 não simula um `workflow_dispatch`, não usa comentários em Issues como ponte oculta para deploy e não cria tokens adicionais.

## Conversas suportadas na primeira versão

- "No repositório owner/repo, encontre o último M4 Universal, mostre o SHA, pacote, operação e status."
- "Revise a falha dessa Action, sem publicar tokens ou logs brutos."
- "Compare o baseline declarado com o SHA atual, valide catálogo e proponha um `plan`."
- "Crie um PR só com a correção Apex/LWC pedida e os testes relacionados."
- "Prepare o formulário de deploy do package_id para o alvo informado, mas **não dispare** sem ferramenta e intenção inequívoca."

O plugin deve sempre identificar o repositório, o ambiente, a operação, o pacote, a origem da evidência e se houve ou não escrita.

## Contrato de execução

| Operação | v0.1.0 | Condição |
| --- | --- | --- |
| Descobrir repositórios, PRs, Actions, jobs e diagnósticos | Suportado via GitHub conectado | Ferramenta disponível e permissões |
| Abrir PR com código/testes para revisão | Suportado via GitHub conectado | Pedido explícito do usuário |
| Analisar Tooling API, Apex tests e Metadata API | Indireto, pelos workflows/logs existentes | Não declarar acesso Salesforce direto |
| Preparar `plan` | Suportado | Alvo/pacote e SHA/baseline comprovados |
| Iniciar `workflow_dispatch` pelo ChatGPT | **Pendente** | Exige conector GitHub que exponha dispatch, ou integração equivalente auditada |
| Executar deploy real direto do chat | **Pendente** | Além da ferramenta, contrato forte de autorização e proteção M4 |
| Flosum Deploys por API | **Pendente** | Verificar capacidades, APIs e permissões Flosum antes de implementar |
| Produção e exclusões de metadata | **Fora do escopo inicial** | Governança e rollout próprios |

## Política irrevogável do piloto

- Nenhum segredo ECA, JWT private key, refresh token ou token Salesforce no chat, em GitHub Issue/PR ou log público.
- **Somente o GitHub Environment já cadastrado por organização**; não criar um Environment por ação.
- Deploys reais só após solicitação explícita e verificável com alvo + pacote + SHA imutável + baseline implantado comprovado + dry-run/testes + recheck.
- Nunca usar `--ignore-conflicts` de forma genérica, `--force`, `--ignore-errors` ou `--ignore-warnings` para superar divergências não aprovadas.
- Nunca repetir automaticamente deployment de resultado incerto ou usar "Re-run jobs" para efetivar novo write.
- Alterações de código ficam em PRs; nenhum merge/deploy automático implícito.
- "Success" no GitHub sem `SDOA_REAL_DEPLOY_SUCCEEDED` pode ser apenas `plan`; confirmar Salesforce Deployment Status quando o resultado real importar.

## Próximas entregas do M5

**M5.1:** usar o plugin em conversas reais para status e diagnóstico de Actions de diferentes repositórios, testando resolução correta de projeto/ambiente.

**M5.2:** quando houver `workflow_dispatch` disponível por um conector autorizado, disparar inicialmente **somente** `plan`, preservando as validações e audit trail GitHub.

**M5.3:** liberar pedidos `deploy` para sandbox mediante intenção textual inequívoca, SHA e baseline revisados; reusar M4.1 sem criação de uma rota paralela insegura.

**M5.4:** expandir seleção de ambientes, comparação entre orgs e Flosum após especificação, testes e autorização técnica.

## Projeto de referência

Repo: `mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP`.

Target: `DevSreFeat`, GitHub Environment único `sf-devsrefeat-read`.

Workflow: `.github/workflows/sf-universal-m4.yml`.

Pacotes aprovados: ler o catálogo da `master` atual, **nunca presumir que um PR pendente já foi mesclado**.

Comandos e URLs: sempre consultar fontes atuais no GitHub; não reaproveitar SHA de execuções anteriores para um novo deployment.
