# Modelo de dados inicial e limites

| Entidade | Fonte confirmada em código | Uso neste incremento |
| --- | --- | --- |
| Pipeline | `Flosum__Pipeline__c` | Id, Name |
| Pipeline Step | `Flosum__PipelineStep__c` | Id, parent `Flosum__Pipeline__c`, número, descrição, ação e próximos Steps em pass/fail conforme FLS |
| Deployment | Ainda sem contrato de origem confirmado | **Não utilizado** |
| Incidente / rollback | Ainda sem contrato de origem confirmado | **Não utilizado** |
| Commit / release | Correlações futuras dependem de validação na org | **Não utilizado** |

Pipeline → Steps é 1:N. Transições pass/fail conectam Step a Step, mas **não** significam que o Step tenha sido executado, nem seu resultado.

Tipos e estados de resposta: DTO PipelineSummary; PipelinePage com `hasMore`; PipelineDetail com `steps` e `hasMore`. Ausência de campo por FLS não é preenchida com valor inferido.
