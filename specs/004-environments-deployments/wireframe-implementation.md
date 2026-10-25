# Pipeline Monitor — Deployments e Ambientes (wireframes de 24/10/2026)

## Escopo
Atualização das abas internas Deployments e Ambientes conforme wireframes aprovados, sem modificar o monitor operacional principal, a aba Pipeline original, objetos, permissões, dados ou regras de integridade temporal. Fonte: `Flosum__Metadata_Log__c` para entregas e `DevSre_EnvironmentMapping__c` para classificação.

## Deployments
- Pesquisa no servidor por nome de Metadata Log/Branch, inclusive combinada com filtro exato de ID da Branch; método Apex `listDeploymentsWithSearch`.
- Datas inclusivas por dia UTC; até 366 dias; filtros de organização, ambiente e resultado.
- Lista paginada por cursor: até 50 resultados e até 200 registros de origem examinados por chamada; páginas vazias com continuação são possíveis e exibidas.
- Detalhes contextuais do log selecionado, incluindo qualidade/fonte, resultado, organização, Branch, timestamps, duração e navegação ao Metadata Log.
- Exportar página (somente registros já retornados): CSV em UTF-8 com proteção contra interpretação de fórmulas; não equivale a exportação global.
- Erros, filtros alterados, ausência de classificação e classificação ambígua informados sem valores inventados.

## Ambientes
- Classificações atuais como visão inicial; histórico (encerradas, futuras ou todas).
- Pesquisa local nas classificações carregadas; filtro exato por organização com nova consulta e ações Histórico/Atualizar/Abrir registro.
- Formulário lateral exclusivo para permissão `DevSre_ManageEnvironments`; início obrigatório sem padrão implícito, término opcional, justificativa obrigatória e foco contextual.
- Em edição, identidade imutável (organização, classe e início); vigências anteriores não podem ser reabertas. Validação de sobreposição permanece sob Apex/trigger.
- Intervalo de classificação [início, fim), aplicado à data de conclusão do log, preservando entregas anteriores.

## Publicação
- Pacote estrito de quatro componentes: `manifest/sf-pipeline-monitor-detail-ux.xml`.
- Nome no catálogo M4/M5: `pipeline-monitor-detail-ux`.
- Testes Apex: `DevSreEnvironmentTest`, `DevSreDeploymentTest`.
- A inclusão do método Apex **exige deploy conjunto** com os LWCs; atualizar apenas a interface causaria erro na busca.
- CI do PR: ESLint, Jest e política. Não constitui dry-run nem teste visual em sandbox.
- Testar em DevSreFeat: acesso Manager e Reader, organizações reais, log de sucesso/falha, datas sem conclusão, ausência de classificação, paginação, CSV, 200% zoom, teclado, layout mobile e tema da org.

## Limites reconhecidos
- O backend não apresenta métrica DORA certificada nem total global de resultados filtrados.
- O carregamento de opções de organizações fica limitado a 50 por consulta; usar a busca de organizações para localizar outro registro.
- Nenhum dado ilustrativo dos wireframes é criado.
