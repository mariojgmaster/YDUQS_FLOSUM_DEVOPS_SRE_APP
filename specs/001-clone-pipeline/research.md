# Research: Clone Pipeline

## Decision 1: Screen Action rather than standard Clone or Flow

- **Decision**: Use a Lightning Web Component record Screen Action backed by Apex.
- **Rationale**: The standard clone action does not clone child records, while the operation needs two-pass self-reference remapping and atomic rollback. The modal also supplies preview and confirmation.
- **Alternatives considered**: Standard Clone (insufficient child behavior), Flow (possible but materially harder to make maintainable and testable for dynamic field copying and graph remapping), headless action (insufficient confirmation UX).

## Decision 2: Describe-driven field copying

- **Decision**: At runtime copy the intersection of fields that are readable, createable, non-calculated, and not explicitly managed by the clone algorithm.
- **Rationale**: This respects field security and remains compatible when the managed package adds optional configurable fields.
- **Alternatives considered**: Hardcoded full field lists (brittle on package upgrades), unrestricted `clone()` after broad queries (can copy fields the user may not create).

## Decision 3: User-mode security with sharing

- **Decision**: Run the class `with sharing`, query with user mode, perform DML as user, and fail when object-level read/create prerequisites are missing.
- **Rationale**: Sharing and CRUD/FLS are distinct controls; all are required by the project constitution.
- **Alternatives considered**: System mode plus `stripInaccessible` (can silently produce misleading partial configuration), `without sharing` (unjustified privilege escalation).

## Decision 4: Synchronous atomic transaction

- **Decision**: Clone a maximum supported set of 100 Steps in a single transaction with a savepoint and rollback.
- **Rationale**: Immediate user feedback and integrity outweigh async complexity at this bounded volume.
- **Alternatives considered**: Queueable Apex (unnecessary status/retry complexity and weaker immediate outcome), partial success (creates unusable pipelines).

## Confirmed Managed-Package Contract

- Parent: `Flosum__Pipeline__c`, creatable/queryable, Name length 80.
- Child: `Flosum__PipelineStep__c`, creatable/queryable.
- Parent lookup: `Flosum__Pipeline__c`.
- Ordering value: `Flosum__Number__c`.
- Self-references: `Flosum__Next_Step_Id_On_Pass__c` and `Flosum__Next_Step_Id_On_Fail__c`, both reference Pipeline Step.
- Child relationship: `Flosum__PipelineSteps__r`.
