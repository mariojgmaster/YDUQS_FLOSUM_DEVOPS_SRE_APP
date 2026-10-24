# Tasks — SPEC-003 / fase de desenho

## Documentação e qualidade
- [x] T001 Confirmar que não há tabela própria de incidentes; decisão dada pelo responsável em 23/10/2026.
- [x] T002 Registrar ADR-001, separando configuração Flosum, deployment real e incidente.
- [x] T003 Especificar domínio, quatro entidades candidatas e vínculos auditáveis.
- [x] T004 Definir política **Não mensurável / Parcial / Certificado** e testes negativos.
- [x] T005 Versionar proposta em PR próprio, preservando escopo do PR #34.

## Dependências de descoberta/revisão
- [x] T006a Confirmar responsáveis pelo cadastro manual: equipe DevOps/SRE (aprovado em 23/10/2026).
- [x] T006b Definir responsáveis pela **revisão causal**: RMs DevOps; COE fora do MVP.
- [ ] T006c Definir quem certifica cobertura DORA, ainda não atribuída.
- [ ] T007 Confirmar cadastro autoritativo de serviços/aplicações.
- [ ] T008 Inventariar objetos Flosum de deployment PROD, campos e contratos temporais.
- [ ] T009 Aprovar campos mínimos, compartilhamento e retenção de histórico.

## Implementação posterior, não concluída
- [x] T010a Criar schema inicial para incidentes e ações, validações temporais e Permission Sets de operador/leitor em PR de código.
- [ ] T010b Validar schema, regras, campos e acesso real na sandbox antes de marcar conclusão.
- [x] T011a Criar LWC SLDS 2 operacional para cadastro e consulta manual.
- [ ] T011b Homologar a interface com operadores reais.
- [x] T012a Preparar revisão causal por RMs, com permissão granular e bloqueio de `DeploymentRelated + Confirmed`.
- [ ] T012b Implementar vínculos auditáveis com deployments Flosum verificados, liberando confirmação causal apenas após controle adequado.
- [ ] T013 Implementar certificação da cobertura do período.
- [x] T014a Escrever testes Apex/Jest e CI de interface.
- [ ] T014b Executar CI, testes Apex e testes de permissão na DevSreFeat, sem deploy.
- [ ] T015 Homologar UX/fluxo de incidentes.
- [ ] T016 Implementar fórmulas DORA por SPEC posterior com evidência suficiente.

**Sem declarar KPI DORA implementado ou confiável antes dos gates.**

## MVP-02 / revisão em GitHub
- [x] T017 Atualizar decisão de governança: RMs DevOps; COE postergado.
- [x] T018 Preparar Custom Permission + Permission Set RM e regras de validação anti-confirmação prematura.
- [x] T019 Preparar formulário de revisão exclusivo para RM em LWC e testes Jest/CI.
- [ ] T020 Validar deploy package, teste de permissões/FLS e sharing na DevSreFeat; nenhum deploy implícito.
