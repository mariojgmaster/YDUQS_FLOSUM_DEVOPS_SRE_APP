# Plano de implementação — SPEC-006

## Arquitetura
**Lightning App:** inserir aba `Branch Monitor` entre `DORA Cockpit` e `Pipeline Monitor` quando o módulo navegável M1 estiver pronto; respeitar CustomApplication/CustomTab atual em PR separado e sem alterar ordem das demais tabs.

**LWC:** container `devSreBranchMonitor` com uma visão montada por vez: `Overview`, `Branches`, `Compare`, `Components`. Visual SLDS 2 do Design System `docs/design-system.md`; tokens semânticos, campos de busca específicos, loading/vazio/erro, navegação teclado, truncamento e responsividade.

**Apex:** controllers read-only modularizados (ex.: `DevSreBranchController` para Branch/Metadata Log e `DevSreComponentController` apenas quando identidade de componente for confirmada). `with sharing`, `WITH USER_MODE`, guardrails para IDs/cursor/limites, DTOs estáveis e sem DML.

**Comparador:** pipeline de aquisição → reconciliação identidade/revisão → inventário → normalização de conteúdo → diff → interpretação semântica. Cache efêmero, sem replicar fonte em custom objects. Nunca persistir código arbitrário sem ADR e revisão de segurança.

**Describer:** pesquisa indexável por `ComponentKey`, drilldown por BranchPresence, união com HistoryVersion somente após prova de ligação e associação a OperationEvidence somente se o vínculo exato da versão com a execução existir.

## Fases / gates
- **G0 Descoberta confiável:** lookup History→Component tipado confirmado; ainda falta validar dados, cardinalidade, identidade de revisão, conteúdo e acesso; testes — andamento.
- **G1 Directory + Overview:** leitura de Branch e logs confirmados, sem inventar indicadores, testes Jest/Apex, primeira demo em sandbox sob autorização específica.
- **G2 Component Describer:** buscar identidade + BranchPresence; timeline/history opcional e explicitamente indisponível até G0.
- **G3 Diff inventário:** comparar duas listas completas de BranchPresence em snapshot/revisão conhecida; estados Unknown se ausência de evidência.
- **G4 Diff conteúdo:** somente depois de comprovar revisões/payloads, criar modo lado a lado e preview com sanitização de código (sem exec).
- **G5 Semantic Diff + riscos:** plugins de tipo de metadata e análise de dependências, após fixtures reprodutíveis e estudo de versões.

## Testes / qualidade
- Apex: CRUD/FLS/user mode, sharing, limites, paginação/cursor, processos desconhecidos, vínculos faltantes e números não certificados.
- Jest: lookup, navegação, duas branches, travamento de ações sem conteúdo, stable-key, loading/erro/incomplete, ellipsis/accessibilidade.
- Segurança: SQL dinâmico apenas de colunas permitidas pelo describe e `escapeSingleQuotes`/bind; nunca ecoar corpos de campos.
- Dry-run na DevSreFeat com run e artefatos sanitizados. Deploy real exige consentimento explícito, alvo + pacote + SHA fixado, testes e comparação posterior.

## Compatibilidade
Não alterar `DevSreEnvironmentController`/mapeamentos de vigência antigos como efeito lateral. Métricas DORA permanecem independentes do Branch Monitor. Nenhum workflow de escrita novo nesta etapa.

## Pendências
G0 ainda não demonstra join de History para Component, acesso à versão do XML nem evidência por componente no deployment. Não implementar o Diff de conteúdo antes desses gates.
