# Piloto Salesforce DevOps Assistant — DevSreFeat (sem MCP)

> Status: **configuracao pendente**. Este documento nao prova que a ECA, JWT ou GitHub Environment ja estejam funcionando. Objetivo inicial: diagnostico somente leitura na sandbox `DevSreFeat`.

## 1. Contexto do repositorio

- GitHub: `mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP`; branch principal: `master`.
- Projeto Salesforce DX: `force-app/`; `sourceApiVersion: 67.0`; testes Jest no `package.json`.
- Sandbox alvo: `https://yduqs--devsrefeat.sandbox.my.salesforce.com`.
- Repositorio atualmente **PUBLICO**. Logs e artifacts do GitHub Actions podem ser vistos publicamente; nao imprimir dados da org, nomes de classe, IDs, tokens, chaves ou resultados detalhados.
- Nao alterar `sfdx-project.json` para forcar o login de todos os desenvolvedores; o workflow usa `--instance-url` explicitamente.
- Nao usar o `manifest/package.xml` existente para deploy automatico: ele contem varios curingas `*`. Deploys precisam de pacote **explicitamente revisado**, aprovacoes e outro workflow.

## 2. Preparar chave e certificado (fora do repositorio)

Em um terminal com OpenSSL instalado, gere uma chave privada unica para esta integracao:

```bash
mkdir -p sf-devsrefeat-eca
cd sf-devsrefeat-eca
openssl req -x509 -newkey rsa:3072 -sha256 -days 365 -nodes \
  -keyout sf-devsrefeat.key \
  -out sf-devsrefeat.crt \
  -subj "/CN=GitHub-Actions-DevSreFeat"
```

- `sf-devsrefeat.crt` = **certificado publico**, destinado a ECA.
- `sf-devsrefeat.key` = **chave privada**; nao enviar ao ChatGPT, nao commitar, nao colocar em issue/PR. Guardar em local seguro ate cadastrar no GitHub Secrets e planejar rotacao.
- Nao compartilhar certificados/chaves entre diferentes empresas ou ambientes sem aprovacao formal.
- Avaliar prazo de validade e politica corporativa; rotacionar certificado e secret juntos.

## 3. Criar ECA na propria DevSreFeat

1. Entre na sandbox e abra **Setup -> App Manager -> New External Client App**. Se o Setup direcionar para External Client App Manager, utilize o cadastro equivalente.
2. Nome sugerido: `GH Actions - DevSreFeat - DevOps SRE`. Informe email corporativo de contato.
3. Ative OAuth; em **Callback URL**, utilize `http://localhost:1717/OauthRedirect` conforme guia oficial da Salesforce CLI (JWT nao usa redirecionamento, mas a ECA pode exigir o campo).
4. De acordo com o guia Salesforce DX para ECA, habilite os escopos `api`, `web` e `refresh_token` **se requeridos pela configuracao usada**. Para o JWT bearer em si, o objetivo e acessar a API com o minimo de privilegios; `mcp_api` nao faz parte desta integracao.
5. Na secao **Flow Enablement**, selecione **Enable JWT Bearer Flow** e envie **somente** `sf-devsrefeat.crt`.
6. Crie a ECA e abra **Policies**. Configure `Permitted Users = Admin approved users are pre-authorized`.
7. Crie/associe um **Permission Set de usuario autorizado**, por exemplo `GH_Actions_DevSreFeat_Read`, e atribua apenas ao usuario de integracao escolhido; conceda somente as permissoes necessarias para leitura Tooling API e testes autorizados.
8. Revise limites de sessao e politicas da empresa. Evite usar perfil System Administrator no piloto. Uma consulta de metadata exige `API Enabled` e acesso apropriado; no caso de teste Apex, revise permissoes especificas.
9. Em **External Client App Manager -> ECA -> Settings -> OAuth Settings**, obtenha o **Consumer Key** (Client ID). **Nao e necessario inserir o Consumer Secret no workflow JWT**.
10. Confirme o My Domain em Setup -> My Domain. Se o fluxo JWT falhar por exigencia de autenticacao interativa adicional, consulte a equipe de seguranca: nao desabilitar MFA/high-assurance cegamente.

Guia Salesforce DX: https://developer.salesforce.com/docs/platform/sfdx-dev/guide/sfdx-dev-auth-eca.html

## 4. Criar e proteger o GitHub Environment

No repositorio: **Settings -> Environments -> New environment**.

Nome exato: `sf-devsrefeat-read`.

