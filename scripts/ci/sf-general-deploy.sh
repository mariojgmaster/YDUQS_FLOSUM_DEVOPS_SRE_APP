#!/usr/bin/env bash
# M4.1: reviewed Git baseline -> remote equality -> dry-run -> explicit Metadata API deploy.
set -euo pipefail
umask 077
abort() { echo "::error title=$1::$2"; exit 1; }
: "${OPERATION:?}" "${TARGET:?}" "${PACKAGE_ID:?}" "${REQUESTED_SHA:?}" "${BASELINE_SHA:?}"
[[ "$OPERATION" == plan || "$OPERATION" == deploy ]] || abort SDOA_OPERATION_DENIED 'Only plan/deploy supported.'
[[ "$GITHUB_EVENT_NAME" == workflow_dispatch && "$GITHUB_REF" == refs/heads/master ]] || abort SDOA_TRIGGER_DENIED 'Manual master dispatch required.'
[[ "$GITHUB_ACTOR" == "$GITHUB_REPOSITORY_OWNER" ]] || abort SDOA_ACTOR_DENIED 'Only the repository owner may initiate this pilot.'
[[ "$GITHUB_RUN_ATTEMPT" == 1 ]] || abort SDOA_RERUN_DENIED 'Never re-run a real deployment workflow.'
[[ "$REQUESTED_SHA" =~ ^[[:xdigit:]]{40}$ && "$BASELINE_SHA" =~ ^[[:xdigit:]]{40}$ ]] || abort SDOA_SHA_INVALID 'Provide two full Git commit SHAs.'
[[ "${REQUESTED_SHA,,}" == "${GITHUB_SHA,,}" && "$(git rev-parse HEAD)" == "$GITHUB_SHA" ]] || abort SDOA_SHA_MISMATCH 'The master revision changed.'
git cat-file -e "$BASELINE_SHA^{commit}" 2>/dev/null || abort SDOA_BASELINE_MISSING 'Unknown baseline commit.'
git merge-base --is-ancestor "$BASELINE_SHA" "$GITHUB_SHA" || abort SDOA_BASELINE_NOT_ANCESTOR 'Baseline must be an ancestor of current master.'
[[ -n "$SF_INSTANCE_URL" && "$SF_INSTANCE_URL" == "$EXPECTED_INSTANCE_URL" ]] || abort SDOA_TARGET_DENIED 'My Domain does not match the registered target.'
[[ -n "${SF_CLIENT_ID:-}" && -n "${SF_USERNAME:-}" && -n "${SF_JWT_KEY:-}" ]] || abort SDOA_SECRETS_MISSING 'Missing ECA/JWT credentials in existing GitHub Environment.'
if [[ "$OPERATION" == deploy ]]; then
  [[ "$CONFIRMATION" == "DEPLOY $TARGET $PACKAGE_ID" ]] || abort SDOA_NOT_AUTHORIZED 'Explicit exact target/package confirmation required.'
else
  [[ -z "$CONFIRMATION" ]] || abort SDOA_PLAN_ONLY 'Plan must not carry a deploy confirmation.'
fi

policy() { python3 scripts/ci/sf-deploy-policy.py "$@"; }
policy_out="$(mktemp "$RUNNER_TEMP/sdoa-policy.XXXXXXXX")"
trap 'rm -f "$policy_out"' EXIT
policy resolve --target "$TARGET" --package "$PACKAGE_ID" --output-file "$policy_out" > /dev/null || abort SDOA_REGISTRY_DENIED 'Unreviewed environment or manifest.'
[[ "$(sed -n 's/^github_environment=//p' "$policy_out" | tail -1)" == "$GITHUB_ENVIRONMENT_NAME" ]] || abort SDOA_GITHUB_ENV_DENIED 'GitHub Environment mismatch.'
MANIFEST="$(sed -n 's/^manifest=//p' "$policy_out" | tail -1)"
[[ -f "$MANIFEST" ]] || abort SDOA_MANIFEST_MISSING 'Manifest absent from the reviewed revision.'

