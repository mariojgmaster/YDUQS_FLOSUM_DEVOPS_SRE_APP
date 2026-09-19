# Tasks: Clone Pipeline

**Input**: Design documents from `specs/001-clone-pipeline/`
**Tests**: Apex and Jest tests are required by FR-014 and the project constitution.

## Phase 1: Setup

- [x] T001 Verify managed Pipeline and Pipeline Step object/field contracts against org `devsrefeat` and record findings in `specs/001-clone-pipeline/research.md`
- [x] T002 Update the managed Spec Kit context reference in `AGENTS.md`

## Phase 2: Foundational

- [x] T003 Define preview, clone result, security, atomicity, and two-pass remapping contracts in `specs/001-clone-pipeline/contracts/clone-pipeline.md`
- [x] T004 Define entities, relationships, exclusions, and transaction states in `specs/001-clone-pipeline/data-model.md`

## Phase 3: User Story 1 - Clone a complete pipeline (Priority: P1) MVP

**Goal**: Atomically clone a Pipeline and all Steps with correct internal references.

**Independent Test**: Clone a source with linked Steps and verify parent, child count, copied values, and source-to-clone reference mapping.

- [x] T005 [P] [US1] Write Apex success, no-Step, reference-remapping, input/security enforcement, and rollback tests in `force-app/main/default/classes/ClonePipelineControllerTest.cls`
- [x] T006 [US1] Implement secure describe-driven parent/child cloning and rollback in `force-app/main/default/classes/ClonePipelineController.cls`
- [x] T007 [P] [US1] Add Apex metadata in `force-app/main/default/classes/ClonePipelineController.cls-meta.xml` and `force-app/main/default/classes/ClonePipelineControllerTest.cls-meta.xml`

## Phase 4: User Story 2 - Review and control the clone action (Priority: P2)

**Goal**: Present a confirmation modal with editable suggested name and Step count, including loading and duplicate-submit safeguards.

**Independent Test**: Load a preview, validate blank/oversized names, cancel without mutation, and submit once while controls are disabled.

- [x] T008 [P] [US2] Write LWC loading, validation, cancel, and duplicate-submit tests in `force-app/main/default/lwc/clonePipelineAction/__tests__/clonePipelineAction.test.js`
- [x] T009 [US2] Implement the confirmation modal in `force-app/main/default/lwc/clonePipelineAction/clonePipelineAction.html`
- [x] T010 [US2] Implement preview, validation, submit state, and cancellation logic in `force-app/main/default/lwc/clonePipelineAction/clonePipelineAction.js`
- [x] T011 [US2] Expose and define the desktop Screen Action in `force-app/main/default/lwc/clonePipelineAction/clonePipelineAction.js-meta.xml` and `force-app/main/default/quickActions/Flosum__Pipeline__c.Clonar_Pipeline.quickAction-meta.xml`

## Phase 5: User Story 3 - Receive a clear completion result (Priority: P3)

**Goal**: Provide safe feedback and navigate to the cloned Pipeline after success.

**Independent Test**: Simulate success and error responses and assert toast, modal, recovery, and navigation behavior.

- [x] T012 [P] [US3] Extend LWC tests for success navigation and safe error feedback in `force-app/main/default/lwc/clonePipelineAction/__tests__/clonePipelineAction.test.js`
- [x] T013 [US3] Add toast, close, navigation, and error normalization behavior in `force-app/main/default/lwc/clonePipelineAction/clonePipelineAction.js`

## Phase 6: Polish and Validation

- [x] T014 Run formatting and static project checks for files under `force-app/main/default/classes/ClonePipelineController*` and `force-app/main/default/lwc/clonePipelineAction/`
- [x] T015 Run Jest tests and record the result in `specs/001-clone-pipeline/quickstart.md`
- [x] T016 Run Salesforce deployment validation with `ClonePipelineControllerTest` against `devsrefeat` and record the result in `specs/001-clone-pipeline/quickstart.md`
- [x] T017 Review implementation against FR-001 through FR-014 and mark all completed tasks in `specs/001-clone-pipeline/tasks.md`

## Dependencies & Execution Order

- Phase 1 precedes Phase 2; both are already bounded documentation/setup work.
- US1 provides the server contract required by US2 and US3.
- US2 depends on the preview/clone methods from US1.
- US3 extends US2 feedback behavior.
- Validation depends on all desired stories.

## Parallel Opportunities

- T005 and T007 affect separate files and can be prepared in parallel before T006 is finalized.
- T008 can be prepared against the documented contract while T006 is implemented.
- T012 can extend the Jest suite once the base test harness from T008 exists.

## Implementation Strategy

The MVP is US1: a tested, atomic application service. US2 adds deliberate user confirmation, and US3 completes operational feedback. Tests are authored before their corresponding implementation and run again as an integrated validation gate.
