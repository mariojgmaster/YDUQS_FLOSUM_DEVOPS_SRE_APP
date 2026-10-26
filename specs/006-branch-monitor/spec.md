# SPEC-006 — Branch Monitor (UI/UX aprovado, implementação incremental)

**Status:** especificação para desenvolvimento; não equivale a funcionalidade instalada. **Origem:** quatro wireframes anotados aprovados em 25/10/2026. **Escopo:** aplicativo Salesforce DevOps & SRE Analytics, nova aba principal **Branch Monitor** entre DORA Cockpit e Pipeline Monitor, com quatro visões internas. **Alvo de experimentação:** sandbox DevSreFeat.

## Objetivo e personas
Consultores e administradores devem entender onde um componente está versionado, quais branches o possuem, as diferenças comprováveis entre branches e as operações Flosum associadas. Perfil Reader realiza apenas consultas; funções de execução, merge, deploy, alteração de componentes e rollback não fazem parte do Branch Monitor.

## Fluxos aprovados
1. **Visão geral (BM-01):** cabeçalho + filtros (período, organização/branch quando aplicável), resumo de branches acessíveis, movimentações e operações, atividades recentes, avisos de qualidade; navegação contextual às outras visões.
2. **Branches (BM-02):** busca e seleção de Branch real; detalhe e inventário de componentes, logs por tipo de processo/resultado, timeline de alterações (somente quando correlação validada), ações abrir no Flosum e comparar.
3. **Comparar (BM-03):** dois lookups de Branch Flosum, explicitando A e B, seleção de revisão/snapshot quando a fonte existir; inventário Added/Removed/Modified/Unchanged/Unknown; filtros por tipo/resultado; Diff textual lado a lado somente com conteúdo versionado verificável; modo semântico por tipo liberado em fase posterior.
4. **Componentes / Branch Describer (BM-04):** procurar por **tipo de metadata + FullName + namespace**, com possibilidade de sugestões limitadas; distinguir componentes com mesmo nome; listar Branches em que o componente está presente, versões e commits documentados, logs/deploys comprovadamente ligados à versão, evidências e lacunas. Linha do tempo navegável.

## Requisitos funcionais
- **FR-001** Preservar as abas existentes e inserir Branch Monitor na ordem aprovada sem reproduzir shell global Salesforce dentro de LWC.
- **FR-002** Usar somente IDs e registros reais visíveis ao usuário, sem mock em runtime.
- **FR-003** Todas as buscas devem usar filtros aplicados automaticamente (texto com debounce), limites, cursores estáveis e sinalização de páginas incompletas.
- **FR-004** Todas as referências a organizações usam o lookup nativo para `Flosum__Organisation__c`; Branches usam objeto `Flosum__Branch__c`.
- **FR-005** Exibir estados claros: carregando, vazio, erro, acesso negado, fonte incompleta e correlação não comprovada.
- **FR-006** Não concluir que um componente foi deployado apenas porque integra uma Branch; a associação exige evidência identificável de execução/versão.
- **FR-007** Não usar `Flosum__Last_Commit__c` como identidade autoritativa de versão de componente.
- **FR-008** No comparador, não denominar Modified/Unchanged com base só no mesmo FullName. Sem conteúdo/checksum confiável, usar Unknown/Não comparável.
- **FR-009** Tratar operação `Validate` e `Deployment` separadamente e preservar valores de processo desconhecidos; CreatedDate, Start_Date e Completed_Date são instantes distintos.
- **FR-010** IDs Salesforce, corpo de metadata, código, segredos e detalhes de clientes nunca serão publicados em logs de GitHub Actions/repositório público.
- **FR-011** Links devem abrir o objeto real com `NavigationMixin`; texto extenso deve truncar com reticências e revelar o valor completo de modo acessível.
- **FR-012** Permissões: `with sharing`, CRUD/FLS sob `WITH USER_MODE`; somente leitura, sem criar infraestrutura externa ou objetos espelho sem decisão arquitetural posterior.

## Regras de integridade de comparações
- Inputs A/B devem referir-se a Branches distintas, com referência temporal/versão de cada lado quando disponível.
- Identidade canônica: metadataType + fullName + namespace; definir regras por tipo (CustomField, LWC, Flow etc.).
- Ausente em A e presente em B = somente-em-B, **não** implica novo deploy. Ausente em B pode significar exclusão se ambas as fontes forem snapshots completos, caso contrário Unknown.
- Diffs de texto dependem de duas versões de conteúdo obtidas e identificadas; primeiro normalizar formato preservando significado, nunca executar código trazido da fonte.
- A linha do tempo do Branch Describer deve distinguir fatos `Observed` de correlações `Inferred` e lacunas `Unverified`.

## Não objetivos
Deploy/merge/rollback, alterações de dados Flosum, inferir disponibilidade/saúde da org, métricas DORA certificadas, resumo LLM sem evidências, comparações parciais apresentadas como integrais.

## Critérios de aceite verificáveis
- Reader enxerga somente registros acessíveis. Nenhuma ação de escrita é exposta.
- Busca por componente de nome repetido devolve identidades distintas ou ambiguidade explícita.
- O lookup tipado History→Component está confirmado, mas não prova preenchimento, cardinalidade ou revisão; exigir teste de correlação antes de usar dados históricos.
- A comparação de inventário com um lado incompleto retorna `incomplete`, nunca contagens globais definitivas.
- Falha de acesso ao conteúdo bloqueia Diff textual, mas não as visões de identidade e inventário comprovado.
- Todas as telas responsivas, com teclado, foco, cabeçalho único e reticências nas tabelas.
- Nenhuma implantação persistente em DevSreFeat sem autorização específica de pacote/SHA e dry-run aprovado.

## Referências visuais aprovadas
Quatro wireframes anotados aprovados na conversa: dashboard/Visão geral, navegação/Branches, comparador de metadados e explorador/describer de componentes. Estas referências são canônicas para disposição e comportamento; qualquer divergência relevante exige revisão visual.