TEMP="$(mktemp -d "$RUNNER_TEMP/sdoa-universal.XXXXXXXX")"
cleanup() { rm -rf -- "$TEMP"; rm -f "$policy_out"; }
trap cleanup EXIT
mkdir -p "$TEMP/base" "$TEMP/baseline-mdapi" "$TEMP/candidate-mdapi" "$TEMP/isolated/empty" "$TEMP/retrieved"
cat > "$TEMP/isolated/sfdx-project.json" <<'JSON'
{"packageDirectories":[{"path":"empty","default":true}],"name":"sdoa-m4","namespace":"","sourceApiVersion":"67.0"}
JSON
# A pinned Git commit is the ONLY baseline source; never compare to a floating branch.
git archive --format=tar "$BASELINE_SHA" | tar -xf - -C "$TEMP/base"
[[ -f "$TEMP/base/sfdx-project.json" ]] || abort SDOA_BASELINE_NO_SFDX 'Missing SFDX project in baseline.'
( cd "$TEMP/base"; sf project convert source --manifest "$GITHUB_WORKSPACE/$MANIFEST" --output-dir "$TEMP/baseline-mdapi" --json > "$TEMP/convert-base.json" 2> "$TEMP/convert-base.err" ) || abort SDOA_CONVERT_BASE 'Could not convert baseline.'
( cd "$GITHUB_WORKSPACE"; sf project convert source --manifest "$MANIFEST" --output-dir "$TEMP/candidate-mdapi" --json > "$TEMP/convert-candidate.json" 2> "$TEMP/convert-candidate.err" ) || abort SDOA_CONVERT_CANDIDATE 'Could not convert reviewed candidate.'
# Inspect allowlists even when source comparisons are with themselves.
policy compare --package "$PACKAGE_ID" --left "$TEMP/baseline-mdapi" --right "$TEMP/baseline-mdapi" --label candidate > "$TEMP/self-base" || abort SDOA_BASE_PACKAGE_UNSAFE 'Baseline has missing or extra metadata.'
policy compare --package "$PACKAGE_ID" --left "$TEMP/candidate-mdapi" --right "$TEMP/candidate-mdapi" --label candidate > "$TEMP/self-candidate" || abort SDOA_NEW_PACKAGE_UNSAFE 'Candidate has missing or extra metadata.'
diff_exit=0
policy compare --package "$PACKAGE_ID" --left "$TEMP/baseline-mdapi" --right "$TEMP/candidate-mdapi" --label candidate > "$TEMP/candidate-diff" || diff_exit=$?
[[ "$diff_exit" == 0 || "$diff_exit" == 4 ]] || abort SDOA_SOURCE_COMPARE_FAILED 'Unable to compare the two reviewed source versions.'
echo 'SDOA_INTENT_VERIFIED: manual dispatch, allowed target/package, current SHA and pinned baseline.'

printf '%s' "$SF_JWT_KEY" > "$TEMP/key.pem"
openssl pkey -in "$TEMP/key.pem" -noout -passin pass: >/dev/null 2>&1 || abort SDOA_JWT_KEY_INVALID 'Invalid unencrypted PEM private key.'
sf org login jwt --client-id "$SF_CLIENT_ID" --username "$SF_USERNAME" --jwt-key-file "$TEMP/key.pem" --instance-url "$SF_INSTANCE_URL" --alias sdoa-universal --json > "$TEMP/auth.json" 2> "$TEMP/auth.err" || abort SDOA_JWT_LOGIN_FAILED 'JWT login failed.'
jq -e '.status==0' "$TEMP/auth.json" >/dev/null 2>&1 || abort SDOA_JWT_UNCONFIRMED 'JWT login returned non-success.'

