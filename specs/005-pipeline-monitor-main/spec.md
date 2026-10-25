# SPEC-005 — Tela principal de Pipeline Monitor

## Origem e objetivo

Pedido do usuário: manter as abas atuais por enquanto e montar a tela principal conforme o protótipo aprovado. Referência visual autoritativa: `docs/visual-guides/2_Pipeline_Monitor_Screen.png`. A composição principal é operacional: período/ações, cabeçalho de observabilidade, cinco cartões, busca/filtros e lista de entregas com detalhe de origem. Não recriar chrome Salesforce dentro da LWC.

## Requisitos e aceite

- Preservar as três abas e seus componentes; montar o monitor antes delas, no mesmo host da aba original. Não alterar CustomTab/App, Clone Pipeline ou Incident Intake.
- Fonte real: Deployment do Metadata Log. Nome da Branch quando disponível, organização, ambiente na conclusão, resultado, duração válida e data de referência. Abrir o log Flosum com NavigationMixin.
- Resumo de todos os registros acessíveis do período/busca/organização/ambiente, independente do cursor e do filtro de resultado. Em andamento, fila indisponível, sucessos, falhas e taxa operacional; informar parciais/não executados/desconhecidos no contexto. Não chamar contagem de logs de métrica DORA certificada.
- Taxa = sucessos / (sucessos + falhas + parciais); denominador vazio é indisponível. Acima de 2.000 candidatos, não apresentar contagem parcial como total; lista paginada continua utilizável. Cada card tem explicação.
- Não inventar fila separada, squad, componentes, progresso percentual ou fonte de release. O protótipo usa dados simulados; esta entrega usa somente os campos comprovados da integração.
- Busca de log/Branch no servidor com binds e tratamento literal de curingas. Filtros de período UTC, ambiente, organização e resultado. Mudança de filtros exige aplicar e invalida respostas anteriores.
- Exibir dez linhas inicialmente de cada página de até 50; permitir mostrar as demais antes de avançar o cursor. Página vazia com continuação não bloqueia a consulta.
- Atualização automática opt-in de 60 segundos; não executar quando oculta, carregando ou com filtros pendentes, e limpar ao desconectar. Atualizar manualmente e informar última consulta.
- Ações: navegar à aba de Incidentes existente, exportar somente a página consultada, atualizar. Novo deployment permanece indisponível com orientação ao fluxo Flosum; nenhuma escrita Flosum é criada pelo produto.
- Exportação CSV limitada à página acessível, com neutralização de fórmulas, MIME permitido por LWS e blob URL revogável. Sem persistir dados no servidor/repositório.
- Estados loading/erro/vazio/filtro pendente/limite separados, status textual, rótulos acessíveis, foco visível e layout responsivo.

## Limites

Sem novos objetos, permissões, alterações de configuração real, KPI DORA ou criação/execução de deploy por este produto. Aprovação técnica não equivale a homologação visual na org.
