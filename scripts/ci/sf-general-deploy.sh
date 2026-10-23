#!/usr/bin/env bash
# M4.2 sandbox: reviewed Git package -> direct Salesforce dry-run -> optional explicit deploy.
# DRY-RUN IS NOT A REMOTE-DRIFT CHECK; reviewed files may overwrite org-side edits.
set -euo pipefail
umask 077
abort() { echo "::error title=$1::$2"; exit 1; }

: "${OPERATION:?}" "${TARGET:?}" "${PACKAGE_ID:?}"
[[ "$OPERATION" == plan || "$OPERATION" == deploy ]] || abort SDOA_OPERATION_DENIED 'Only plan/deploy supported.'
# Two audited entrypoints: manual M4.2 plan/deploy or owner-authored M5 Issue PLAN.
# M5 can NEVER deploy. The event payload is verified again in this privileged job.
if [[ "$GITHUB_EVENT_NAME" == issues ]]; then
  [[ "$GITHUB_REF" == refs/heads/master && "$OPERATION" == plan && -z "${CONFIRMATION:-}" ]] || abort SDOA_M5_PLAN_ONLY 'Issue ChatOps is restricted to plan on master.'
  python3 scripts/ci/sf-m5-chatops-intent.py --event "$GITHUB_EVENT_PATH" --owner "$GITHUB_REPOSITORY_OWNER" --repository "$GITHUB_REPOSITORY" --target "$TARGET" --package "$PACKAGE_ID" || abort SDOA_M5_INTENT_DENIED 'Issue intent could not be verified.'
else
  [[ "$GITHUB_EVENT_NAME" == workflow_dispatch && "$GITHUB_REF" == refs/heads/master ]] || abort SDOA_TRIGGER_DENIED 'Manual master dispatch required.'
fi
[[ "$GITHUB_ACTOR" == "$GITHUB_REPOSITORY_OWNER" ]] || abort SDOA_ACTOR_DENIED 'Only repository owner may initiate this pilot.'
[[ "$GITHUB_RUN_ATTEMPT" == 1 ]] || abort SDOA_RERUN_DENIED 'Never re-run a deployment workflow.'
[[ "$GITHUB_SHA" =~ ^[[:xdigit:]]{40}$ && "$(git rev-parse HEAD)" == "$GITHUB_SHA" ]] || abort SDOA_SHA_MISMATCH 'Selected master revision does not match checked-out commit.'
[[ -n "${SF_INSTANCE_URL:-}" && "$SF_INSTANCE_URL" == "$EXPECTED_INSTANCE_URL" ]] || abort SDOA_TARGET_DENIED 'My Domain does not match the registered sandbox.'
[[ -n "${SF_CLIENT_ID:-}" && -n "${SF_USERNAME:-}" && -n "${SF_JWT_KEY:-}" ]] || abort SDOA_SECRETS_MISSING 'Missing ECA/JWT credentials in existing GitHub Environment.'
if [[ "$OPERATION" == deploy ]]; then
  [[ "${CONFIRMATION:-}" == "DEPLOY $TARGET $PACKAGE_ID" ]] || abort SDOA_NOT_AUTHORIZED 'Exact target/package confirmation required for a real deploy.'
else
  [[ -z "${CONFIRMATION:-}" ]] || abort SDOA_PLAN_ONLY 'Plan must not carry a deployment confirmation.'
fi

policy() { python3 scripts/ci/sf-deploy-policy.py "$@"; }
TEMP="$(mktemp -d "$RUNNER_TEMP/sdoa-m4-2.XXXXXXXX")"
cleanup() { rm -rf -- "$TEMP"; }
trap cleanup EXIT
policy_out="$TEMP/policy"
policy resolve --target "$TARGET" --package "$PACKAGE_ID" --output-file "$policy_out" > /dev/null || abort SDOA_REGISTRY_DENIED 'Unreviewed environment or metadata manifest.'
[[ "$(sed -n 's/^github_environment=//p' "$policy_out" | tail -1)" == "$GITHUB_ENVIRONMENT_NAME" ]] || abort SDOA_GITHUB_ENV_DENIED 'GitHub Environment mismatch.'
MANIFEST="$(sed -n 's/^manifest=//p' "$policy_out" | tail -1)"
[[ -f "$MANIFEST" && ! -L "$MANIFEST" ]] || abort SDOA_MANIFEST_MISSING 'Reviewed manifest missing or symlink.'

# Convert exactly the allowlisted Git manifest to a fixed Metadata API directory.
# Do not retrieve/compare the org, do not use deploy preview or source-tracking bypass flags.
mkdir -p "$TEMP/candidate-mdapi"
( sf project convert source --manifest "$MANIFEST" --output-dir "$TEMP/candidate-mdapi" --json > "$TEMP/convert.json" 2> "$TEMP/convert.err" ) || abort SDOA_CONVERT_CANDIDATE 'Cannot convert reviewed metadata.'
jq -e '.status==0' "$TEMP/convert.json" >/dev/null 2>&1 || abort SDOA_CONVERT_UNCONFIRMED 'Converted metadata result not confirmed.'
# The policy compare verifies that the converted payload contains no unapproved files
# and that every reviewed manifest member is present.
policy compare --package "$PACKAGE_ID" --left "$TEMP/candidate-mdapi" --right "$TEMP/candidate-mdapi" --label candidate > "$TEMP/package-check" || abort SDOA_CANDIDATE_UNSAFE 'Converted payload violates strict metadata allowlist.'
echo "SDOA_M42_INTENT_VERIFIED: master SHA pinned, actor authorized, registered target/package verified."
echo "SDOA_M42_SHA: $GITHUB_SHA"
echo "SDOA_M42_PACKAGE_VERIFIED: only reviewed metadata members; no destructive changes."

