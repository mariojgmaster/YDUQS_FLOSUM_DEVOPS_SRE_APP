# Implementation Plan: Clone Pipeline

**Branch**: current working branch | **Date**: 2026-09-18 | **Spec**: [spec.md](spec.md)

## Summary

Add a Lightning record Screen Action that previews and confirms cloning of `Flosum__Pipeline__c`. A focused Apex application service performs user-mode reads and writes, dynamically copies only readable/createable fields, inserts every `Flosum__PipelineStep__c`, remaps pass/fail self-references in a second pass, and rolls the transaction back on any failure.

## Technical Context

**Language/Version**: Apex and Lightning Web Components, Salesforce API 67.0

**Primary Dependencies**: Salesforce Lightning Experience, Lightning Data Service navigation/toasts, managed Flosum objects

**Storage**: Existing `Flosum__Pipeline__c` and `Flosum__PipelineStep__c` records

**Testing**: Apex tests and Jest tests with `@salesforce/sfdx-lwc-jest`

**Target Platform**: Salesforce Lightning Experience desktop

**Project Type**: Salesforce DX application

**Performance Goals**: Complete a clone of up to 100 Steps within 10 seconds in normal sandbox conditions

**Constraints**: One synchronous transaction; no SOQL/DML in loops; user-mode CRUD/FLS; record sharing; no managed-package source modification; maximum Pipeline name length 80

**Scale/Scope**: One Pipeline per action invocation and up to 100 associated Steps; execution history and result objects excluded

## Constitution Check

- **Well-Architected / simplicity**: PASS — native LWC and Apex only, no external dependency.
- **Security / least privilege**: PASS — `with sharing`, explicit object checks, user-mode SOQL/DML, dynamic readable/createable field intersection.
- **Separation of responsibilities**: PASS — UI handles confirmation; controller/service owns application transaction.
- **Bulkification and governor limits**: PASS — fixed query/DML count and collection operations; no query or DML in loops.
- **Transaction integrity**: PASS — savepoint and full rollback; partial clones are prohibited.
- **Testability**: PASS — Apex behavior and LWC state/interaction receive automated tests.
- **Configuration before hardcode**: PASS WITH RATIONALE — managed object/field API names are stable compile-time integration contracts; the set of copied fields is describe-driven.
- **Deployability**: PASS — source metadata plus documented page-layout post-deployment step.
- **Constitution status**: The user's explicit instruction to document and implement this feature is treated as feature authorization; it does not amend the constitution itself.

Post-design recheck: PASS. No constitution exception or ADR is required because this is a bounded, synchronous, Salesforce-native record operation.

## Architecture

1. `clonePipelineAction` receives `recordId`, loads a preview, and presents the suggested name and Step count.
2. `ClonePipelineController.getPreview` validates read access and returns only the UI data required.
3. `ClonePipelineController.clonePipeline` validates input and delegates the atomic operation.
4. The service queries readable/createable Pipeline fields, creates the parent clone, queries all child Steps, and inserts child clones with self-references cleared.
5. A map from source Step ID to cloned Step ID is used to update pass/fail references in a second DML operation.
6. Any exception rolls back all records. The controller exposes a safe error message.
7. On success, the LWC closes the action, shows a toast, and navigates to the cloned Pipeline.

## Project Structure

### Documentation

```text
specs/001-clone-pipeline/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/clone-pipeline.md
├── checklists/
└── tasks.md
```

### Source Code

```text
force-app/main/default/
├── classes/
│   ├── ClonePipelineController.cls
│   ├── ClonePipelineController.cls-meta.xml
│   ├── ClonePipelineControllerTest.cls
│   └── ClonePipelineControllerTest.cls-meta.xml
└── lwc/clonePipelineAction/
    ├── clonePipelineAction.html
    ├── clonePipelineAction.js
    ├── clonePipelineAction.js-meta.xml
    └── __tests__/clonePipelineAction.test.js
└── quickActions/
    └── Flosum__Pipeline__c.Clonar_Pipeline.quickAction-meta.xml
```

**Structure Decision**: Follow the existing Salesforce DX package structure. One cohesive Apex class is sufficient for this bounded use case; adding speculative repository/domain layers would violate the simplicity principle.

## Deployment Notes

- Deploy the Apex and LWC metadata.
- Create an object-specific Lightning Web Component action on `Flosum__Pipeline__c` using `clonePipelineAction`.
- Add the action to the Pipeline page layout's Salesforce Mobile and Lightning Experience Actions section (desktop only despite the section name).
- Grant Apex class access to the intended Permission Set personas; existing object/field permissions remain authoritative.
