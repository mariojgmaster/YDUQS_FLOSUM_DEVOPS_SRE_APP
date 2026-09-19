# Quickstart Validation: Clone Pipeline

## Prerequisites

- Salesforce CLI authenticated to the Flosum development sandbox.
- User has access to both managed objects and to the new Apex class.
- A source Pipeline exists with at least three Steps and pass/fail links between them.

## Automated Validation

```powershell
npm install
npm run test:unit -- --runInBand
sf project deploy validate --source-dir force-app/main/default/classes --source-dir force-app/main/default/lwc/clonePipelineAction --test-level RunSpecifiedTests --tests ClonePipelineControllerTest --target-org devsrefeat --wait 30
```

Expected: Jest and Apex tests pass; deployment validation reports success.

### Validation result (2026-09-18)

- ESLint: passed with no reported errors.
- Jest: 5 tests passed, 0 failed.
- Salesforce validation: succeeded in `devsrefeat`, job `0AfV900000DzXCTKA3`.
- Apex: 5 tests passed, 0 failed; 203 of 217 executable lines covered (approximately 93.5%).
- Validated metadata: 2 Apex classes, 1 Lightning Web Component bundle, and 1 object-specific Quick Action.
- Quick Deploy completed successfully in `devsrefeat` on 2026-09-18, deployment job `0AfV900000DzY6vKAF` (`CheckOnly = false`, 4 components, 0 errors).

## Manual End-to-End Validation

1. Deploy the metadata and configure the `clonePipelineAction` record action on the Pipeline page layout.
2. Open the prepared source Pipeline and choose **Clonar Pipeline**.
3. Confirm the suggested name and displayed Step count.
4. Change the name and submit once; verify controls remain disabled during processing.
5. Verify navigation reaches one new Pipeline with the entered name.
6. Compare Step counts, values, order, and pass/fail links with the source.
7. Verify every cloned pass/fail link targets a Step under the cloned Pipeline.
8. Repeat with a Pipeline that has no Steps.
9. Trigger a validation failure and verify that no partial Pipeline or Step remains.

## Post-Deployment Configuration

- Add the action to the Pipeline Lightning record page/page layout.
- Grant Apex class access through the intended Permission Set.
- Do not broaden managed object or field permissions solely for this feature.
- The installed Flosum Pipeline layouts are managed-package metadata and could not be retrieved for a safe source-controlled edit. Adding `Clonar Pipeline` to the assigned layout remains an explicit post-deployment administration step.
