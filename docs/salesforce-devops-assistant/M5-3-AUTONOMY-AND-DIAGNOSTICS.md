# M5.3 — Autonomia para PLAN, deploy explícito e diagnóstico seguro

Status: em implementação, não homologado na Salesforce.

## Contrato GitHub Issue

PLAN (formato anterior mantido):
Title: SDOA PLAN DevSreFeat clone-pipeline-apex
Body:
    SDOA-CHATOPS/1
    operation=plan
    target=DevSreFeat
    package_id=clone-pipeline-apex

DEPLOY (somente pedido explícito do proprietário):
Title: SDOA DEPLOY DevSreFeat clone-pipeline-apex
Body:
    SDOA-CHATOPS/2
    operation=deploy
    target=DevSreFeat
    package_id=clone-pipeline-apex
    commit_sha=<sha master real de 40 caracteres>
    confirmation=DEPLOY DevSreFeat clone-pipeline-apex

Os 40 caracteres do SHA devem vir da consulta atual à master, e ser iguais ao commit efetivamente usado pelo workflow. Nunca submeter texto placeholder. Uma solicitação do usuário = uma Issue de deploy; reexecução (run_attempt > 1), comentários, edição da Issue e autores não proprietários não autorizam escrita. O mesmo M4.2 executa novo dry-run e testes Apex antes da implantação; no retry de deploy, nunca agir sem nova autorização e sem consultar Deployment Status.

## Autonomia controlada

O plugin pode abrir Issues PLAN, inspecionar logs e relatórios, propor/corrigir código em PR e, quando o usuário tiver delegado tentativas, executar no máximo duas tentativas adicionais de PLAN, cada uma como Issue nova. Não repetir falhas determinísticas de Apex/metadata sem corrigir a causa. Se pedir DEPLOY explicitamente, o plugin poderá criar uma única Issue de deploy v2 com SHA + confirmação e observar o resultado. Não executar deploy por sugestões, status, PLAN ou intenção implícita. A política continua limitada aos ambientes e pacotes cadastrados no repositório, sem ECA hospedada, MCP ou backend próprio.

## Análise detalhada e privacidade

O runner mantém o JSON Salesforce completo apenas em diretório temporário e o remove ao encerrar. Um artefato público seguro, nome sdoa-safe-report-<run-id>, é produzido quando a operação chegou ao retorno da CLI, retenção 7 dias. Ele enumera TODAS as entradas de falha conhecidas, com categoria, numeração, linhas/colunas, nomes revisados no manifesto, contagens, status e classificação. O plugin pode consultar o artefato com o conector GitHub.

Este relatório NÃO contém a íntegra literal do retorno bruto. Mensagens originais, código Apex, stack traces, nomes de classes não revisadas, IDs de registro, URLs e segredos NÃO são publicados. O repositório é PÚBLICO; disponibilizar JSON bruto nos Actions seria um vazamento de informações da organização. Para dar ao plugin acesso literalmente integral, precisaremos habilitar um canal privado com controle de acesso e revisar a sanitização antes de mudar a política. Não criar esse canal nem trocar a visibilidade do repo implicitamente.

## Homologação

- Passar GitHub CI com todos os testes unitários de política.
- Validar PLAN após merge e consultar o artefato público seguro.
- Testar deploy real somente após pedido específico e explícito, com SHA atual confirmado.
- Correlacionar SDOA_M42_DRY_RUN_PASSED, SDOA_REAL_DEPLOY_SUCCEEDED e SDOA_M5_DEPLOY_SUCCEEDED. Na dúvida, consultar o Salesforce Deployment Status.
