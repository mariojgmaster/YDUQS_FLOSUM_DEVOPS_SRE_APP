# Tasks — SPEC-002

## Fundação / documentação
- [x] T001 Consultar source do Flosum já integrado ao projeto e separar configuração de execução.
- [x] T002 Documentar as quatro áreas e as variantes operacional/analítica no padrão SLDS 2.
- [x] T003 Escrever spec, plano, contrato, modelo inicial e quickstart.
- [x] T004 Preparar branch de feature a partir da master verificada.

## US1 / US2 / US3 — implementação
- [x] T005 Implementar Apex de consulta read-only com FLS/sharing, limites e erros seguros.
- [x] T006 Implementar LWC no padrão Lightning com pesquisa, seleção, Steps e record navigation.
- [x] T007 Criar manifesto mínimo e testes automatizados Apex/Jest.
- [x] T008 Disponibilizar CI restrito a testes de LWC do novo componente.

## Validação não executada na origem ainda
- [x] T009 Executar Jest e lint do novo LWC com dependências instaladas, verificar logs de CI — [run #40044764106](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40044764106): ESLint PASS; 6/6 Jest PASS.
- [ ] T010 Validar compile, segurança e Apex tests na DevSreFeat sem deploy.
- [ ] T011 Verificar dados reais, perfis e o comportamento de FLS na sandbox.
- [ ] T012 Validar configuração da Lightning Component Tab, App Manager e tema Cosmos.
- [ ] T013 Obter aceite visual/funcional e só então concluir esta SPEC.

**Não marcar DONE com base apenas em PR ou em testes locais.** Próximas features exigem SPEC própria.
