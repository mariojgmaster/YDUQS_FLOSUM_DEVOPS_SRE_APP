# Tasks — SPEC-003 / fase de desenho

## Documentação e qualidade
- [x] T001 Confirmar que não há tabela própria de incidentes; decisão dada pelo responsável em 23/10/2026.
- [x] T002 Registrar ADR-001, separando configuração Flosum, deployment real e incidente.
- [x] T003 Especificar domínio, quatro entidades candidatas e vínculos auditáveis.
- [x] T004 Definir política **Não mensurável / Parcial / Certificado** e testes negativos.
- [x] T005 Versionar proposta em PR próprio, preservando escopo do PR #34.

## Dependências de descoberta/revisão
- [x] T006a Confirmar responsáveis pelo cadastro manual: equipe DevOps/SRE (aprovado em 23/10/2026).
- [x] T006b Definir responsáveis pela **revisão causal**: equipe DevOps/SRE (RMs); COE fora do MVP.
- [ ] T006c Definir quem certifica cobertura DORA, ainda não atribuída.
- [ ] T007 Confirmar cadastro autoritativo de serviços/aplicações.
- [ ] T008 Inventariar objetos Flosum de deployment PROD, campos e contratos temporais. **Parcial:** inventário de metadados da DevSreFeat executado no [run #40130263390](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40130263390) — 8 candidatos de deployment, 6 descritos, 1 com sinais de status/destino/commit, sem timestamp de conclusão identificado. Ainda falta validar objeto/fonte exata, registros reais autorizados e contrato temporal/PROD. Não marcar concluído.
- [ ] T009 Aprovar campos mínimos, compartilhamento e retenção de histórico.

## Implementação posterior, não concluída
- [x] T010a Criar schema inicial para incidentes e ações, validações temporais e Permission Sets de operador/leitor em PR de código.
- [ ] T010b Validar schema, regras, campos e acesso real na sandbox antes de marcar conclusão.
- [x] T011a Criar LWC SLDS 2 operacional para cadastro e consulta manual.
- [x] T011b Homologar a interface com o responsável na DevSreFeat: cadastro de incidente fictício, consulta na lista e ação de recuperação confirmados em 24/10/2026.
- [x] T012a Preparar revisão causal por RMs, com permissão granular e bloqueio de `DeploymentRelated + Confirmed`.
- [ ] T012b Implementar vínculos auditáveis com deployments Flosum verificados, liberando confirmação causal apenas após controle adequado.
- [ ] T013 Implementar certificação da cobertura do período.
- [x] T014a Escrever testes Apex/Jest e CI de interface.
- [ ] T014b Executar CI, testes Apex e testes de permissão na DevSreFeat, sem deploy.
- [x] T015 Homologar o fluxo operacional de incidentes na aba original com o responsável; confirmação funcional em 24/10/2026. Isso não certifica causalidade nem métricas DORA.
- [ ] T016 Implementar fórmulas DORA por SPEC posterior com evidência suficiente.

**Sem declarar KPI DORA implementado ou confiável antes dos gates.**

## MVP-02 / revisão em GitHub
- [x] T017 Atualizar decisão de governança: RMs DevOps; COE postergado.
- [x] T018 Preparar Custom Permission no Permission Set DevOps/SRE e regras anti-confirmação prematura.
- [x] T019 Preparar formulário de revisão exclusivo para RM em LWC e testes Jest/CI.
- [ ] T020 Validar deploy package, teste de permissões/FLS e sharing na DevSreFeat; nenhum deploy implícito.

- [x] T021 Remover a separação artificial de RM e operador; revisão pelo grupo DevOps/SRE com o próprio `DevSreIncident_Operator`.
- [x] T022 Preparar Public Group e sharing rules para todos os incidentes e ações da equipe, sem expor a organização inteira.
- [x] T023 Preparar workflow manual de dry-run com teste Apex em DevSreFeat (execução real pós-merge).
- [x] T024 Registrar execução real na DevSreFeat: deploy [#40124487168](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40124487168), job `120962879031`; limpeza da duplicata [#40128322847](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40128322847), job `120974423896`; validação após limpeza [#40128701599](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40128701599), job `120975581489`. Todos SUCCESS; homologação funcional confirmada pelo responsável.

## Reconciliação de evidências — 24/10/2026

Os jobs acima comprovam testes LWC, dry-run/deploy e validação após limpeza. Não encerram automaticamente T010b, T014b ou T020: ainda falta demonstrar a matriz completa de permissões, FLS e sharing. T012b/T013/T016 continuam pendentes; cadastro manual não certifica vínculo causal nem cobertura DORA.

T008 permanece aberta. A inspeção direcionada Branch/Metadata Log foi preparada e mesclada no [PR #93](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/pull/93), mas ainda não há run observado dessa operação. O [contrato proposto de classificação de ambientes](../../docs/devops-sre-analytics/environment-classification-contract.md) registra regras e dependências sem inventar campos ou classificar destinos reais.
