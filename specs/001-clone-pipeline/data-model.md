# Data Model: Clone Pipeline

## Pipeline

Existing managed entity `Flosum__Pipeline__c`.

- `Id`: source identity; never copied.
- `Name`: copied into the suggested name and replaced by the user-confirmed value; maximum 80 characters.
- Other readable/createable, non-calculated fields: copied when the current user is allowed to read and create them.
- Owner/audit/system values: not explicitly copied.

## Pipeline Step

Existing managed entity `Flosum__PipelineStep__c`.

- `Id`: source identity; never copied.
- `Flosum__Pipeline__c`: always replaced with the cloned Pipeline ID.
- `Flosum__Number__c`: copied and used for deterministic query order.
- `Flosum__Next_Step_Id_On_Pass__c`: remapped through source-ID → clone-ID map; cleared when the source target is outside the cloned set.
- `Flosum__Next_Step_Id_On_Fail__c`: remapped through source-ID → clone-ID map; cleared when the source target is outside the cloned set.
- Other readable/createable, non-calculated fields: copied when permitted.

## Relationship and Integrity Rules

- One Pipeline has zero to many Pipeline Steps.
- Each cloned Step belongs to exactly the cloned Pipeline for this operation.
- A cloned Step can point only to another Step created in the same operation.
- The complete parent/child graph is committed or rolled back as one unit.
- Maximum supported operation size for the first increment: 100 Steps.

## State Transitions

```text
Source selected → Preview loaded → Confirmation submitted
  → Parent created → Children created → References remapped → Complete
  ↘ any failure → Full rollback → Error returned
```
