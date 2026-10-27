# Plano incremental de UX — Branch Monitor / Componentes

**Baseline homologada:** M2D (explorador ZIP), M2E (foco/filtragem), M2F (ficha e históricos); M2B.1 (comparação de conteúdo) tecnicamente implantado. A experiência de Diff unificado foi considerada confusa e substituída por proposta lado a lado. **Não presumir homologação dos incrementos seguintes.**

## Ordem de execução e critérios de aceite

| Marco | Guias | Mudança | Aceite verificável |
|---|---|---|---|
| V3.1 · Diff lado a lado | 05, 13 | Base esquerda e Destino direita; linhas alinhadas, +/−, alternar apenas alterações; inverter históricos | Sem mistura de textos, números independentes, nenhum HTML executado; Jest e validação DevSreFeat |
| V3.2 · Navegação contextual | 01–06, 08 | Inventário → ficha → históricos → arquivos/compare em área focada; preservar filtros e seleção | Voltar não descarta paginação, busca ou selection; focos e breadcrumbs consistentes |
| V3.3 · Estados e erros | 07, 09–12 | Carregamento, filtro vazio, sem acesso, ZIP sem texto e arquivo grande com ações reais | Cada estado tem título, explicação e saída praticável, sem mensagens falsas |
| V3.4 · Mobile | 14 | Fluxos empilhados, controles touch, troca entre painéis sem rolagem horizontal forçada | 360px / 390px / 768px, navegação por teclado e leitor de tela |
| V3.5 · Histórico robusto | 04, 05, 11–13 | Arquivos só em um ZIP, comparabilidade, percurso por arquivos e resumo confiável | Arquivos `added/deleted/changed/unchanged` baseados em presença exata do caminho; sem extrapolar identidade |
| V3.6 · Identidade | 03, 05, 13 | Correlação com FullName, versões e operações via dados verificados | Sinais explícitos de grau de evidência; sem inferência por `Name` nem por `Last_Commit` |

## Estado dos componentes

- `devSreComponentDescriber`: UI, filtros, metadata, histórico, preview ZIP, Diff. Refatorar em subcomponentes apenas com testes de integração e aprovação de dependências.
- `historyDiff.js`: cálculo LCS limitado e transformação em duas colunas; testes para acréscimo, remoção, troca, arquivo idêntico, limitações.
- Apex controlador, reader e PermissionSet: **sem mudanças necessárias para V3.1**.
- `devSreBranchMonitor`: shell e abas existentes devem permanecer intactos; preservar target `lightning__Tab`.

## Regras de execução

1. Não incluir 14 cenários em um deploy monolítico: cada PR foca um marco com reversibilidade.
2. Pipeline: PR → M4 + ESLint/Jest → merge com SHA revisado → PLAN ChatOps DevSreFeat → **DEPLOY somente com intenção específica e gates limpos** → COMPARE read-only → homologação funcional.
3. Não expor código-fonte de ZIP/Component real em artefatos e logs públicos.
4. Capturar evidência de cada um dos estados de UX, inclusive condições de erro e arquivos acima do limite.
5. A comparação em duas colunas é visual; não supor que linhas emparelhadas representam renomeações ou significado semântico.
6. Preservar escopo de acessibilidade, `with sharing`, CRUD/FLS/USER_MODE e paginação.

## Casos de regressão prioritários

- 2 históricos do mesmo Component, arquivo textual presente nos dois, com 1 linha removida e 1 adicionada;
- histórico com arquivo só de um lado — estado claro e nenhuma leitura indevida;
- ambos os arquivos idênticos — confirmação positiva;
- só uma relação History / histórico inacessível — ação Comparar não aparece;
- ZIP malformado / sem texto / acima de limite — erro explicativo sem vazar nomes/bytes;
- troca de componente enquanto requisição está ativa — resposta obsoleta ignorada;
- elementos HTML dentro do arquivo são exibidos **somente como texto**, sem execução;
- mobile: lista → detalhe → ZIP → Diff → voltar preservando contexto.
