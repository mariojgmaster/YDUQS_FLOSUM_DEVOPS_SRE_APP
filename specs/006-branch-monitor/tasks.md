# Tasks — SPEC-006

Status: `[x]` concluído nesta fase de SPEC; `[ ]` pendente. Tasks sem autorização de deploy persistente.

## Especificação e pesquisa
- [x] T001 Documentar quatro telas e critérios de aceite dos wireframes.
- [x] T002 Inventariar fontes confirmadas e sinalizar lacunas de Component History/versão.
- [x] T003 Modelar DTOs e estados de confiança/completude.
- [x] T004 Definir fases G0–G5 e política de rollout.
- [ ] T005 Inventariar tipos/roles dos campos de Component e Component History sem revelar schema privado em GitHub público.
- [ ] T006 Identificar nome/tipo de FullName, metadataType, namespace, revisão/commit e política FLS reais.
- [x] T007a Verificar a existência de referência tipada \`Component_History → Component\` via describe autenticado.
- [ ] T007b Provar preenchimento/cardinalidade History→Component→Branch em amostra read-only, inclusive nulos e duplicatas.
- [ ] T008 Provar acesso ao conteúdo de **duas versões** e mecanismo de replay de snapshot de Branch, ou marcar Diff textual indisponível.
- [ ] T009 Investigar ligação componente/revisão→Metadata Log por evidência direta, sem join por Branch isoladamente.
- [ ] T010 Validar UX/contratos finais com estado completo/incompleto e pesquisa por nomes duplicados.

## M1 — Directory / Overview
- [ ] T011 Revisar metadata CustomApplication/CustomTab e permissão Reader.
- [ ] T012 Implementar controller read-only de Branch+atividade confirmada com cursor e DTO.
- [ ] T013 Implementar shell tabulado Visão geral/Branches/Comparar/Componentes conforme wireframes.
- [ ] T014 Implementar lista Branch, filtros automáticos, drilldown e ligação com Flosum.
- [ ] T015 Adicionar Jest/Apex e validação em DevSreFeat.
- [ ] T016 Implantar **somente** com autorização explícita do pacote e comparar metadata publicada.

## M2 — Describer por componente
- [ ] T017 Pesquisa por `ComponentKey` e resolução de ambiguidade; paginação.
- [ ] T018 BranchPresence e painel de detalhe com proveniência.
- [ ] T019 Version timeline apenas após T007; deploy timeline apenas após T009.
- [ ] T020 Testes de duplicação/versão/sem evidência e segurança.

## M3–M5 — Diff
- [ ] T021 Comparação de inventário com snapshots completos, classificação bidirecional e limites.
- [ ] T022 Diff por linha para fontes versionadas com conteúdo (gate T008).
- [ ] T023 Diff semântico por tipo de metadata com fixtures e proteção de XML.
- [ ] T024 Avaliação de conflitos e dependências baseada em identidade/versionamento.
- [ ] T025 Homologar as quatro telas e preparar documentação operacional.

## Gates que não podem ser pulados
T007, T008 e T009 são independentes: um join bem-sucedido não prova versão acessível nem deployment. A aprovação dos wireframes não libera inferências sem evidência.
