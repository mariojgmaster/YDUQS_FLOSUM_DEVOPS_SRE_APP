# Entrega — Pipeline Monitor principal

Implementação do PR #121 a partir da referência visual `docs/visual-guides/2_Pipeline_Monitor_Screen.png`. O monitor é renderizado antes das abas existentes, preservadas sem remoção ou reorganização. Não altera CustomTab, CustomApplication, objetos, campos, permissões, dados reais ou o fluxo Clone Pipeline.

## Evidências técnicas

- SHA implantado: `7119bde3e20867cab1277c77271f6c14d1adb298`.
- Pacote universal `pipeline-monitor-main`: DevSreDeploymentController, DevSreDeploymentTest, devSreDeliveryHub e devSrePipelineOverview. Módulo de estilos e permissões de acesso à classe já existentes foram reutilizados. Workflows preservados.
- Local: 54 testes Jest em sete suítes, ESLint, 112 testes Python e política de manifesto aprovados. CI do PR #121 aprovado: #40147378642 / #40147378648.
- Comparação anterior: Issue #122 / [#40147476431](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40147476431). Três componentes instalados diferentes, dentro do escopo autorizado. Artifact #12581148677 baixado/lido; ZIP SHA-256 926d375dfd4833d6fb16d019df46a64505e85b481e5f5f9c04e4889ca699f352. O módulo novo foi excluído da comparação inicial, pois ainda não existia.
- Validação: Issue #123 / [#40147534105](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40147534105). success=true/done=true/Succeeded, 12 testes, zero erros e alertas de cobertura. Artifact #12580214511 baixado/lido; ZIP SHA-256 f43bfc3d3f8783224cb28f50208434e9051544909e506ce73310e63ebeb1a641.
- Deploy real: Issue #124 / [#40147655682](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40147655682). Dry-run e testes repetidos no fluxo; REAL_DEPLOY success=true/done=true/Succeeded, 12 testes, zero erros e alertas de cobertura. Marcadores SDOA_REAL_DEPLOY_SUCCEEDED e SDOA_M5_DEPLOY_SUCCEEDED confirmados. Artifact #12581164112 baixado/lido; ZIP SHA-256 e5147906eb190c25e5cb18a62d5563cb6bf51852a2726dae89c4c83cd5c15c5c.
- Comparação posterior: Issue #125 / [#40147766970](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40147766970). Quatro componentes recuperados e comparados. Relatório sanitizado baixado e lido: ["ApexClass:DevSreDeploymentController:metadata", "ApexClass:DevSreDeploymentTest:metadata"]. A lista de diferenças contém somente os XML de metadados Apex: os dois bundles e o código das classes coincidem. Essas duas categorias de XML já apareciam na comparação anterior. O kit sanitizado não informa os valores divergentes; a causa não foi presumida e não foi afirmada equivalência integral de metadados. Revisão específica de XML permanece aberta, sem reenviar o deploy já confirmado. Artifact #12580514183; ZIP SHA-256 2519fff6b53060572a02461f67ad426eb369fad044b39a844131db7849cedb8c..

O kit publica somente retorno sanitizado neste repositório público. Os relatórios foram efetivamente baixados e lidos; não se afirma acesso ao JSON Salesforce bruto integral ou Deployment ID. As evidências de execução não homologam a aparência ou a jornada de uso na org.

## Homologação pendente

Atualizar a aba Pipeline Monitor na DevSreFeat. Conferir o monitor principal antes das abas anteriores; período, cartões, busca/filtros, linhas e abertura de log; filtros pendentes; resumo independente da paginação/resultado; expansão de dez para até 50 linhas e cursor; exportação da página; atualização manual e opt-in de 60 segundos; navegação a Incidentes. Validar teclado, zoom de 200% e largura reduzida no tema real da org.

Usar intervalo que contenha entregas conhecidas. Sem dados, apresentar vazio; nunca carregar exemplos do protótipo como registros reais. Fila permanece indisponível; squad, quantidade de componentes e progresso não são simulados. Novo deployment segue o fluxo Flosum e está desabilitado no monitor com orientação explícita.

## Reversão

Em regressão comprovada, preparar PR restaurando os dois Apex e o Hub do commit anterior ao #121, validar e implantar pelo mesmo kit. O bundle novo pode permanecer sem referência, sem exclusão destrutiva. Reversão não executada automaticamente.

Status: implantado / homologação visual e funcional pendente.
