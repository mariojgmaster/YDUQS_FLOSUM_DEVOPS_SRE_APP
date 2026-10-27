# SPEC-006 · Branch Monitor > Componentes — Guia visual e UX

**Objetivo:** tornar a experiência Salesforce clara, eficiente e segura: descobrir componentes, analisar metadados Flosum, abrir arquivos históricos e comparar texto **realmente lado a lado**.

## Biblioteca visual (14 variações)

Este repositório contém **14 guias vetoriais SVG navegáveis**, derivados dos cenários conceituais aprovados, com dados ilustrativos. O manifesto [visual-manifest.json](./visual-manifest.json) associa cada variação ao PNG gerado originalmente e ao respectivo SHA-256. As imagens PNG originais permanecem no pacote independente `branch-monitor-componentes-14-originais.zip`, a ser importado por meio do [importador validado](../../../scripts/docs/import_componentes_originals.py) quando os bytes estiverem disponíveis no checkout; **não trate SVG como cópia pixel a pixel do PNG**.

| Nº | Cenário | Guia vetorial | Estado atual |
|---:|---|---|---|
| 01 | Inventário inicial | [Abrir](visual/01-inventario.svg) | Implementado |
| 02 | Resultados filtrados | [Abrir](visual/02-resultados-filtrados.svg) | Implementado |
| 03 | Detalhe do componente | [Abrir](visual/03-detalhe-componente.svg) | Implementado |
| 04 | Exploração ZIP | [Abrir](visual/04-explorador-zip.svg) | Implementado |
| 05 | Comparação de históricos | [Abrir](visual/05-comparacao-historicos.svg) | Em revisão V3 |
| 06 | Fluxo orientado | [Abrir](visual/06-fluxo-recomendado.svg) | Planejado |
| 07 | Loading / skeleton | [Abrir](visual/07-loading-skeleton.svg) | Parcial |
| 08 | Sem seleção | [Abrir](visual/08-sem-selecao.svg) | Implementado |
| 09 | Nenhum resultado | [Abrir](visual/09-sem-resultados.svg) | Implementado |
| 10 | Acesso indisponível | [Abrir](visual/10-sem-acesso-historico.svg) | Parcial |
| 11 | ZIP sem texto compatível | [Abrir](visual/11-zip-sem-arquivos.svg) | Parcial |
| 12 | Arquivo acima dos limites | [Abrir](visual/12-arquivo-excede-limites.svg) | Parcial |
| 13 | Diff avançado lado a lado | [Abrir](visual/13-diff-avancado.svg) | Em revisão V3 |
| 14 | Responsividade mobile | [Abrir](visual/14-mobile-responsivo.svg) | Parcial |

## Diretrizes de design

- Seguir o Design System existente no app e Lightning Design System/SLDS 2. Priorizar `lightning-*`, tokens e espaços de leitura. Sem criar uma segunda navegação global dentro da aba.
- Hierarquia: **pesquisar → escolher um componente → inspecionar ficha → escolher histórico → ZIP → comparação**. Nunca exibir todas as ferramentas com igual peso o tempo todo.
- **Componente = Name (número) + Flosum__Component_Name__c (nome humano)**; usar o nome humano como título e número como secundário.
- Filtros: busca no nome real, Component Type como picklist pesquisável; não assumir que o registro é FullName canônico.
- Histórico: relação tipada ao registro Flosum corrente. Não inferir commit Git, versão canônica ou deploy a partir da existência do histórico.
- ZIP: listar apenas arquivos disponíveis; pré-visualizar texto, sem executar conteúdo ou incorporar como HTML; manter políticas de acesso em Apex USER_MODE.
- Diff: **Base à esquerda, Destino à direita**, números de linha independentes, espaços alinhados para linhas sem par; estados `adicionado`, `removido`, `idêntico`, `indisponível`. Evitar tabela única de eventos coloridos.
- Cores de diff devem ter texto e indicadores complementares (não depender apenas de verde/vermelho); teclado, foco, zoom e contraste devem continuar operáveis.
- Nunca inventar affordances: “Baixar arquivo” só pode ser mostrado quando política, URL e permissionamento da operação estiverem realmente implementados. O mesmo vale para “navegar todas as versões”.

## Contratos técnicos protegidos

- Objetos Flosum continuam **read-only**. Nenhum DML nem leitura sem autorização.
- `DevSreComponentDescriberController`, `DevSreHistoryArchiveReader` e o registro `devSreBranchMonitor` existentes são preservados.
- Limites atuais de consulta/ZIP/texto continuam válidos. Nenhum aumento por motivos puramente visuais.
- O Diff de texto é comparado localmente no LWC, sobre duas respostas autorizadas do método existente.
- Deploy somente na sandbox explicitamente autorizada, com CI, RunSpecifiedTests, dry-run, deploy real aprovado e comparação do metadata pós-deploy.

Consulte [Plano de evolução](./implementation-plan.md) para critérios, dependências e fatiamento dos incrementos.
