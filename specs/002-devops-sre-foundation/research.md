# Research / confirmação de contratos

## Confirmado em GitHub (master consultada em 23/10/2026)

- Projeto `sfdx-project.json` source API 67.0.
- `ClonePipelineController.cls` usa os objetos gerenciados `Flosum__Pipeline__c` e `Flosum__PipelineStep__c` com `WITH USER_MODE`.
- `ClonePipelineControllerTest.cls` prova a expectativa de payload de Steps para número, descrição, ação, pass/fail.
- `config/salesforce-devops/catalog.json` lista `DevSreFeat` sandbox com Environment `sf-devsrefeat-read`; **não** comprova configuração ativa de secrets.

## Referências oficiais

- Salesforce LWC Tab: https://developer.salesforce.com/docs/platform/lwc/guide/use-config-custom-tab.html
- SLDS 2 e Cosmos: https://developer.salesforce.com/docs/platform/lwc/guide/create-components-css-slds1-slds2.html
- Apex user-mode e sharing: https://developer.salesforce.com/docs/platform/aura-platform/guide/apex-crud-fls.html
- DORA: https://dora.dev/guides/dora-metrics/

## Não verificado / bloqueios do roadmap

- Fonte Salesforce/Flosum de deployments concluídos em produção e carimbos temporais.
- Fonte de incidentes vinculados a falhas em produção, hora de restauração e retrabalho.
- API names reais para execução e associações a Change/Commit/Release.
- Permissões de usuários de negócio sobre os campos de Step.
- Estado do tema Cosmos na sandbox.
