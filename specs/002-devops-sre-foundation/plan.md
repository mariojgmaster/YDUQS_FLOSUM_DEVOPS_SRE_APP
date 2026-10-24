# Plano técnico — Primeiro incremento SLDS 2

## Evidências confirmadas em source control

- O repositório é Salesforce DX (`force-app`, API 67.0).
- `ClonePipelineController.cls` já utiliza `Flosum__Pipeline__c`, `Flosum__PipelineStep__c`, `Flosum__Number__c`, `Flosum__Description__c`, `Flosum__Step__c`, `Flosum__Next_Step_Id_On_Pass__c`, `Flosum__Next_Step_Id_On_Fail__c`.
- Essa evidência de código não equivale à validação atual de permissões, disponibilidade de registros ou execução na org.

## Arquitetura

`devSrePipelineMonitor (LWC)` → `DevSrePipelineMonitorController (Apex)` → `Flosum__Pipeline__c / Flosum__PipelineStep__c`.

Apex retorna DTOs enxutos. `listPipelines(searchTerm)` consulta server-side até 51 Pipelines para exibir no máximo 50, sinalizando truncamento. `getPipelineDetail(pipelineId)` consulta 1 Pipeline e até 101 Steps para renderizar até 100. Ambos verificam permissões e usam `WITH USER_MODE`. Não há transações de escrita.

LWC mantém estado local de busca, seleção, carregamento e erros e previne sobreposição de respostas assíncronas; mostra duas tabelas Salesforce: pipelines e etapas. Navegação via `NavigationMixin`.

## SLDS 2

Usar `lightning-card`, `lightning-datatable`, `lightning-input`, `lightning-button`, `lightning-spinner` e utilitários SLDS. Estilos próprios só para grid responsivo, sem alterar CSS dos componentes base. O app global e o App Launcher são componentes da plataforma; não são replicados.

## Deploy seguro

- Entregar via branch + PR, sem merge/deploy implícito.
- Manifesto específico: `manifest/sf-devops-sre-pipeline-monitor.xml`, somente novas classes e LWC.
- **Não** adicionar este pacote à allowlist de deploy existente sem revisão e autorização posterior.
- Após merge e aprovação explícita: planejar validação na DevSreFeat, com Apex tests; criar aba Lightning e adicionar a Lightning App por procedimento controlado ou metadata validada.
- `DevSreFeat` mapeado no catálogo existente para GitHub Environment `sf-devsrefeat-read`; configuração de secrets NÃO é inspecionável pelo conector e não será presumida, nem reutilizada implicitamente para produção.

## Riscos / pendências

- Flosum e FLS podem variar entre ambientes; testar com personas reais.
- Limites de resultados são deliberados para proteger LDV; paginação pode ser uma SPEC posterior.
- Campos de execução e status não foram verificados; monitor, inicialmente, significa **monitoramento de configuração**, não execução runtime.
- Testar comportamento da tab e Cosmos no Salesforce real.
