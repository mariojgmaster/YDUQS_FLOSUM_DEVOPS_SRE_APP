# M3 - Metadata API na DevSreFeat (GitHub Actions + ECA/JWT)

**Status:** proposto para revisão; este PR não executa operações Salesforce. O piloto M3 depende de merge e de um disparo manual.

## Escopo e dependências

- Repositório: `mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP` (público).
- Sandbox: `DevSreFeat` / `https://yduqs--devsrefeat.sandbox.my.salesforce.com`.
- Autenticação: ECA da Salesforce com JWT Bearer. **Sem Salesforce Hosted MCP / Flex Credits de MCP**.
- Reutiliza o Environment GitHub `sf-devsrefeat-read`, com `SF_CLIENT_ID`, `SF_USERNAME`, `SF_JWT_KEY` e `SF_INSTANCE_URL` já usados no diagnóstico Apex.
- Workflows são **manuais**, sem deploy efetivo.
- NÃO usar o `manifest/package.xml` genérico com curingas neste piloto.
- O manifesto restrito `manifest/sf-devsrefeat-m3.xml` seleciona somente:
  - `ApexClass:CompareSecurityCode`
  - `ApexClass:CompareSecurityCodeTest`

O script recusa alterações não aprovadas nesse manifesto e verifica o My Domain para evitar executar no ambiente errado.

## Diagnóstico de falhas de retrieve

Se `retrieve` falhar **depois** de `JWT authorization succeeded`, o problema não é necessariamente a ECA. O comando `sf project retrieve start` depende de permissões de **Metadata API**, diferentes das operações REST/Tooling API já homologadas.

A documentação Salesforce exige, para acesso à Metadata API, **`Modify Metadata Through Metadata API Functions` ou `Modify All Data`**, além das permissões específicas do tipo de metadados. Essas permissões concedem também capacidade de modificação de metadados e **não são somente leitura**. Não habilitar nenhuma delas sem autorização administrativa e revisão de segurança corporativa. Idealmente, separar identidades e GitHub Environments para diagnósticos de baixo privilégio e operações que requerem permissão de Metadata API.

O script trata respostas brutas apenas em arquivos temporários e imprime **somente categorias de erro** no GitHub, porque o repositório é público. Códigos previstos:

| Código | Interpretação inicial |
|---|---|
| `M3_RETRIEVE_PERMISSION` | Possível falta de permissão da Metadata API ou específica de ApexClass |
| `M3_RETRIEVE_LOCAL_PATH` | Diretório de saída inválido, não gravável ou fora do projeto |
| `M3_RETRIEVE_CLI_FLAGS` | Flags incompatíveis com versão instalada da CLI |
| `M3_RETRIEVE_SOURCE_CONFLICT` | Conflito de source tracking |
| `M3_RETRIEVE_METADATA` | Componentes/nomes ou tipo de metadata indisponíveis |
| `M3_RETRIEVE_SESSION` | Token/sessão rejeitados pela Metadata API |
| `M3_RETRIEVE_TRANSIENT` | Problema temporário de rede, timeout ou limite |
| `M3_RETRIEVE_UNCLASSIFIED` | Erro sem classificação segura; diagnosticar em ambiente privado |

O comando `--manifest` com `--output-dir` é válido, conforme a referência oficial da Salesforce CLI. Depois da execução M3 #2, identificamos `M3_RETRIEVE_SOURCE_CONFLICT`: a sandbox tem Source Tracking e a CLI detectou conflito no contexto do projeto versionado.

**Correção proposta:** o script cria um projeto Salesforce DX **novo e isolado** sob o diretório temporário do runner, com `sfdx-project.json` próprio e pacote fonte inicialmente vazio. O retrieve ocorre com `cwd` neste projeto isolado, usando o mesmo manifesto fechado de duas classes; a comparação com os arquivos do GitHub só é feita em memória. O script não usa `--ignore-conflicts`, não sobrescreve `force-app` e não faz `git commit` ou upload de artefatos.

Se `M3_RETRIEVE_SOURCE_CONFLICT` persistir mesmo no projeto isolado, **não** liberar `--ignore-conflicts` às cegas: verificar a saída detalhada em ambiente privado. A execução `validate` ainda será testada separadamente; sua própria verificação de conflitos precisa ser analisada antes de adicionar qualquer flag de bypass.

Verificações recomendadas no Salesforce (sem aumentar permissões automaticamente):

1. **Setup → Users → usuário configurado em `SF_USERNAME`**: identificar Profile e Permission Sets realmente atribuídos.
2. Conferir `API Enabled`, `Modify Metadata Through Metadata API Functions` e eventuais permissões específicas dos componentes que serão recuperados. Não habilitar `Modify All Data` apenas para liberar o retrieve.
3. Manter revisão/segregação de acesso antes de passar de Tooling API para Metadata API.
4. Não copiar JSON bruto, nomes internos ou tokens dos jobs do GitHub público.

