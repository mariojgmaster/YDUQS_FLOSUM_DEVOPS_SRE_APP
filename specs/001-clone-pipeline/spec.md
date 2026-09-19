# Feature Specification: Clone Pipeline

**Feature Branch**: `001-clone-pipeline`
**Created**: 2026-09-18
**Status**: Approved for implementation
**Input**: Add an action to a Pipeline record that clones the Pipeline and all associated Pipeline Steps.

## User Scenarios & Testing

### User Story 1 - Clone a complete pipeline (Priority: P1)

As an authorized DevOps, SRE, or COE user, I want to clone an existing Pipeline together with its Steps so that I can create a new configuration without rebuilding its workflow manually.

**Why this priority**: This is the core business value and must be delivered atomically to avoid unusable pipeline configurations.

**Independent Test**: Select a Pipeline with multiple linked Steps, provide a new name, confirm cloning, and compare the clone with the source.

**Acceptance Scenarios**:

1. **Given** an accessible Pipeline with associated Steps, **When** an authorized user supplies a valid new name and confirms, **Then** one new Pipeline and the same number of Steps are created.
2. **Given** Steps that reference other Steps on pass or failure, **When** cloning completes, **Then** every internal reference points to the corresponding cloned Step and never to a source Step.
3. **Given** any failure while creating the Pipeline or its Steps, **When** the operation ends, **Then** no part of the clone remains persisted and the user receives a safe error message.

---

### User Story 2 - Review and control the clone action (Priority: P2)

As an authorized user, I want to review the suggested name and Step count before cloning so that I can avoid accidental or ambiguously named copies.

**Why this priority**: Confirmation reduces operator error without changing the core clone semantics.

**Independent Test**: Open the action, edit the suggested name, cancel once, then reopen and confirm.

**Acceptance Scenarios**:

1. **Given** a Pipeline record, **When** the action opens, **Then** it shows a suggested copy name and the number of Steps to be cloned.
2. **Given** the confirmation screen, **When** the user cancels, **Then** no records are created.
3. **Given** a blank or whitespace-only name, **When** the user attempts to confirm, **Then** cloning is not started and a validation message is shown.

---

### User Story 3 - Receive a clear completion result (Priority: P3)

As an authorized user, I want clear success or failure feedback so that I know whether the clone is ready to use.

**Why this priority**: Operational feedback completes the workflow and makes failures actionable.

**Independent Test**: Complete one successful clone and trigger one controlled validation failure.

**Acceptance Scenarios**:

1. **Given** a successful clone, **When** processing finishes, **Then** the user sees a success notification and is taken to the cloned Pipeline.
2. **Given** a validation, authorization, or persistence failure, **When** processing finishes, **Then** the user sees a concise message without stack traces or sensitive details and can retry after correction.

### Edge Cases

- The source Pipeline has no Steps: create the Pipeline clone with zero Steps.
- The source record no longer exists or is inaccessible: create nothing and report that the source is unavailable.
- The requested name exceeds the target field length: block submission before data mutation.
- A Step has a pass/fail reference outside the source Pipeline: clear that reference in the clone to prevent cross-pipeline coupling.
- A Step contains an optional null field: preserve the null value.
- Automation or validation rejects any inserted record: roll back the entire operation.
- Repeated clicks while processing: accept only one request from the open action.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST expose a clone action on an individual Pipeline record to authorized users.
- **FR-002**: The system MUST suggest a new Pipeline name derived from the source name and allow the user to edit it before confirmation.
- **FR-003**: The system MUST display the number of associated Steps before confirmation.
- **FR-004**: The system MUST require a nonblank name within the Pipeline name length limit.
- **FR-005**: The system MUST copy all user-configurable values of the source Pipeline except its identity and audit values.
- **FR-006**: The system MUST copy all associated Pipeline Steps and preserve their configurable values and ordering.
- **FR-007**: The system MUST associate every cloned Step with the cloned Pipeline.
- **FR-008**: The system MUST remap pass/fail Step references to cloned Steps; references outside the source Pipeline MUST NOT be retained.
- **FR-009**: The clone operation MUST be all-or-nothing.
- **FR-010**: The system MUST enforce current record access, object creation permission, and field-level read/create permissions.
- **FR-011**: The system MUST prevent duplicate submissions while a request is processing.
- **FR-012**: On success, the system MUST notify the user and open the cloned Pipeline record.
- **FR-013**: On failure, the system MUST present a safe, actionable message without sensitive technical details.
- **FR-014**: The solution MUST include automated tests for the success path, no-Step path, relationship remapping, validation failure, rollback behavior, and authorization-relevant enforcement.

### Key Entities

- **Pipeline**: The parent configuration being copied; its new identity and user-provided name distinguish the clone.
- **Pipeline Step**: An ordered child configuration associated with one Pipeline; it may reference another Step to determine the next action after pass or failure.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An authorized user can clone a Pipeline of up to 100 Steps in one interaction and receive a result within 10 seconds under normal sandbox conditions.
- **SC-002**: For every successful clone, the cloned Step count equals the source Step count and 100% of internal Step references resolve only to cloned Steps.
- **SC-003**: For every failed clone attempt, zero records from that attempt remain persisted.
- **SC-004**: All defined acceptance scenarios are covered by automated tests and pass in deployment validation.
- **SC-005**: A user can complete the confirmation flow using keyboard navigation and standard assistive labels.

## Assumptions

- Version 1 always clones all associated Steps; selectively cloning Steps is out of scope.
- Runtime execution records, Step results, logs, and deployment history are not cloned.
- The feature targets Lightning Experience desktop because record-page component actions are not supported in the standard Salesforce mobile app.
- Existing Flosum automation and validation rules remain authoritative and can reject invalid cloned configurations.
- The source and cloned records use the existing Flosum managed-package objects; no new domain object is introduced.
