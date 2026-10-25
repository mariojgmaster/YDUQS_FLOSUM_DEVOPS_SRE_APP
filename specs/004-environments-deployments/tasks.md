# Tarefas SPEC-004

- [x] T001 Especificar requisitos/contrato/modelo e analisar consistência com fonte verificada.
- [x] T002 Criar metadados de configuração, integridade temporal e permissões granulares.
- [x] T003 Implementar controladores USER_MODE, paginação/filtros e classificação de qualidade.
- [x] T004 Implementar UI SLDS com cadastro/listagem e navegação à origem.
- [x] T005 Testar Apex/Jest e controles de pacote/automação: 9 Apex reais, 9 Jest, 10 testes de automação e 102 regressões Python PASS.
- [x] T006 Inspecionar navegação real e preparar integração preservando recursos existentes.
- [x] T007 Dry-run #40141697664 PASS, artifact realmente baixado/descriptografado/analisado: 20 componentes, 9 testes, zero erros; cobertura de cada recurso de produção entre 88,5% e 100%.
- [x] T008 Autorização recebida e deploy real executado na DevSreFeat: [#40142453709](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40142453709), 20 componentes, 9 testes, zero erros. Resposta integral analisada com checkOnly=false/success=true/done=true.
- [x] T009 Conferir tab original e navegação após deploy por leitura Metadata API: run #40142581375, pipelineMonitor aponta para devSreDeliveryHub e as quatro abas da aplicação permanecem iguais.
- [ ] T010 Homologação funcional pelo responsável: atribuir Permission Set adequado, cadastrar vigências e conferir filtros, resultados e histórico. Não confundir leitura de metadados com teste visual.

## Revisão de clareza e Design System

- [x] U001 Definir finalidade das abas e registrar interações em `ux-refinement.md`.
- [x] U002 Simplificar cadastro/listagem de ambientes e aplicar estilos semânticos compartilhados.
- [x] U003 Reorganizar filtros, explicações e estados da consulta de deployments.
- [x] U004 Executar Jest/ESLint e controles de pacote.
- [ ] U005 Implantar como atualização controlada e homologar aparência/teclado/zoom/fusos na org.