printf '%s' "$SF_JWT_KEY" > "$TEMP/key.pem"
openssl pkey -in "$TEMP/key.pem" -noout -passin pass: >/dev/null 2>&1 || abort SDOA_JWT_KEY_INVALID 'Invalid unencrypted PEM private key.'
sf org login jwt --client-id "$SF_CLIENT_ID" --username "$SF_USERNAME" --jwt-key-file "$TEMP/key.pem" --instance-url "$SF_INSTANCE_URL" --alias sdoa-universal --json > "$TEMP/auth.json" 2> "$TEMP/auth.err" || abort SDOA_JWT_LOGIN_FAILED 'JWT login failed.'
jq -e '.status==0' "$TEMP/auth.json" >/dev/null 2>&1 || abort SDOA_JWT_UNCONFIRMED 'Salesforce JWT authorization unconfirmed.'
echo "SDOA_M42_AUTH_OK: JWT login completed."

# Apex tests remain mandatory for both plan and deploy, including LWC-only packages.
mapfile -t TESTS < <(python3 - "$PACKAGE_ID" <<'PY'
import json, sys
with open("config/salesforce-devops/catalog.json", encoding="utf-8") as f:
    catalog = json.load(f)
print("\n".join(catalog["packages"][sys.argv[1]]["tests"]))
PY
)
(( ${#TESTS[@]} > 0 )) || abort SDOA_TEST_POLICY_DENIED 'Reviewed package has no specified Apex test classes.'
test_args=(--test-level RunSpecifiedTests)
for class_name in "${TESTS[@]}"; do test_args+=(--tests "$class_name"); done

# Dry-run is mandatory even for plan. It is a deployment validation, NOT
# proof that remote edits or managed-package version pins will be preserved.
echo "SDOA_M42_DRY_RUN_STARTING: Salesforce validation with specified Apex tests."
dry_exit=0
sf project deploy start --dry-run --metadata-dir "$TEMP/candidate-mdapi" "${test_args[@]}" --target-org sdoa-universal --wait 60 --json > "$TEMP/dry.json" 2> "$TEMP/dry.err" || dry_exit=$?
if [[ "$dry_exit" != 0 ]] || ! jq -e '.status==0 and .result.success==true and (.result.done==true or .result.status=="Succeeded") and ((.result.numberComponentErrors // 0)==0) and ((.result.numberTestErrors // 0)==0)' "$TEMP/dry.json" >/dev/null 2>&1; then
  python3 scripts/ci/sf-deploy-safe-diagnostic.py --file "$TEMP/dry.json" --exit "$dry_exit" --phase DRY_RUN
  abort SDOA_M42_DRY_RUN_FAILED 'Salesforce rejected dry-run, Apex tests failed, or response was not confirmed. See sanitized diagnostic and Salesforce Deployment Status; no real deployment attempted.'
fi
echo 'SDOA_M42_DRY_RUN_PASSED: Salesforce validation succeeded; specified Apex tests passed.'
if [[ "$OPERATION" == plan ]]; then
  echo 'SDOA_M42_PLAN_OK: Salesforce dry-run validated this exact package. No real deployment was submitted.'
  exit 0
fi

# Explicit write; same Git commit, package and local MDAPI payload as dry-run.
[[ "${CONFIRMATION:-}" == "DEPLOY $TARGET $PACKAGE_ID" && "$(git rev-parse HEAD)" == "$GITHUB_SHA" && "$GITHUB_RUN_ATTEMPT" == 1 ]] || abort SDOA_FINAL_GATE_DENIED 'Explicit deployment authorization changed.'
echo '::warning title=M4.2 no drift gate::This authorized deployment may overwrite edits made directly in the sandbox to the same metadata members.'
echo "SDOA_M42_REAL_DEPLOY_STARTING: authorized write to $TARGET using SHA $GITHUB_SHA."
real_exit=0
sf project deploy start --metadata-dir "$TEMP/candidate-mdapi" "${test_args[@]}" --target-org sdoa-universal --wait 60 --json > "$TEMP/deploy.json" 2> "$TEMP/deploy.err" || real_exit=$?
if [[ "$real_exit" != 0 ]] || ! jq -e '.status==0 and .result.success==true and (.result.done==true or .result.status=="Succeeded") and ((.result.numberComponentErrors // 0)==0) and ((.result.numberTestErrors // 0)==0)' "$TEMP/deploy.json" >/dev/null 2>&1; then
  python3 scripts/ci/sf-deploy-safe-diagnostic.py --file "$TEMP/deploy.json" --exit "$real_exit" --phase REAL_DEPLOY
  abort SDOA_M42_DEPLOY_UNCONFIRMED 'Real deploy failed or outcome uncertain; inspect Salesforce Deployment Status before retrying. Do not rerun this job.'
fi
echo 'SDOA_REAL_DEPLOY_SUCCEEDED: Salesforce confirmed persistent deployment.'
