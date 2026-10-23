# UI/Application Contract: Clone Pipeline

## `getPreview(sourcePipelineId)`

Input:

- `sourcePipelineId`: non-null Pipeline record ID.

Success output:

- `sourceName`: source Pipeline name.
- `suggestedName`: source name plus ` - Cópia`, truncated if necessary to fit 80 characters.
- `stepCount`: number of associated Pipeline Steps.
- `maxNameLength`: `80`.
- `steps`: lista de pré-visualização não mutável, ordenada pelo número do Step quando legível. Cada item contém:
  - `number`: número do Step, quando o usuário tiver acesso ao campo; pode ser `null`.
  - `description`: descrição do Step, quando legível; pode ser `null`.
  - `action`: tipo do Step (`Flosum__Step__c`), quando legível; pode ser `null`.

A consulta de `steps` usa `WITH USER_MODE`, valida `isAccessible()` campo a campo e é limitada a 100 Steps. O cliente trata `steps` ausente como compatibilidade com versões anteriores do Apex. Nenhuma configuração é modificada pela pré-visualização.

Failure categories exposed safely: invalid input, inaccessible/missing source, insufficient permission, unexpected processing failure.

## `clonePipeline(sourcePipelineId, newName)`

Input:

- `sourcePipelineId`: non-null Pipeline record ID.
- `newName`: trimmed, nonblank, at most 80 characters.

Success output:

- `pipelineId`: cloned Pipeline ID.
- `pipelineName`: persisted clone name.
- `stepCount`: number of cloned Steps.

Transaction guarantee: an error returns no result and leaves no Pipeline or Step created by the attempt.

## UI States

- Loading preview: controls disabled, spinner and assistive text shown.
- Ready: name editable, source Step count visible, cancel and clone controls available.
- Submitting: all controls disabled; duplicate invocation ignored.
- Success: modal closes, success toast appears, navigation opens the clone.
- Error: modal remains open where recovery is possible and a safe error message is shown.
