# M5 — Salesforce DevOps Assistant / GitHub ChatOps

## Situação

- **M4.2 — homologado (23/10/2026)**. PLAN #16: \`SDOA_M42_DRY_RUN_PASSED\` e \`SDOA_M42_PLAN_OK\`. DEPLOY #18: \`SDOA_REAL_DEPLOY_SUCCEEDED\` para \`DevSreFeat\`, pacote \`clone-pipeline-apex\`, SHA \`844f6d327801770f95c5596697e25b296a5b50a7\`. Aceite funcional confirmado pelo proprietário: clonagem inicial, numeração sequencial, clonagem de cópia e integridade dos Pipeline Steps. Contagens específicas de métodos Apex e verificação independente do Deployment Status não fazem parte da evidência apresentada neste documento.
- **M5.1 — ChatOps de consulta**: plugin usa GitHub conectado para examinar repositórios, PRs, testes, Actions e logs sanitizados. Sempre consultar a execução mais recente, nunca presumir status do histórico.
- **M5.2 — implementação para PLAN**: novo workflow \`.github/workflows/sf-m5-chatops-plan.yml\`, acionado pela abertura de **Issue de intenção exata do proprietário**, executa o mesmo \`scripts/ci/sf-general-deploy.sh\` do M4.2 com \`OPERATION=plan\`. Não é \`workflow_dispatch\` nativo do conector. Até o primeiro teste end-to-end, o acionamento Issue → GitHub Actions deve ser tratado como **a validar**, não homologado.
- **M5.3 — deploy solicitado pelo chat**: ainda **não implementado**; deploy real permanece exclusivamente pelo formulário manual M4.2, com \`confirmation\` literal. Não usar Issue para deploy.

Plugin privado: https://chatgpt.com/plugins/plugins_6adae31dc0188191a7d6c1c1c1b347d0

## Arquitetura (sem backend e sem MCP)

ChatGPT + GitHub connector → \`create_issue\` no repositório escolhido → evento \`issues.opened\` → workflow M5 PLAN → validador rígido (repositório + owner + título + corpo + evento) → allowlist catálogo/manifesto → ambiente GitHub existente + ECA/JWT → dry-run Salesforce + RunSpecifiedTests → logs sanitizados que o plugin pode consultar no GitHub.

**Não cria credenciais no chat, PAT, tokens adicionais, outro Environment ou servidor**. O GitHub Actions continua hospedando as operações Salesforce. Uma Issue é um *evento explícito e auditável* e não equivale a um GitHub \`workflow_dispatch\`. A conexão GitHub deve expor a ação de criação de Issue para que o plugin possa disparar. Se a conta conectada aparecer como bot e não como dono, o job é rejeitado sem acessar a Salesforce; nesse caso deve-se usar o M4.2 manual.

## Contrato mínimo do comando para PLAN

Pedido no ChatGPT: **"Crie um PLAN ChatOps para o repositório mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP, pacote clone-pipeline-apex e sandbox DevSreFeat."**

O plugin verifica a identidade exata do repositório, a existência do M5 no branch padrão, o catálogo, e cria **uma única Issue** pelo conector GitHub:

Título exato:

\`\`\`text
SDOA PLAN DevSreFeat clone-pipeline-apex
\`\`\`

Corpo exato (sem Markdown, espaços extras, comentários, links ou comandos):

\`\`\`text
SDOA-CHATOPS/1
operation=plan
target=DevSreFeat
package_id=clone-pipeline-apex
\`\`\`

O \`workflow\` só processa \`issues.opened\` no \`master\` e na primeira tentativa do runner. Os campos do corpo são analisados como strings enumeradas, **nunca como shell**; seleção efetiva depende do catálogo registrado (\`config/salesforce-devops/catalog.json\`) e do manifesto revisado. A Issue deve ser aberta e enviada pela conta proprietária \`mariojgmaster\`. \`issue_comment\`, \`issue.edited\`, \`reopened\`, PRs e autor não autorizado não executam nada. O código mestre do workflow é fixado em \`github.sha\`.

Depois de criar a Issue, plugin lê \`Actions → Salesforce DevOps - M5 ChatOps PLAN\` e relata estado **in progress / sucesso / falha** por evidências. Marcadores:

- \`SDOA_M5_PLAN_INTENT_VERIFIED\` — comando aceito. Não implica auth ou sucesso Salesforce.
- \`SDOA_M42_AUTH_OK\` — autenticação ECA/JWT da sandbox concluída.
- \`SDOA_M42_DRY_RUN_PASSED\` — Salesforce validou o pacote e os testes selecionados.
- \`SDOA_M42_PLAN_OK\`, \`SDOA_M5_PLAN_SUCCEEDED\` — nenhum deploy real enviado nesta execução.
- \`SDOA_M42_DRY_RUN_DIAG\` — falha categorizada, sem erros brutos.

## Segurança / governança

- **É impossível escolher \`deploy\` no evento M5 de Issue**: o validador, o workflow e a verificação dentro do executor rejeitam \`deploy\`. Escrita pelo chat só será considerada em um milestone futuro com autorização e revisão específicas.
- Sem fallback oculto ou posterior retry via Issue/comment; rejeitar operações malformadas e duplicadas. Cada Issue criada é uma nova tentativa de \`plan\`; nunca criar automaticamente em loop.
- SHA da master fixado automaticamente; nunca usar informação antiga da memória como status atual.
- Somente sandbox \`DevSreFeat\` e pacotes enumerados e registrados; produção fora de escopo.
- Mesmo GitHub Environment \`sf-devsrefeat-read\` (nome legado) e secrets ECA/JWT guardados no GitHub; nenhum token nos logs ou na Issue.
- \`plan\` da Salesforce é um dry-run, não necessariamente uma operação absolutamente sem efeitos externos de automação, limites ou consumo de API; porém **não persiste metadata de deploy**.
- A política M4.2 intencionalmente **não compara drift remoto**. O fluxo manual de deploy pode sobrescrever alterações org-side, e continua explicitamente confirmado.
- Não publicar logs brutos, metadata recuperada, stacks, JWT, private key, IDs sensíveis nem credenciais.

## Checklist de aceite M5.2

1. PR de implementação passou testes Python, sintaxe Bash e revisão de diffs, sem credenciais Salesforce.
2. Merge na \`master\` aprovado; verificar que o workflow M5 aparece em Actions.
3. Criar uma Issue exata de \`plan\` via plugin/conector GitHub.
4. Confirmar \`SDOA_M5_PLAN_INTENT_VERIFIED\`, \`SDOA_M42_DRY_RUN_PASSED\`, \`SDOA_M42_PLAN_OK\` e \`SDOA_M5_PLAN_SUCCEEDED\`. Não há deploy.
5. Checar falha segura para Issue sem autorização / schema inválido sem usar Salesforce. Teste end-to-end precisa de evidência própria.
6. Exercitar status em ChatGPT: latest run, latest success e latest real deploy distinguíveis.
7. Caso o conector não consiga criar a Issue como \`mariojgmaster\`, não relaxar a autorização. Manter M4.2 manual até solução autorizada.

## Roadmap

- M5.1: status/diagnóstico em qualquer repo acessível, usando GitHub conectado, com fatos atuais e sanitização.
- M5.2: PLAN por Issue explícita e auditável, executor Salesforce existente; ainda requer homologação operacional.
- M5.3: avaliação de um dispatch nativo em conector autorizado para deploy, mantendo confirmação explícita; **nunca** fazer deploy via Issue.
- M5.4: múltiplos sandboxes, produção, Tooling API e Flosum, com catálogo, permissões e políticas próprios por repositório/ambiente.

Projeto piloto: \`mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP\` / \`DevSreFeat\`. Para outro repo, instalar os workflows + catálogo + testes na sua master e autorizar expressamente o target e pacote; **não** pressupor que esse repositório controla todos os outros.
