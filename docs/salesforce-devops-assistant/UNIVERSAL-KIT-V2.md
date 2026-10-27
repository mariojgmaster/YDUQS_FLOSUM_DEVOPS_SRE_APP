# Salesforce DevOps Assistant — Universal Kit v2 (incremental)

## Scope and compatibility

This opt-in v2 lane extends the existing, approved **Retrieve / Compare / Validate
(PLAN) / Deploy** GitHub Issue ChatOps protocol. It does **not** replace the
homologated kit v1 or change its published template manifest and checksums.
An explicit package in config/salesforce-devops/catalog.json switches to v2
using policy_version: 2 and reviewed: true. Every other package uses v1.

- Existing sandbox targets, immutable Git SHA, repository-owner Issue, one Issue
  per deploy, first attempt only, and exact confirmation are unchanged.
- Production remains blocked. A deploy still requires an explicit instruction
  for the exact sandbox/package followed by a **new** SDOA DEPLOY Issue.
- The requested manifest is reviewed in Git. Only named metadata members are
  accepted; wildcards and destructive-change bundles are rejected.
- Additional Salesforce metadata types are admitted by the declarative catalog
  and native SF CLI source-to-Metadata-API conversion, not a two-type allowlist.
  Compatibility with a specific metadata type is proven only through its real
  validation, not inferred from policy acceptance.

## Test selection

For a reviewed package, test_level=auto chooses:
- RunSpecifiedTests when explicit Apex test class names are listed;
- RunLocalTests when Apex/Flow/object/field/validation/workflow metadata is
  changed and no specified tests were reviewed;
- NoTestRun for low-risk sandbox metadata without specified Apex tests
  (for example CustomTab).

Explicit RunSpecifiedTests requires test names. Apex-impacting changes cannot
force NoTestRun. The Salesforce response must confirm success in both PLAN
and DEPLOY; a green GitHub Action alone is insufficient. For LWC changes,
repository-local Jest checks remain separate from Apex test decisions; v1
clone-pipeline-lwc Jest behavior is retained.

Sensitive types (profiles, permission sets, connected apps, credentials,
sharing etc.) require an additional sensitive_change_reviewed=true flag
in the reviewed catalog. This is not a bypass of required PR review or org
permissions; changes must still be scoped and verified independently.

## Three v2 packages for safe, representative validation

- branch-monitor-tab-v2: CustomTab:branchMonitor; NoTestRun
- environment-reason-field-v2: CustomField:DevSre_EnvironmentMapping__c.Reason__c;
  RunSpecifiedTests(DevSreEnvironmentTest)
- environment-trigger-v2: ApexTrigger:DevSreEnvironmentMapping;
  RunLocalTests when no explicit test classes are specified

These packages reference existing source-controlled metadata. They do not
indicate any Salesforce deployment or that those members have been validated
against the org.

## Operation examples

Use the existing Issue title/body contract, changing only package_id to a
reviewed v2 package:

SDOA PLAN DevSreFeat branch-monitor-tab-v2

SDOA-CHATOPS/1
operation=plan
target=DevSreFeat
package_id=branch-monitor-tab-v2

Retrieve and Compare use SDOA-CHATOPS/3; Deploy uses
SDOA-CHATOPS/2 plus an immutable 40-hex master SHA and exact
confirmation=DEPLOY DevSreFeat <package_id>. Do not run a real DEPLOY
during kit migration or smoke testing.

## Acceptance gates

1. Review PR diff and pass all tests/test_sf_*.py plus branch protection.
2. Merge after normal approval; this alone executes **no** Salesforce operation.
3. Start only a Retrieve Issue for branch-monitor-tab-v2 and inspect exact
   run, sanitized artifact and actual retrieved members.
4. Start Compare; check drift against Git (differences are not an execution
   failure).
5. Start PLAN (dry-run) for the tab package; confirm no persistent write.
6. Validate field and trigger packages only after dependency review; confirm
   the resolved Apex level in runner logs and Salesforce result.
7. Propose real sandbox deployment only after review of actual package diff,
   drift and explicit user authorization; never treat this PR as that consent.

## Known limitations and migration risks

- v2 Compare reports an aggregate count of differing files; it does not yet
  attribute every changed Metadata API file to a logical member for every
  Salesforce metadata type. This is deliberate rather than inventing names.
- Metadata API conversion and retrieve formats may differ for some types.
  A manifest/payload mismatch blocks until investigated, not bypassed.
- Expanded type support does not guarantee every metadata family, namespace,
  dependency, binary content or package version will deploy successfully.
- Public repositories receive sanitized reports, **not** raw XML, Apex or
  JSON; private raw artifacts remain opt-in with short retention.
- The plugin uses GitHub Actions' SF CLI runner and the available GitHub
  connector, not an unrestricted local terminal. It cannot override a missing
  permission, approval or execution tool.
- The legacy v1 template installer stays pinned to v1 for existing customers.
  Distribution of v2 templates is a separate, reviewed template release.
