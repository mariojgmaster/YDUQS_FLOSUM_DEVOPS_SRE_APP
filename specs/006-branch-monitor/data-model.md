# Modelo lógico — Branch Monitor

Modelo de leitura derivado dos objetos Flosum; nomes a seguir são **DTOs propostos**, não novos objetos persistentes.

| DTO | Identidade e campos | Evidência obrigatória |
| --- | --- | --- |
| `BranchRef` | `id, name, organizationId?, updatedAt?, status?` | Id de `Flosum__Branch__c`; outros campos sujeitos a schema |
| `ComponentKey` | `metadataType, fullName, namespace?` | regras por tipo e normalização Unicode/case definidas |
| `BranchPresence` | `branchId, componentId, key, revisionRef?, observedAt?, completeness` | `Flosum__Component__c` + lookup Branch confirmado |
| `HistoryVersion` | `historyId, componentRef?, revisionRef?, commitRef?, timestamp?, payloadRef?, linkage` | contrato de `Flosum__Component_History__c` ainda pendente |
| `OperationEvidence` | `metadataLogId, branchId, processType, outcome, startedAt?, completedAt?, organizationId?` | Metadata Log; associação ao componente precisa de trilha adicional |
| `DiffResult` | `key, leftPresence?, rightPresence?, state, textDiff?, semanticDiff?, provenance` | A/B completos ou explicitamente incompletos |
| `ComponentDescriberResult` | `key, branchOccurrences[], history[], operationEvidence[], quality` | joins independentes, cada um com qualidade declarada |

## Estados
- `ADDED_ON_RIGHT`: existe somente em B com ambos snapshots completos.
- `REMOVED_ON_RIGHT`: existe somente em A com ambos snapshots completos.
- `MODIFIED`: conteúdo/canonical hash confiável diferente entre revisões identificadas.
- `UNCHANGED`: payloads canônicos verificados iguais.
- `UNKNOWN`: mesmo nome porém versões/conteúdo ausentes, ambiguidade ou acesso insuficiente.
- `INCOMPLETE`: uma ou duas consultas não demonstram cobertura completa.
- `CONFLICT_CANDIDATE`: mudanças distintas em ambas as linhas de desenvolvimento comprovadas; jamais classificar conflito real sem ancestral comum e semântica confirmada.

## Constraints
- `ComponentKey` não é Id Salesforce. Não unir linhas por Name puro; guardar também `componentId` e `branchId`.
- Revisão deve ter proveniência `object, recordId, sourceField, collectedAt, sourceTimestamp?`, não só texto genérico.
- Timestamps sempre UTC internamente; time zone local apenas na apresentação.
- `OperationEvidence` no Describer pode ter quality `DIRECT`, `CORRELATED`, `UNVERIFIED`. `CORRELATED` precisa de regra auditada; sem regra, ocultar join e marcar unverified.
- Evitar `LIMIT` silencioso: `hasMore`, `cursor`, `complete`, `inspected`; só apresentar totais se completo.
- Nenhum corpo de código/XML em logs públicos ou Platform Events. Sanitizar mensagens de erro.
