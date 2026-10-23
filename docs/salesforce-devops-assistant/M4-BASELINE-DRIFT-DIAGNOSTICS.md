# Diagnóstico de divergência do baseline — M4 Universal

## Situação real (23/10/2026)
- M4 Universal **#5**: `clone-pipeline-lwc`, `deploy`, `SDOA_REAL_DEPLOY_SUCCEEDED` (commit `387599ebd2c789199f3e65bdbc834e16c11a3f4d`). **Não comprova deploy de classes Apex.**
- M4 Universal **#6**: `clone-pipeline-apex`, `deploy`, baseline `387599ebd2c789199f3e65bdbc834e16c11a3f4d` e commit `edf81b0932ee42b559cc08465a5fc42988431bb3`: bloqueado em `SDOA_REMOTE_DRIFT`. Nenhum deploy real ou dry-run.
- M4 Universal **#7**: `clone-pipeline-apex`, `plan`, mesmos SHAs: bloqueado em `SDOA_REMOTE_DRIFT`. Nenhum deploy real ou dry-run.
- PR #19 (nomes sequenciais) está mesclada. **Merge não implanta o Apex**.

## Objetivo da melhoria
Quando o comparador já recusa o baseline, imprimir no log público **apenas os identificadores de metadata existentes no manifesto revisado** que apresentem diferenças entre a versão Git e a versão recuperada da org. Exemplo ilustrativo (não é resultado observado):

```text
SDOA_REMOTE_COMPARE: equal=false differences=1
SDOA_REMOTE_DIFFERING_MEMBERS: ApexClass:ClonePipelineController
Error: Org differs from the last-known-deployed package. Blocked.
```

Não imprimir conteúdo do Apex, hashes do conteúdo remoto, campos, credenciais, XML, ZIP, SOQL ou caminhos de arquivos privados. Se o pacote contiver arquivos ausentes, extras ou não autorizados, a validação existente continua falhando de forma genérica e segura.

## Teste operacional após PR revisada e mesclada
1. Obter o **novo SHA da master**.
2. GitHub Actions → M4 Universal → `operation=plan`, `target=DevSreFeat`, `package_id=clone-pipeline-apex`, `commit_sha=<SHA atual da master>`, `baseline_sha=387599ebd2c789199f3e65bdbc834e16c11a3f4d`, `confirmation=` vazio.
3. Como o baseline já divergiu no histórico, esperar que o gate continue bloqueando. Ele imprimirá contagens e nomes aprovados dos componentes divergentes, quando a comparação puder ser concluída. **Não selecionar deploy durante o diagnóstico.**
4. Com base nos nomes identificados, um operador autorizado deve realizar uma comparação de leitura entre a org e commits candidatos do Git para identificar a versão efetivamente implantada **para este pacote Apex**. Não há evidência suficiente para escolher esse SHA automaticamente.
5. Se não existir nenhum commit equivalente à versão org, registrar o estado remoto de forma controlada e revisada antes de permitir um novo baseline. Jamais colocar `--ignore-conflicts`, omitir testes ou igualar o baseline ao HEAD sem comprovação.
6. Somente quando `SDOA_REMOTE_BASELINE_OK` permitir `plan` com a baseline correta, revisar intenção e executar deploy autorizado em **nova** execução, e validar Salesforce Deployment Status.

## Proteções mantidas
`workflow_dispatch` somente manual, GitHub Environment atual, allowlist, SHA imutável, JWT restrito, recheck de baseline, `RunSpecifiedTests`, nenhum re-run de escrita, logs sem fonte ou tokens, bloqueio do próprio `SDOA_REMOTE_DRIFT`.

**Este PR não executa Actions, não valida deploy, não modifica a sandbox e não altera ECA/JWT.** Os testes Python da política foram ampliados; a execução da suíte no GitHub deve ocorrer antes de aprovar a PR.
