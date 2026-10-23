# M4 — Deploy Salesforce explícito na DevSreFeat

## Decisão de arquitetura

- **Um único GitHub Environment por organização Salesforce.** No piloto, todos os workflows usam o Environment já existente `sf-devsrefeat-read` (nome legado), inclusive diagnósticos, testes Apex, Metadata M3 e M4.
- Não criar novo Environment nem copiar secrets somente para permitir deploy.
- Não exigir `Required reviewers` ou aprovação humana adicional na hora de executar o job. O **ato de solicitar manualmente o workflow + a confirmação textual + o SHA completo** constitui a intenção verificável.
- Nunca interpretar teste, PR, merge, consulta ou comparação como autorização para deploy.
- **Somente sandbox DevSreFeat neste piloto.** Produção e outras orgs precisam de políticas e configurações específicas, não herdam esta autorização.
- Nenhum MCP, Node.js próprio ou OpenBao. Node.js do GitHub Actions apenas instala a Salesforce CLI.

### Sobre o nome do GitHub Environment

Nome atual (já funcional): `sf-devsrefeat-read`.

Nome desejado para um modelo amplo: `sf-devsrefeat`, porém **GitHub não fornece mecanismo documentado de rename-in-place que migre secrets e proteção**; a API cria/atualiza um environment pelo nome e a remoção do antigo apaga seus secrets. Não fazer criação/exclusão automática. Enquanto for mantido o Environment existente, **preservar exatamente** `sf-devsrefeat-read` em todos os workflows. Não trocar o nome no YAML antes de uma migração planejada, pois o GitHub pode criar silenciosamente um Environment sem secrets ao executar um workflow com nome inexistente.

Referência: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments

## Segurança do repositório público

O repositório atual é **público**: logs e workflow YAML são observáveis. Não imprimir classes, tokens, respostas JSON da Salesforce, segredos, arquivos ZIP ou conteúdo da org.

Como o mesmo Environment possui privilégios suficientes para escrita, **qualquer workflow autorizado a lê-lo merece confiança equivalente a deploy**. Recomenda-se proteger a `master`, impedir alterações não revisadas de `.github/workflows/**` e `scripts/ci/**`, restringir colaboradores com acesso de escrita e auditar as permissões do usuário ECA. Não configurar `Required reviewers` no Environment caso não deseje uma segunda aprovação do deployment. Uma revisão de alterações no repositório e uma aprovação de deploy são ações distintas.

As regras de fluxo que garantem intenção não impedem abuso por alguém com permissão de alterar o próprio YAML na branch `master`. Governança do GitHub permanece fundamental.

## Workflow do M4

Arquivo: `.github/workflows/sf-devsrefeat-m4-deploy.yml`

É disparado **somente por `workflow_dispatch`**. Não existem gatilhos `push`, `pull_request`, Issue, ChatOps ou schedule para deployment real.

O job rejeita se:

1. A execução não foi manual ou a branch não é `master`;
2. O disparador não é o proprietário do repositório piloto;
3. O usuário tentar usar **Re-run jobs** (`run_attempt > 1`);
4. A confirmação não for exatamente `DEPLOY DevSreFeat`;
5. O SHA informado não tiver 40 caracteres hexadecimais ou não for exatamente o SHA do commit checkado pelo GitHub;
6. O domínio de destino não for `https://yduqs--devsrefeat.sandbox.my.salesforce.com`;
7. O manifesto tiver outros componentes, wildcards, API diferente ou classes ausentes;
8. Os segredos de ECA/JWT estiverem ausentes;
9. A autenticação JWT ou o **dry-run com `RunSpecifiedTests`** falhar ou retornar conclusão incerta.

O primeiro pacote autorizado contém **exatamente**:
- `ApexClass:CompareSecurityCode`
- `ApexClass:CompareSecurityCodeTest`

O manifesto reutiliza `manifest/sf-devsrefeat-m3.xml`. O M4 **não executa deployments destrutivos** nem utiliza `--ignore-errors`, `--ignore-warnings` ou opção para pular testes. Após o diagnóstico **M4 Preview #1 (`toDeploy=1 conflicts=1 toDelete=0 ignored=0`)**, acrescentamos uma exceção cuidadosamente limitada de Source Tracking para o piloto:

- O workflow executa o **`compare` M3 homologado no mesmo job**, recuperando via Metadata API ZIP as duas classes aprovadas e conferindo **quatro arquivos idênticos** ao commit da `master`. Qualquer diferença real ou falha de recuperação interrompe a operação.
- Executa `sf project deploy preview` com o manifesto fechado. Qualquer exclusão (`toDelete>0`) ou componente ignorado bloqueia o deploy.
- Se nenhum item estiver pendente nem em conflito, informa **`M4_NOOP_ALREADY_SYNCED`** e termina sem executar deploy real. Isso não equivale à homologação de um deploy real.
- **Somente quando há conflito de tracking e identidade 4/4 comprovada com a sandbox**, o comando real recebe `--ignore-conflicts`, restrito ao manifesto explícito de duas classes. A validação `--dry-run` e os testes Apex continuam obrigatórios; após o dry-run, uma **segunda comparação 4/4** evita implantar se a org mudou durante a validação.
- Se ocorrerem modificações reais na organização ou no GitHub, este piloto **falha fechado**. Futuras implantações que intencionalmente mudem o código exigirão um processo próprio de análise de diferença e autorização de sobrescrita, não poderão utilizar automaticamente esta exceção.
- Repositório público: resposta bruta Salesforce, conteúdo do ZIP, hashes e segredos não são impressos nem armazenados como artifacts.

