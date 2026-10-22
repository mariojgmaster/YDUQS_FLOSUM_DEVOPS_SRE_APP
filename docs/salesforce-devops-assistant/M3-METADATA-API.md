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
sf project retrieve start \
  --manifest manifest/sf-devsrefeat-m3.xml \
  --output-dir <diretorio-temporario-no-runner> \
  --target-org devsrefeat-m3 \
  --wait 30 --json
```

- Não modifica o repositório nem grava metadados no package directory `force-app/`.
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