verify_remote() {
  local phase="$1" dest="$TEMP/mdapi-$1"
  mkdir -p "$dest"
  ( cd "$TEMP/isolated"; sf project retrieve start --manifest "$GITHUB_WORKSPACE/$MANIFEST" --target-metadata-dir "$dest" --target-org sdoa-universal --wait 40 --json > "$TEMP/retrieve-$phase.json" 2> "$TEMP/retrieve-$phase.err" ) || abort SDOA_RETRIEVE_FAILED 'Metadata API retrieve failed.'
  jq -e '.status==0' "$TEMP/retrieve-$phase.json" >/dev/null 2>&1 || abort SDOA_RETRIEVE_UNCONFIRMED 'Metadata retrieve returned non-success.'
  shopt -s nullglob
  local zips=("$dest"/*.zip)
  [[ "${#zips[@]}" == 1 ]] || abort SDOA_ZIP_MISSING 'Expected exactly one Metadata API ZIP.'
  if ! policy compare --package "$PACKAGE_ID" --left "$TEMP/baseline-mdapi" --right "${zips[0]}" --right-zip --label "$phase" > "$TEMP/compare-$phase"; then
    # Emit only fixed policy markers and approved manifest-member names.
    grep -E '^SDOA_(REMOTE|RECHECK)_(COMPARE|DIFFERING_MEMBERS|DIFFERING_PARTS|APEX_META_FACTS):' "$TEMP/compare-$phase" || true
    abort SDOA_REMOTE_DRIFT 'Org differs from the last-known-deployed package. Blocked.'
  fi
  echo "SDOA_${phase^^}_BASELINE_OK: remote metadata matches pinned Git baseline."
}
verify_remote remote
if [[ "$diff_exit" == 0 ]]; then
  echo 'SDOA_NO_CHANGE: candidate is identical to verified remote baseline; no deployment sent.'
  exit 0
fi

preview_exit=0
sf project deploy preview --manifest "$MANIFEST" --target-org sdoa-universal --json > "$TEMP/preview.json" 2> "$TEMP/preview.err" || preview_exit=$?
[[ "$preview_exit" == 0 ]] || abort SDOA_PREVIEW_FAILED 'Deploy preview failed, no write attempted.'
jq -e '.status==0 and (.result.toDeploy|type)=="array" and (.result.conflicts|type)=="array" and (.result.toDelete|type)=="array" and (.result.ignored|type)=="array"' "$TEMP/preview.json" >/dev/null 2>&1 || abort SDOA_PREVIEW_SCHEMA 'Unsupported Salesforce CLI preview JSON.'
read -r to_deploy conflicts to_delete ignored < <(jq -r '[(.result.toDeploy|length),(.result.conflicts|length),(.result.toDelete|length),(.result.ignored|length)]|@tsv' "$TEMP/preview.json")
echo "SDOA_PREVIEW: toDeploy=$to_deploy conflicts=$conflicts toDelete=$to_delete ignored=$ignored"
(( to_delete == 0 && ignored == 0 )) || abort SDOA_DELETION_DENIED 'Deletion or ignored components blocked.'
if [[ "$OPERATION" == plan ]]; then
  echo 'SDOA_PLAN_OK: candidate differs, org matches baseline, preview complete; no deployment was executed.'
  exit 0
fi

mapfile -t TESTS < <(python3 - "$PACKAGE_ID" <<'PY'
import json,sys
with open('config/salesforce-devops/catalog.json', encoding='utf-8') as f:
    data=json.load(f)
print('\n'.join(data['packages'][sys.argv[1]]['tests']))
PY
)
test_args=(--test-level RunSpecifiedTests)
for t in "${TESTS[@]}"; do test_args+=(--tests "$t"); done
# Use a fixed Metadata API payload instead of source-tracking deployment.
dry_exit=0
sf project deploy start --dry-run --metadata-dir "$TEMP/candidate-mdapi" "${test_args[@]}" --target-org sdoa-universal --wait 60 --json > "$TEMP/dry.json" 2> "$TEMP/dry.err" || dry_exit=$?
[[ "$dry_exit" == 0 ]] && jq -e '.status==0 and .result.success==true and (.result.done==true or .result.status=="Succeeded")' "$TEMP/dry.json" >/dev/null 2>&1 || abort SDOA_DRY_RUN_FAILED 'Dry-run or Apex tests failed; no write attempted.'
echo 'SDOA_DRY_RUN_PASSED: package validated, tests accepted.'
verify_remote recheck
[[ "$CONFIRMATION" == "DEPLOY $TARGET $PACKAGE_ID" && "${REQUESTED_SHA,,}" == "${GITHUB_SHA,,}" && "$GITHUB_RUN_ATTEMPT" == 1 ]] || abort SDOA_FINAL_GATE_FAILED 'Authorization changed after validation.'
echo 'SDOA_REAL_DEPLOY_STARTING: explicitly authorized deployment submitted.'
real_exit=0
sf project deploy start --metadata-dir "$TEMP/candidate-mdapi" "${test_args[@]}" --target-org sdoa-universal --wait 60 --json > "$TEMP/deploy.json" 2> "$TEMP/deploy.err" || real_exit=$?
[[ "$real_exit" == 0 ]] && jq -e '.status==0 and .result.success==true and (.result.done==true or .result.status=="Succeeded")' "$TEMP/deploy.json" >/dev/null 2>&1 || abort SDOA_REAL_DEPLOY_UNCONFIRMED 'Deployment failed or outcome uncertain. Inspect Salesforce Deployment Status before retrying.'
echo 'SDOA_REAL_DEPLOY_SUCCEEDED: Salesforce confirmed persistent deployment.'
