# Tasks — SPEC-003 / fase de desenho

## Documentação e qualidade
- [x] T001 Confirmar que não há tabela própria de incidentes; decisão dada pelo responsável em 23/10/2026.
- [x] T002 Registrar ADR-001, separando configuração Flosum, deployment real e incidente.
- [x] T003 Especificar domínio, quatro entidades candidatas e vínculos auditáveis.
- [x] T004 Definir política **Não mensurável / Parcial / Certificado** e testes negativos.
- [x] T005 Versionar proposta em PR próprio, preservando escopo do PR #34.

## Dependências de descoberta/revisão
- [x] T006a Confirmar responsáveis pelo cadastro manual: equipe DevOps/SRE (aprovado em 23/10/2026).
- [ ] T006b Confirmar papéis que revisam causalidade e certificam cobertura; a revisão antes de DORA é mandatória.
- [ ] T007 Confirmar cadastro autoritativo de serviços/aplicações.
- [ ] T008 Inventariar objetos Flosum de deployment PROD, campos e contratos temporais.
- [ ] T009 Aprovar campos mínimos, compartilhamento e retenção de histórico.

## Implementação posterior, não concluída
- [x] T010a Criar schema inicial para incidentes e ações, validações temporais e Permission Sets de operador/leitor em PR de código.
- [ ] T010b Validar schema, regras, campos e acesso real na sandbox antes de marcar conclusão.
- [x] T011a Criar LWC SLDS 2 operacional para cadastro e consulta manual.
- [ ] T011b Homologar a interface com operadores reais.
- [ ] T012 Implementar revisão causal e links para deployments reais.
- [ ] T013 Implementar certificação da cobertura do período.
- [x] T014a Escrever testes Apex/Jest e CI de interface.
- [ ] T014b Executar CI, testes Apex e testes de permissão na DevSreFeat, sem deploy.
- [ ] T015 Homologar UX/fluxo de incidentes.
- [ ] T016 Implementar fórmulas DORA por SPEC posterior com evidência suficiente.

**Sem declarar KPI DORA implementado ou confiável antes dos gates.**
