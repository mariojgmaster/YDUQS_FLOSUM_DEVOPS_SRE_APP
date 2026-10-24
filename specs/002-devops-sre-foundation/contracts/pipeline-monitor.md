# Contrato funcional — consultas Pipeline Monitor

## Apex

- `DevSrePipelineMonitorController.listPipelines(String searchTerm)` → `PipelinePage { pipelines: PipelineSummary[], hasMore: Boolean }`; cada summary contém `id, name`.
- `DevSrePipelineMonitorController.getPipelineDetail(Id pipelineId)` → `PipelineDetail { id, name, steps: StepRow[], hasMore: Boolean }`; cada Step contém `id, stepNumber, description, action, nextOnPass, nextOnFail`.
- Ambos `@AuraEnabled` somente leitura; Apex com sharing e SOQL em user mode; mensagens seguras de falha.
- Busca no servidor; máximo 50 pipelines e 100 Steps; `hasMore` sinaliza que os registros retornados não são a totalidade.
- Nenhuma ação de deploy, rollback, atualização ou inserção está exposta.

## LWC

- Botão Pesquisar: executa nova consulta e redefine seleção.
- Botão Atualizar: repete consulta do termo atual (não usa cache Apex).
- Ação de linha Visualizar etapas: carrega detalhe do Pipeline.
- Ação de linha Abrir no Flosum: navegação padrão ao registro `Flosum__Pipeline__c`.
- Estados: spinner / erro / vazio / resultado / truncado. As colunas de pass/fail identificam o Step de destino somente quando retornado e legível; caso contrário usam estado não resolvido, jamais inventado.
