# M4.2 — Salesforce-native deploy (sandbox)

## Objetivo e status

Piloto da DevSreFeat: **dispensar baseline SHA e deploy preview**, preservando segurança de ECA/JWT, escolha de ambiente, pacote revisado, código Git auditável, validação Salesforce e autorização explícita. O GitHub Actions é o motor; o ChatOps não tem dispatch nativo neste momento.

**Modelo de risco deliberado:** um deploy aprovado pode **sobrescrever alterações diretas na mesma metadata do Salesforce**, mesmo quando o dry-run passa. O dry-run **não compara** o estado remoto com uma versão Git anterior e não protege pinagem de versões de pacote gerenciado. Apenas em sandbox; produção exige outra política.

## Formulário GitHub Actions

Actions → **Salesforce DevOps - M4 Universal** → Run workflow → Use workflow from **master**.

| Campo | Valor para homologar numeração Apex |
| --- | --- |
| operation | **plan** |
| target | **DevSreFeat** |
| package_id | **clone-pipeline-apex** |
| confirmation | **vazio** |

Não existe campo de commit SHA nem baseline SHA: o workflow fixa automaticamente o **SHA do commit selecionado no disparo**, conferido com o checkout. O SHA inteiro é registrado em \`SDOA_M42_SHA\`. Para **deploy real** (somente após plan bem-sucedido e pedido intencional), nova execução com \`operation=deploy\` e \`confirmation=DEPLOY DevSreFeat clone-pipeline-apex\` exatamente. Não reaproveitar tentativas com **Re-run jobs**; o script rejeita \`run_attempt != 1\`.

## Execução interna

1. Disparo manual pela \`master\`, apenas proprietário, primeira tentativa; checkout imutável.
2. Testes Python de política; para LWC, Jest. Resolução de alvo/pacote cadastrados; **mesmo Environment \`sf-devsrefeat-read\`** com secrets ECA/JWT.
3. Conversão de **manifesto explícito** para diretório Metadata API com inspeção de arquivos contra a allowlist. Sem wildcards, arquivos estranhos ou destructiveChanges.
4. Autenticação JWT no My Domain autorizado; nenhum token ou segredo em logs públicos.
5. \`sf project deploy start --dry-run --metadata-dir ... --test-level RunSpecifiedTests --tests ... --json\` em **plan e deploy**. Só aprovação \`status=0\`, \`success=true\` e conclusão.
6. **PLAN** emite \`SDOA_M42_PLAN_OK\` e encerra sem deploy real.
7. **DEPLOY** verifica novamente commit + confirmação, usa **exatamente o mesmo payload local** do dry-run e executa comando Salesforce de deploy real. Somente \`SDOA_REAL_DEPLOY_SUCCEEDED\` confirma persistência.

## Evidência de testes e implantação

- \`SDOA_M42_PACKAGE_VERIFIED\`: somente arquivos permitidos.
- \`SDOA_M42_DRY_RUN_PASSED\`: dry-run Salesforce e testes Apex concluídos.
- \`SDOA_M42_PLAN_OK\`: **nenhum deploy**.
- \`SDOA_REAL_DEPLOY_SUCCEEDED\`: Salesforce confirmou escrita.
- Em caso de erro real ou estado incerto, verificar **Setup → Deployment Status** na sandbox antes de qualquer nova tentativa.

## O que foi intencionalmente removido

- Não pede nem calcula \`baseline_sha\` para bloquear execução.
- Não usa \`sf project retrieve start\` para comparar org ↔ Git antes do deploy.
- Não usa \`sf project deploy preview\` como gate.
- Não usa \`--ignore-conflicts\`, \`--ignore-errors\`, \`--ignore-warnings\` nem deleta metadata.
- **Não** é deploy Flosum por API. É Salesforce Metadata API/CLI sobre pacote autorizado.

## Limitações / proteção operacional

- Sem detecção de alterações manuais concorrentes no Salesforce; pode sobrescrever componentes do manifesto.
- Alterações a \`packageVersions\` ou outras dependências Apex podem ser aplicadas pela Metadata API, ainda que o teste passe. Inspecionar as classes e as versões de pacotes quando elas forem relevantes.
- Aprovação de pacote e revisão de código antes de escrever continuam responsabilidade do GitHub e do autor da mudança.
- O \`plan\` é uma validação do candidato **naquele momento**, não uma garantia de sucesso futuro; o \`deploy\` repete o dry-run antes de qualquer gravação.
- Não usar em produção sem uma política separada com controle de drift, backup e rollback.

## Próximo teste operacional

1. Validar PR CI \`M4 Policy Checks\`: \`bash -n\`, \`py_compile\` e \`unittest\`.
2. Após merge, abrir o workflow na \`master\`; realizar **plan** de \`clone-pipeline-apex\`.
3. Se \`SDOA_M42_PLAN_OK\`, examinar resultado do Salesforce e autorizar separadamente **deploy**, se adequado.
4. Após \`SDOA_REAL_DEPLOY_SUCCEEDED\`, validar a sequência \`Teste - Cópia 01\`, \`02\`, \`03\` na tela Flosum.