Essa exceção **não é um bypass genérico**. Na documentação da Salesforce, `--ignore-conflicts` pode sobrescrever código remoto; por isso ele só é aceito para um pacote que já demonstrou igualdade exata entre Git e org no mesmo job.

Referência oficial: https://developer.salesforce.com/docs/platform/sfdx-dev/guide/sfdx-dev-source-tracking-resolve-conflicts.html

## Pré-requisitos (mesmo Environment, sem segredos novos)

1. GitHub → Settings → Environments → `sf-devsrefeat-read`.
2. Confirmar que `SF_CLIENT_ID`, `SF_USERNAME`, `SF_JWT_KEY` e `SF_INSTANCE_URL` continuam configurados conforme os testes anteriores.
3. Deixar `Required reviewers` **desativado**, conforme decisão do projeto.
4. Restringir deployment branches a `master` e proteger a branch. O script também faz essa validação.
5. Confirmar que o usuário de integração da ECA tem permissões de Metadata API adequadas ao pacote e à política corporativa.

## Como solicitar o primeiro deployment real

1. Revisar/mesclar o PR que adiciona o workflow, sem executá-lo.
2. Acessar GitHub → Actions → **Salesforce DevSreFeat - Deploy Explicito M4** → **Run workflow**.
3. Selecionar `master`.
4. Copiar o **SHA completo do commit atual da master** no campo `commit_sha`.
5. Digitar exatamente `DEPLOY DevSreFeat` no campo `confirmation`.
6. Conferir novamente sandbox, SHA e manifesto antes de pressionar o botão **Run workflow**.

Isso é um ato **intencional de deployment real**. Não execute somente para verificar se o workflow está funcionando, a menos que deseje realmente reimplantar as duas classes Apex na DevSreFeat.

O workflow primeiro usa:

```bash
sf project deploy start --dry-run \
  --manifest manifest/sf-devsrefeat-m3.xml \
  --test-level RunSpecifiedTests \
  --tests CompareSecurityCodeTest \
  --target-org devsrefeat-m4 --wait 60 --json
```

**Somente se aprovado**, ele executa o mesmo comando **sem `--dry-run`**.

## Diagnóstico comprovado (M4 Preview #1)

Após dois deployments reais com retorno de erro, o diagnóstico somente leitura informou:
```text
M4_PREVIEW_SUMMARY: toDeploy=1 conflicts=1 toDelete=0 ignored=0
```

Isso evidencia **um conflito de Source Tracking**, mas não prova diferença no conteúdo das classes. A última comparação M3 aprovada mostrou `same=4 different=0 missing=0`; o workflow M4 agora refaz essa comparação no instante da solicitação, sem confiar em um resultado antigo.

Os próximos resultados esperados para o piloto são:
- `M4_METADATA_IDENTICAL`: arquivos da org e do GitHub comprovadamente iguais;
- `M4_TRACKING_ONLY_OVERRIDE`: habilitação condicionada de `--ignore-conflicts` para o pacote restrito;
- `M4_DRY_RUN_PASSED`: testes validados;
- `M4_METADATA_RECHECK_PASSED`: comparados novamente os quatro arquivos após o dry-run, imediatamente antes da escrita;
- `M4_REAL_DEPLOY_SUCCEEDED`: **somente** se Salesforce confirmar a gravação persistente.

**A execução de um PR nunca autoriza um deployment.** Após o merge, solicitar de novo o M4 pela UI do GitHub com o SHA atualizado e a confirmação literal; não reexecutar jobs anteriores.

## Observabilidade segura da Salesforce CLI (correção após M4 #5)

O workflow de deploy passou a registrar **onde e por que falhou**, sem revelar as respostas brutas de Salesforce ou dados corporativos no GitHub público.

O incidente `M4 #5` passou por JWT e `compare` com os quatro arquivos iguais, mas parou com o antigo `M4_PREVIEW_UNVERIFIED`. A condição anterior misturava falha do comando CLI e erro na interpretação do JSON, por isso **a causa raiz da execução #5 ainda não é comprovável** com os logs anteriores.