**Fontes:** [Salesforce Metadata API Edit Access](https://help.salesforce.com/s/articleView?id=meta_modify_metadata_perm.htm&language=en_US&type=5) e [CLI project retrieve start](https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_project_retrieve_start.html).

## Antes da primeira execução

1. Revisar o PR de M3 e confirmar que os três arquivos (`.github/workflows/sf-devsrefeat-metadata.yml`, `scripts/ci/sf-devsrefeat-m3.sh` e `manifest/sf-devsrefeat-m3.xml`) contêm apenas ações autorizadas.
2. Em **Settings → Environments → sf-devsrefeat-read**, manter as restrições de branch e os segredos existentes. A ECA e sua chave privada não devem aparecer em PR, log, issue ou commit.
3. Conferir se o usuário da ECA tem acesso necessário para recuperar metadados das duas classes e validar deployment em sandbox.
4. Confirmar a permissão de uso da sandbox de acordo com a política corporativa. Não mudar permissões globais por conveniência.
5. Aprovar e mesclar na `master`. O workflow usa manual `workflow_dispatch` e não roda automaticamente no merge.

## Executar no GitHub Actions

**Actions → Salesforce DevSreFeat - Metadata M3 → Run workflow → branch master.**

### Operação `retrieve` (primeiro teste)

Comando executado pela CLI no runner:

```bash
# Executado dentro de um projeto SFDX temporario com pacote fonte vazio
sf project retrieve start \
  --manifest <caminho-absoluto-do-manifest-revisado> \
  --output-dir <pasta-retrieved-do-projeto-isolado> \
  --target-org devsrefeat-m3 \
  --wait 30 --json
```

- Não modifica o repositório nem grava metadados no package directory `force-app/`.
- Executa a CLI a partir de um **SFDX temporário** com package directory vazio, isolado do Source Tracking do checkout; o conteúdo é descartado no fim do job.
- Verifica se recuperou as **duas classes** esperadas; publica somente uma contagem.
- O conteúdo recuperado permanece em diretório temporário, apagado ao final; **não é disponibilizado como artifact**, pois o repo é público.

Resultado esperado: `M3_RETRIEVE_SUMMARY: Apex classes retrieved=2 expected=2`.

### Operação `compare` (segundo teste)

Executa o mesmo retrieve isolado e compara os quatro arquivos versionados:

- `CompareSecurityCode.cls`
- `CompareSecurityCode.cls-meta.xml`
- `CompareSecurityCodeTest.cls`
- `CompareSecurityCodeTest.cls-meta.xml`

Compara conteúdo após normalizar quebras de linha, sem imprimir valores, fontes ou hashes.

Exemplo de resultado: `M3_COMPARE_SUMMARY: same=4 different=0 missing=0`.

Se houver drift (`different>0`) ou arquivo ausente, o job falha com `M3_METADATA_DRIFT`. Isso é um alerta: antes de promover alterações, faça uma inspeção do diff **num contexto privado/autorizado**. O M3 **não faz commit automático de código recuperado**.

### Operação `validate` (terceiro teste)

Comando executado pela CLI:

```bash
sf project deploy start \
  --dry-run \
  --manifest manifest/sf-devsrefeat-m3.xml \
  --test-level RunSpecifiedTests \
  --tests CompareSecurityCodeTest \
  --target-org devsrefeat-m3 \
  --wait 40 --json
```

- É uma **simulação de deployment de sandbox**: executa verificações e testes sem persistir o pacote.
- Não executa `sf project deploy start` sem `--dry-run`.
- A regra `RunSpecifiedTests` pode exigir 75% de cobertura de Apex **por componente implantado**, diferentemente dos testes Apex executados na fase anterior.
- Mesmo sem persistir metadados, a validação **executa Apex/Flow de testes**; verifique automações dependentes.
- O job somente marca sucesso se Salesforce retornar `result.success=true`, conclusão e status geral `0`. Caso contrário `M3_VALIDATE_FAILED` e consulta privada a Setup → Deployment Status e Apex Test Execution.

## Política de segurança

Este repositório é **PÚBLICO**. Não expor conteúdo bruto da Metadata API em logs, GitHub artifacts ou outputs. O workflow limita o conteúdo publicado a contagens e estados. Arquivos temporários (inclusive chave privada) são removidos no fim do job.

Nenhum input permite comandos arbitrários, manifest customizado, org arbitrária ou ativação de deployments reais. Para usar em outra org/repo, prepare um workflow derivado, novos Environment/ECA, verificação de domínio, manifest selecionado e revisão de governança.

## Próximas fases

- Depois do M3, criar **M4 Deploy** separado com Environment de escrita, aprovação humana obrigatória, pacote explícito, políticas de branch e trilha de auditoria.
- **M5 ChatOps**: somente operações allowlisted, solicitadas por atores autorizados. Nunca executar PRs ou comandos de usuários externos com credenciais.
- Para múltiplas orgs, usar ECA/JWT e GitHub Environment independente por destino, inclusive comparações feitas em jobs isolados e sem exposição de metadados.

## Documentação oficial

- [Salesforce CLI retrieve start](https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_project_retrieve_start.html)
- [Salesforce CLI deploy start --dry-run](https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_project_deploy_start.html)
- [Salesforce CLI: deploy validate (uso recomendado para produção)](https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_project_deploy_validate.html)
- [GitHub Environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
