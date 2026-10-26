# Contratos API propostos — Branch Monitor

**NÃO IMPLEMENTADOS:** assinaturas de contrato a confirmar na descoberta. Todos read-only, Apex `@AuraEnabled(cacheable=true)` onde seguro e dados de usuário por `USER_MODE`.

## `listBranches(organizationId?, search?, cursor?, pageSize)`
Retorno `{rows:[{id,name,organizationName?,lastActivityUtc?,quality}],hasMore,nextCursor,complete,inspected}`.
`pageSize` 1..50. Busca textual <=80 chars, com escapes e binds. Ausência de Timestamp não significa atividade zero.

## `getBranchDetail(branchId, periodStartUtc?, periodEndUtc?)`
Retorno `{branch,componentSummary?,operationSummary?,recentOperations[],sourceCompleteness}`. `operationSummary` separa Validate e Deployment; processo Unknown não entra em um dos dois por inferência.

## `searchComponents(metadataType?, fullName?, branchId?, cursor?)`
Só habilitar quando `Flosum__Component__c` tiver campo identidade confirmado. Retorno `ComponentKey, BranchPresence, hasMore, quality`. Pesquisa por texto deve informar limite e múltiplos matches.

## `describeComponent(key, branchFilter?, cursor?)`
Retorno `{key,branchOccurrences[],historyEvents?,operationEvidence?,capabilities,provenance}`, em que `historyEvents`/operational links podem estar `unverified`, não vazios falsamente.

## `compareBranches(leftBranchId,rightBranchId,options)`
Pré-condições: IDs válidos, distintos, ambos acessíveis. Retorno `{leftRef,rightRef,completeness,changes[],totals?,capabilities,limitations}`. Changes `ADDED_ON_RIGHT|REMOVED_ON_RIGHT|MODIFIED|UNCHANGED|UNKNOWN|INCOMPLETE` e `provenance`.

## `getComponentDiff(leftRevisionRef,rightRevisionRef,metadataType)`
**Bloqueado até G4:** retorna diff textual/semântico somente de revisões identificadas e de conteúdo comprovado. Não aceitar body injetado pelo cliente; fontes vinculadas a registros acessíveis.

## Erro/qualidade uniformes
`{code: INVALID_INPUT|ACCESS_DENIED|SOURCE_UNAVAILABLE|INCOMPLETE|AMBIGUOUS_VERSION|UNVERIFIED_LINK, messageSafe}`. Nunca retornar usernames/tokens/segredos ou raw query error ao LWC.

## Formato de qualidade
`{level: confirmed|candidate|unverified|unavailable|incomplete, sourceRecordId?, observedAtUtc?, reasoningCode}`. Campos ausentes omitidos, não tratados como fato zero.