Novos diagnósticos do workflow `Deploy Explicito M4`:
- `M4_CLI_VERSION`: versão instalada da Salesforce CLI.
- `M4_PREVIEW_CLI_EXIT`: código de saída numérico do `sf project deploy preview`.
- `M4_PREVIEW_JSON_SHAPE`: apenas `status` (categoria) e **tipos** dos campos `result`, `toDeploy`, `conflicts`, `toDelete` e `ignored`. Não imprime valores de objetos.
- `M4_PREVIEW_CLI_ERROR`: falha do comando, acompanhada exclusivamente de categoria predefinida (`SOURCE_CONFLICT`, `NOTHING_TO_DEPLOY`, `PERMISSION`, `SESSION_OR_AUTH`, `NETWORK_OR_LIMIT`, `CLI_ARGUMENT` ou `UNCLASSIFIED`).
- `M4_PREVIEW_INVALID_JSON`: nenhuma resposta JSON válida/estrutura raiz inesperada.
- `M4_PREVIEW_STATUS_ERROR`: formato reconhecido mas status não é sucesso.
- `M4_PREVIEW_SCHEMA_MISMATCH`: campos ausentes ou com tipos incompatíveis.
- `M4_PREVIEW_SUMMARY`: somente contagens `toDeploy`, `conflicts`, `toDelete`, `ignored`, **apenas depois** de validar o formato.
- `M4_DRY_RUN_CLI_EXIT` / `M4_DRY_RUN_RESPONSE`: código de saída, estado permitido e contagens de erros/testes da validação.
- `M4_REAL_DEPLOY_CLI_EXIT` / `M4_REAL_DEPLOY_RESPONSE`: mesma informação, referente ao deployment efetivo, inclusive nas falhas.

O workflow `Salesforce DevSreFeat - Diagnostico M4` (somente leitura) também foi atualizado para registrar `M4_DIAG_PREVIEW_CLI_EXIT`, `M4_DIAG_PREVIEW_JSON_SHAPE` e categorias de falha, sem deploy e sem exigir SHA.

**Política de segurança:** todos os diagnósticos são gerados a partir de uma allowlist de campos e categorias. Nunca imprimir valores de `message`, `stack`, `data`, `instanceUrl`, `username`, `accessToken`, classes Apex ou hashes. Não habilitar `--verbose`, `set -x` nem `cat` de respostas Salesforce no workflow público.

**Política de decisão:** respostas inesperadas ou incompletas continuam bloqueando a operação. A melhora é de observabilidade, **não de permissão**. Depois do merge, execute **primeiro o workflow somente leitura `Diagnostico M4`**; evite reexecutar o M4 real até entendermos o retorno da CLI.

Referências: [Salesforce CLI — Deploy Preview](https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_project_deploy_preview.html) e [implementação PreviewResult](https://github.com/salesforcecli/plugin-deploy-retrieve/blob/main/src/utils/previewOutput.ts).

## Interpretar resultados

| Código | Significado |
|---|---|
| `M4_INTENT_VERIFIED` | Identidade, branch, commit SHA, destino e componentes foram conferidos |
| `M4_METADATA_IDENTICAL` | GitHub e sandbox possuem os mesmos quatro arquivos autorizados (compare M3) |
| `M4_TRACKING_ONLY_OVERRIDE` | Override pré-autorizado apenas sob igualdade 4/4 e preview sem exclusões |
| `M4_METADATA_RECHECK_PASSED` | A igualdade 4/4 permaneceu válida após o dry-run, antes do deploy real |
| `M4_NOOP_ALREADY_SYNCED` | Nenhum deployment realizado porque não há itens pendentes |
| `M4_DRY_RUN_PASSED` | Validação e testes foram aprovados, sem alteração persistente |
| `M4_REAL_DEPLOY_STARTING` | O workflow iniciou uma operação de escrita na sandbox |
| `M4_REAL_DEPLOY_SUCCEEDED` | Salesforce confirmou o deployment persistente |
| `M4_DEPLOY_UNCONFIRMED` | Não há confirmação conclusiva: verificar Deployment Status antes de nova tentativa |
| `M4_DEPLOY_REPORTED_FAILURE` | Salesforce CLI retornou falha: confirmar no Deployment Status antes de nova tentativa |
| `M4_RERUN_DENIED` | Uma repetição automática ou manual desse mesmo job não é permitida |

**Nunca** interpretar `M4_DRY_RUN_PASSED` como deploy concluído. Nunca afirmar sucesso definitivo se houver erro/incompletude no retorno Salesforce.

## Política para os próximos ambientes e ChatOps

Uma ECA e um GitHub Environment por **organização Salesforce**, não por tipo de ação. Credenciais separadas entre sandboxes distintas e produção.

O plugin pode elaborar uma solicitação ChatOps, mas um deploy real só é autorizado com evidência explícita da intenção, commit exato, manifesto revisado, usuário permitido e validação concluída. Uma Issue aberta ou um label inserido, por si só, **não** autoriza deployment.

O conector GitHub do ChatGPT desta conversa não apresenta `workflow_dispatch` direto. Até existir fluxo seguro de disparo, o acionamento do M4 é feito na UI do GitHub, sem segunda aprovação de `Required reviewers`.

Referência oficial do CLI: https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_project_deploy_start.html
