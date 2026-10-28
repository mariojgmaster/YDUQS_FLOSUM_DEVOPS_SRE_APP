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


## V3.2 — entrega técnica (rolagem independente + workspace)

**Guias:** 01–06, 08, 13–14. A etapa V3.2 muda **somente** `devSreComponentDescriber` e não altera contratos Apex.

- No Diff, Base e Destino são regiões `role=region` independentes, focáveis por teclado, cada uma com `overflow-x:auto` e `overflow-y:auto`. O deslocamento de uma coluna **não** desloca a outra. Antes havia uma única região de scroll.
- A pré-visualização individual do ZIP também é região scrollável X/Y, separada da lista de arquivos.
- Na visualização expandida, navegação contextual `Inventário / Componente / Ficha|Históricos|Arquivos ZIP|Comparar`. Áreas que ainda não foram abertas aparecem indisponíveis; nunca é simulada uma consulta ou comparação.
- Voltar ao Inventário preserva filtros, paginação, seleção e detalhes carregados. Se trocar de componente, respostas pendentes e comparações antigas continuam invalidadas.
- Cada painel começa com linhas alinhadas por bloco do Diff, mas **o scroll é independente** e não tenta manter sincronização automática ao rolar. Isso é intencional.
- Testes Jest cobrem isolação dos painéis DOM, navegação e preservação de estado. Validar visualmente rolagem X/Y no navegador durante homologação — Jest não mede layout/CSS.
- Workflow completo: CI + Jest, PLAN DevSreFeat, deploy real somente mediante autorização específica com commit e pacote fixos, COMPARE e homologação.

**Status:** código/PR de V3.2 em preparação; esta documentação não implica implantação ou aprovação funcional.


## V3.2.1 — sincronização vertical e arquivos de até 6 MiB

- Rolagem vertical de Base/Destino **sincronizada** pelo `scrollTop`, com as linhas do Diff alinhadas; rolagem horizontal própria em cada painel. Os painéis continuam independentes para leitura horizontal.
- Sem teto fixo de linhas: estratégia LCS exata em blocos pequenos + âncoras estáveis para blocos grandes; se não houver correspondência comprovável, apresenta remoções/adições sem presumir igualdade. Todas as linhas permanecem acessíveis por páginas de 250 pares (isso é virtualização da apresentação, não truncamento dos textos).
- A política Apex de tamanho de ZIP e de texto extraído sobe de 1 MiB/64 KiB para **6 MiB (6.291.456 bytes) por arquivo**. O número de entradas ZIP continua limitado a 200, e a whitelist de tipos permanece.
- **Limitação técnica importante:** Apex síncrono dispõe de 10 MB de heap no Winter '27, sujeito às configurações efetivas da org. Carregar ZIP, descompactar e serializar texto pode superar esse heap mesmo quando cada arquivo está abaixo de 6 MiB. Uma checagem pré-extração retorna mensagem legível quando falta memória; **não declarar capacidade garantida de 6 MiB reais sem prova com arquivo desse tamanho**. O próximo passo arquitetural para arquivos que excedem o heap é download autorizado do Attachment e extração em streaming no navegador ou backend específico, mantendo verificação de acesso.
- Metadados de anexos são consultados primeiro em USER_MODE sem `Body`; apenas o ZIP escolhido recebe uma segunda consulta ao campo `Body`. Evita trazer até onze ZIPs inteiros em uma única transação.
- Testes: Diff acima de 600 linhas, páginas 1..N, rolamento Y espelhado e X isolado, arquivo sintético acima de 64 KiB, políticas/segurança. Homologar com arquivo próximo de 6 MiB na DevSreFeat antes de prometer suporte universal.

**Status:** alvo de validação técnica (PR/PLAN). Deploy real somente após autorização exata de pacote e commit.


## V3.3 — estados vazios, carregamento e recuperação (candidato)

**Escopo:** apenas `devSreComponentDescriber` (LWC, estilos e Jest). Sem Apex, DML, mudanças de contrato ou rearranjo de layout.

- Inventário: loading skeleton, busca vazia x filtro sem resultados x falha de API, com ações específicas (atualizar ou limpar filtros).
- Ficha e históricos: estados de carregamento e erro; histórico sem vínculo acessível é explicitamente diferente de histórico com zero ocorrências; nova consulta sob demanda.
- ZIP: distinguir ZIP vazio de ZIP com entradas não textuais, filtro sem resultados e leitura negada/falha/limite; tentar novamente conserva o `historyId` e o caminho solicitado, sem forjar leitura concluída.
- Comparar: consulta falha x ausência de caminhos textuais comuns; ação de reconsultar índices dos ZIPs mantendo a seleção dos históricos; Diff já homologado (rolagem vertical compartilhada e X independente) intocado.
- Acessibilidade: `role=status` nos vazios, `role=alert` nos erros, legendas acionáveis, skeleton não exposto a leitores de tela, `prefers-reduced-motion`.
- Cobertura nova em Jest para estados de consulta pendente, retries de pesquisa/ficha/ZIP/Diff, ZIP somente binário e limpeza do filtro.

**Critério de aceite:** PR e Jest/CI aprovados; validação sandbox + inspeção visual nos guias 07, 09, 10, 11 e 12; comprovar tratamento com um ZIP acima do limite técnico efetivo. **PR não representa deploy nem homologação Salesforce.**


## V3.4 — responsividade e fluxo mobile (guia 14)

**Pacote:** `branch-monitor-v3-4-responsive`, isolado a `devSreComponentDescriber` (LightningComponentBundle), sem Apex/Flosum DML, sem alterar os contratos do Diff ou as outras abas.

- Em viewport de até 48rem (referências: 360px, 390px e 768px), inventário em cartões usando o mesmo `table` semântica; colunas ganham rótulos visuais, sem scrollbar horizontal da página.
- Selecionar um componente em viewport estreita abre automaticamente seu workspace focado. Voltar ao inventário mantém pesquisa, paginação e resultados carregados.
- Ficha, históricos e navegação passam a uma coluna/grade 2x2; ações de toque e textos longos têm espaço adequado.
- Leitor de ZIP empilha lista e texto; a lista mantém rolagem própria e o código longo conserva a rolagem do preview.
- Diff desktop continua **duas colunas** e **uma única rolagem vertical**, com scroll X independente por coluna. Somente em mobile, os botões `Ver base`/`Ver destino` alternam qual coluna ocupa a largura disponível, conservando ambas as sequências no mesmo par de linhas e a posição vertical do viewport. Botões têm `aria-pressed`; nenhuma comparação é recalculada ao alternar.
- Testes Jest novos para autoexpansão/voltar e alternância Base/Destino; guardas estáticas para estrutura responsiva e scroll único. Lint/Jest não medem tamanho, contraste ou quebra real de tela.

**Homologação funcional manual obrigatória:** no navegador DevSreFeat, testar 360px, 390px, 768px e desktop. Verificar inventário (sem scroll lateral externo), filtros, seleção→ficha→históricos→ZIP→comparação, botões Base/Destino, conteúdo longo, scroll horizontal só dentro de código e vertical único preservado; voltar sem perder filtros. Validar também teclado e zoom 200% (a mesma largura CSS, se aplicável). Uma PR verde/deploy OK não comprova homologação visual no dispositivo.

**Deploy:** PR → CI/Jest/policy → merge com SHA pinado → ChatOps PLAN (RunSpecifiedTests) → DEPLOY aprovado → COMPARE read-only. Nenhum workflow improvisado.