**Crie o Environment ANTES de executar qualquer workflow**. GitHub pode criar automaticamente environments sem regras caso sejam referenciados por um workflow.

Em **Environment secrets**, cadastre manualmente:

| Nome | Conteudo |
| --- | --- |
| `SF_CLIENT_ID` | Consumer Key da ECA da DevSreFeat |
| `SF_USERNAME` | Username Salesforce do usuario de integracao autorizado |
| `SF_JWT_KEY` | Conteudo integral (PEM) de `sf-devsrefeat.key`, incluindo BEGIN/END PRIVATE KEY |

Em **Environment variables**, cadastre:

| Nome | Valor |
| --- | --- |
| `SF_INSTANCE_URL` | `https://yduqs--devsrefeat.sandbox.my.salesforce.com` |

Restricoes recomendadas:
- Deployment branches: permitir somente `master` (apos revisao/merge do PR).
- Required reviewers, se disponiveis e praticaveis. Evite autodeploy de PROD e permita revisao externa sempre que possivel.
- Proteja `master` com regras de PR, verificacoes de status e revisao de alteracoes em `.github/workflows/**`.
- Nao execute codigo de PRs de terceiros em jobs com secrets. Workflow piloto so possui gatilho **manual**.
- Github Actions e segredos de repository **publico** merecem revisao de seguranca corporativa; considere repo privado para logs mais detalhados.

Documentacao: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments

## 5. Teste gradual no GitHub

Apos revisão e merge deste PR em `master`:

1. Acesse **Actions -> Salesforce DevSreFeat - Diagnostico Seguro -> Run workflow**.
2. Selecione branch `master` e operacao `connection-check`.
3. Espere a conclusao; verifique se houve **autenticacao JWT concluida** sem dados sigilosos nos logs.
4. Execute `tooling-apex-summary` para testar Tooling API. Ela imprime so a quantidade amostrada, **nao** os nomes das classes.
5. Somente apos autorizacao para testes, execute `apex-tests`. Nao interpreta teste automatizado como deploy.
6. Em caso de falha, forneca ao ChatGPT somente mensagens de erro **sanitizadas** e o link da execucao; nao copie tokens, logs brutos ou documentos internos.

O conector GitHub atualmente disponivel no ChatGPT permite consultar PRs e logs, mas **nao expõe uma acao para iniciar diretamente `workflow_dispatch`**. A primeira execucao deve ser disparada pela UI GitHub.

## 6. Ampliacao apos smoke test

- **SOQL e Tooling API:** adicionar consultas predefinidas e allowlisted; evitar SOQL arbitraria via comentarios de issues.
- **Comparacao multi-org:** configurar um segundo Environment com ECA/JWT propria e realizar leitura das duas orgs em jobs distintos; preservar confidencialidade.
- **Metadata API:** arquivos `package.xml` explicitamente limitados; retrieve/validate com permissao e revisao.
- **Deploy:** workflow separado + GitHub Environment `sf-devsrefeat-deploy` com aprovadores + testes + pacote revisado. Nunca executar usando automaticamente o `manifest/package.xml` com curingas.
- **ChatOps:** issue com autor e operacao permitidos e revisao de mantenedor; nao usar comentarios/labels de usuarios externos como comandos executaveis; jamais criar deploy por label sem revisao.

## 7. Checklist obrigatorio (toda operacao)

- [ ] Repo/branch/commit SHA confirmados.
- [ ] Alias/org e My Domain conferidos.
- [ ] ECA, usuario, permissoes, chave/certificado e Environment confirmados, sem copiar segredos.
- [ ] Operacao classificada: leitura, teste, retrieve, validate ou deploy.
- [ ] Operacao esta na allowlist e tem escopo minimo.
- [ ] Para deploy: manifest/artefatos revisados, approval explicito, testes e rollback definidos.
- [ ] Revisar seguranca de logs/artefatos porque o repo e publico.
- [ ] Reportar Run ID, status real, evidencia e pendencias; nunca alegar execucao nao observada.

## Referencias

- Salesforce ECA para Salesforce CLI: https://developer.salesforce.com/docs/platform/sfdx-dev/guide/sfdx-dev-auth-eca.html
- Autorizacao JWT CI/CD: https://developer.salesforce.com/docs/platform/sfdx-dev/guide/sfdx-dev-auth-jwt-flow.html
- Comando CLI JWT: https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_org_login_jwt.html
- GitHub Environments: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
