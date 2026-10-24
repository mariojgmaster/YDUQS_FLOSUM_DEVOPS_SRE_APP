# DevOps & SRE Analytics — UX canônica (Lightning Experience / SLDS 2)

**Direção de produto aprovada pelo proprietário em 23/10/2026:** manter o conceito visual Salesforce Cosmos / SLDS 2, priorizando a versão **Operacional** das telas e oferecendo a versão **Analítica** sob demanda.

> Este documento especifica a experiência pretendida. O protótipo HTML apresentado na conversa é uma referência visual, **não** uma integração com a sandbox e **não** um conjunto de LWCs implantados. A aparência exata depende da disponibilidade do tema Cosmos na org.

## Navegação Salesforce

- Usar **Lightning App** e barra de navegação padrão do Lightning Experience; não reproduzir app launcher, global header ou navegação principal em HTML customizado.
- Itens previstos: **DORA Cockpit**, **Pipeline Monitor**, **Lead Time Tracker** e **Incidents & Rollbacks**.
- **Operacional** é a visão padrão. Ação secundária **Analítica** abre análise contextualizada; não duplicar a infraestrutura de navegação global.
- Cabeçalho contextual e ações: atualizar, pesquisar, filtrar, abrir registro-fonte.
- Componentes recomendados: `lightning-card`, `lightning-button`, `lightning-input`, `lightning-combobox`, `lightning-datatable`, `lightning-accordion`, `lightning-spinner`, `lightning-icon`, `lightning-badge`; expandir apenas quando existir requisito.
- Não sobrescrever DOM/CSS de Lightning Base Components. SLDS 2: evitar hooks de componente `--slds-c-*`; preferir utilitários SLDS, variantes nativas e hooks **globais** documentados.

## Telas e suas duas visões

### 1. DORA Cockpit

**Operacional (padrão):** cinco métricas oficiais com período, serviço/aplicação, cobertura/fonte, tendência válida e drill-down para dados de origem. Exibir `dados insuficientes` se faltar evidência.

**Analítica:** evolução temporal, distribuição, variações contextualizadas, explicação das fórmulas, segmentação por serviço e análise de qualidade. Nunca ranquear pessoas.

**Métricas oficiais:** Change Lead Time, Deployment Frequency, Failed Deployment Recovery Time (Throughput); Change Fail Rate e Deployment Rework Rate (Instability). Throughput é dimensão, não sexta métrica.

### 2. Pipeline Monitor

**Operacional:** lista pesquisável de pipelines Flosum com acesso à estrutura e às etapas; futuramente, execuções e status **somente** após identificar objetos e campos reais de execução na org.

**Analítica:** detalhamento de Step, transições `On Pass`/`On Fail` e inspeção de gargalos, quando houver timestamps rastreáveis.

**Primeiro incremento funcional:** catálogo de `Flosum__Pipeline__c` + estrutura de `Flosum__PipelineStep__c`. Não inferir status de execução a partir da configuração do Pipeline. Abrir o registro Flosum pelo padrão `standard__recordPage`.

### 3. Lead Time Tracker

**Operacional:** mudanças rastreáveis do commit até implantação em produção, com duração por etapa **se** as fontes e correlações existirem.

**Analítica:** distribuição, percentis, outliers, atrasos, comparação entre períodos equivalentes. Não apresentar duração se faltar vínculo confiável mudança→deployment.

### 4. Incidents & Rollbacks

**Operacional:** incidentes relacionados a mudanças, estado de recuperação, evidência de falha em produção e navegação à origem **após** definir fonte.

**Analítica:** linha do tempo mudança→falha→recuperação, recorrência, categorias e relação com retrabalho. Erro de validação em sandbox não implica incidente de produção.

## Padrões de comportamento

| Estado | Comportamento |
| --- | --- |
| Carregando | spinner/status acessível, sem conteúdo fictício |
| Sem registros | empty state objetivo e caminho para filtros |
| Sem permissão | mensagem genérica e segura, sem enumerar registros protegidos |
| Fonte indisponível | erro recuperável / opção de tentar novamente |
| Parcial ou truncado | aviso explícito, nunca exibir totais parciais como globais |
| Sem qualidade de origem | métrica ausente e motivo visível |
| Ação operacional crítica | usar governança Flosum; não executar deploy/rollback diretamente pelo dashboard |
| Navegação | usar `NavigationMixin` e páginas de registro Salesforce |

## Restrições não negociáveis

- Métricas DORA dependem de definição, denominador, unidade, timezone, versão da regra e proveniência explícitos.
- `Flosum__Pipeline__c` e `Flosum__PipelineStep__c` representam configuração, não eventos de deployment.
- Preferir objetos gerenciados Flosum verificados antes de criar novo armazenamento ou custom object.
- Segurança: sharing, CRUD/FLS, user mode, menor privilégio, sem logs sensíveis.
- Primeiro incremento **somente leitura**; não instalar handlers que criem/alterem deployments ou objetos gerenciados.
- O documento `docs/design-system.md` é transversal; para a Lightning App implementada, Base Components e restrições SLDS 2 prevalecem sobre interpretações genéricas de bibliotecas externas.

## Rastreabilidade

- Constituição: `.specify/memory/constitution.md`.
- Desenvolvimento em loops: `docs/development-loop.md`.
- Referências anteriores: `docs/visual-guides/`.
- SPEC do primeiro incremento: `specs/002-devops-sre-foundation/`.
- A documentação de `specs/001-clone-pipeline/` permanece isolada e preservada.

Fontes oficiais: https://developer.salesforce.com/docs/platform/lwc/guide/use-config-custom-tab.html ; https://developer.salesforce.com/docs/platform/lwc/guide/create-components-css-slds1-slds2.html ; https://dora.dev/guides/dora-metrics/.
