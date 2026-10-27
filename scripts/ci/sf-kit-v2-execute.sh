#!/usr/bin/env bash
# SDOA universal v2 executor: one owner Issue, immutable SHA, no unapproved writes.
set -euo pipefail
umask 077
abort() { echo "::error title=$1::$2"; exit 1; }
: "${OPERATION:?}" "${TARGET:?}" "${PACKAGE_ID:?}" "${RUNNER_TEMP:?}"
[[ "$OPERATION" == retrieve || "$OPERATION" == compare || "$OPERATION" == plan || "$OPERATION" == deploy ]] || abort SDOA_V2_OPERATION_DENIED 'Unapproved operation.'
[[ "$GITHUB_EVENT_NAME" == issues && "$GITHUB_REF" == refs/heads/master && "$GITHUB_ACTOR" == "$GITHUB_REPOSITORY_OWNER" && "$GITHUB_RUN_ATTEMPT" == 1 ]] || abort SDOA_V2_TRIGGER_DENIED 'Owner Issue opened on master and first run required.'
[[ "$GITHUB_SHA" =~ ^[0-9a-f]{40}$ && "$(git rev-parse HEAD)" == "$GITHUB_SHA" ]] || abort SDOA_V2_SHA_DENIED 'Immutable master SHA mismatch.'
python3 scripts/ci/sf-m5-chatops-intent.py --event "$GITHUB_EVENT_PATH" --owner "$GITHUB_REPOSITORY_OWNER" --repository "$GITHUB_REPOSITORY" --operation "$OPERATION" --target "$TARGET" --package "$PACKAGE_ID" --commit-sha "$GITHUB_SHA" || abort SDOA_V2_INTENT_DENIED 'Invalid Issue intent.'
if [[ "$OPERATION" == deploy ]]; then
  [[ "${CONFIRMATION:-}" == "DEPLOY $TARGET $PACKAGE_ID" ]] || abort SDOA_V2_CONFIRMATION_DENIED 'Deploy confirmation missing.'
else
  [[ -z "${CONFIRMATION:-}" ]] || abort SDOA_V2_READ_ONLY 'Unexpected deploy confirmation.'
fi
[[ -n "${SF_CLIENT_ID:-}" && -n "${SF_USERNAME:-}" && -n "${SF_JWT_KEY:-}" && -n "${SF_INSTANCE_URL:-}" && "$SF_INSTANCE_URL" == "${EXPECTED_INSTANCE_URL:-}" ]] || abort SDOA_V2_AUTH_GATE 'Missing credentials or sandbox URL mismatch.'
WORK="$(mktemp -d "$RUNNER_TEMP/sdoa-v2.XXXXXXXX")"
cleanup() { rm -rf -- "$WORK"; }
trap cleanup EXIT
python3 scripts/ci/sf-kit-v2-policy.py resolve --target "$TARGET" --package "$PACKAGE_ID" --output-file "$WORK/resolved" > /dev/null || abort SDOA_V2_SCOPE_DENIED 'Unregistered target or package.'
[[ "$(sed -n 's/^policy_version=//p' "$WORK/resolved" | tail -1)" == 2 ]] || abort SDOA_V2_VERSION_DENIED 'Wrong executor.'
[[ "$(sed -n 's/^github_environment=//p' "$WORK/resolved" | tail -1)" == "$GITHUB_ENVIRONMENT_NAME" ]] || abort SDOA_V2_ENV_DENIED 'Wrong GitHub Environment.'
MANIFEST="$(sed -n 's/^manifest=//p' "$WORK/resolved" | tail -1)"
[[ -f "$MANIFEST" && ! -L "$MANIFEST" ]] || abort SDOA_V2_MANIFEST_DENIED 'Manifest unavailable.'
printf '%s' "$SF_JWT_KEY" > "$WORK/key.pem"
openssl pkey -in "$WORK/key.pem" -noout -passin pass: >/dev/null 2>&1 || abort SDOA_V2_JWT_DENIED 'Invalid JWT key.'
sf org login jwt --client-id "$SF_CLIENT_ID" --username "$SF_USERNAME" --jwt-key-file "$WORK/key.pem" --instance-url "$SF_INSTANCE_URL" --alias sdoa-v2 --json > "$WORK/auth.json" 2> "$WORK/auth.err" || abort SDOA_V2_AUTH_FAILED 'Salesforce login failed.'
jq -e '.status==0' "$WORK/auth.json" >/dev/null 2>&1 || abort SDOA_V2_AUTH_UNCONFIRMED 'Auth response unavailable.'
echo "SDOA_V2_AUTH_OK: sandbox verified."
private_export() {
  if [[ "${GITHUB_EVENT_REPOSITORY_PRIVATE:-false}" == true && "${SDOA_EXPORT_RAW:-false}" == true ]]; then
    mkdir -p "$RUNNER_TEMP/sdoa-private-raw"
    cp -- "$1" "$RUNNER_TEMP/sdoa-private-raw/$2"
  fi
}
safe_report() {
  python3 scripts/ci/sf-deploy-safe-diagnostic.py --file "$1" --exit "$2" --phase "$3" --report "$RUNNER_TEMP/sdoa-safe-report.json" --package "$PACKAGE_ID" || true
}
if [[ "$OPERATION" == retrieve || "$OPERATION" == compare ]]; then
  mkdir -p "$WORK/remote"
  sf project retrieve start --manifest "$MANIFEST" --target-org sdoa-v2 --target-metadata-dir "$WORK/remote" --zip-file-name package.zip --wait 60 --json > "$WORK/retrieve.json" 2> "$WORK/retrieve.err" || abort SDOA_V2_RETRIEVE_FAILED 'Retrieve failed; private details withheld.'
  jq -e '.status==0' "$WORK/retrieve.json" >/dev/null || abort SDOA_V2_RETRIEVE_UNCONFIRMED 'Retrieve result not confirmed.'
  [[ -f "$WORK/remote/package.zip" ]] || abort SDOA_V2_ZIP_MISSING 'No remote metadata ZIP.'
  args=()
  if [[ "$OPERATION" == compare ]]; then
    mkdir -p "$WORK/candidate"
    sf project convert source --manifest "$MANIFEST" --output-dir "$WORK/candidate" --json > "$WORK/convert.json" 2> "$WORK/convert.err" || abort SDOA_V2_CONVERT_FAILED 'Source conversion failed.'
    jq -e '.status==0' "$WORK/convert.json" >/dev/null || abort SDOA_V2_CONVERT_UNCONFIRMED 'Conversion not confirmed.'
    python3 scripts/ci/sf-kit-v2-policy.py verify --package "$PACKAGE_ID" --candidate-dir "$WORK/candidate" || abort SDOA_V2_CANDIDATE_DENIED 'Candidate differs from manifest.'
    args=(--candidate-dir "$WORK/candidate")
  fi
  python3 scripts/ci/sf-kit-v2-policy.py report --package "$PACKAGE_ID" --operation "$OPERATION" --remote-zip "$WORK/remote/package.zip" "${args[@]}" --output-file "$RUNNER_TEMP/sdoa-safe-report.json" || abort SDOA_V2_READ_SCOPE_DENIED 'Remote payload outside registered manifest.'
  private_export "$WORK/remote/package.zip" metadata.zip
  private_export "$WORK/retrieve.json" retrieve.json
  echo "SDOA_KIT_READ_COMPLETE: operation=$OPERATION target=$TARGET package=$PACKAGE_ID write=false v2=true"
  exit 0
fi
mkdir -p "$WORK/candidate"
sf project convert source --manifest "$MANIFEST" --output-dir "$WORK/candidate" --json > "$WORK/convert.json" 2> "$WORK/convert.err" || abort SDOA_V2_CONVERT_FAILED 'Source conversion failed.'
jq -e '.status==0' "$WORK/convert.json" >/dev/null || abort SDOA_V2_CONVERT_UNCONFIRMED 'Conversion not confirmed.'
python3 scripts/ci/sf-kit-v2-policy.py verify --package "$PACKAGE_ID" --candidate-dir "$WORK/candidate" || abort SDOA_V2_CANDIDATE_DENIED 'Candidate differs from manifest.'
mapfile -t RULES < <(python3 scripts/ci/sf-kit-v2-policy.py test-level --package "$PACKAGE_ID")
(( ${#RULES[@]} > 0 )) || abort SDOA_V2_TEST_POLICY_DENIED 'No test policy.'
TEST_LEVEL="${RULES[0]}"
test_args=(--test-level "$TEST_LEVEL")
if [[ "$TEST_LEVEL" == RunSpecifiedTests ]]; then
  (( ${#RULES[@]} > 1 )) || abort SDOA_V2_TESTS_MISSING 'Missing tests.'
  for name in "${RULES[@]:1}"; do test_args+=(--tests "$name"); done
fi
echo "SDOA_V2_DRY_RUN_STARTING: test_level=$TEST_LEVEL"
exit_code=0
sf project deploy start --dry-run --metadata-dir "$WORK/candidate" "${test_args[@]}" --target-org sdoa-v2 --wait 60 --json > "$WORK/dry.json" 2> "$WORK/dry.err" || exit_code=$?
safe_report "$WORK/dry.json" "$exit_code" DRY_RUN
private_export "$WORK/dry.json" validate.json
if [[ "$exit_code" != 0 ]] || ! jq -e '.status==0 and .result.success==true and (.result.done==true or .result.status=="Succeeded") and ((.result.numberComponentErrors // 0)==0) and ((.result.numberTestErrors // 0)==0)' "$WORK/dry.json" >/dev/null 2>&1; then
  abort SDOA_V2_DRY_RUN_FAILED 'Salesforce validation failed or result unknown; no real deploy.'
fi
echo "SDOA_M42_DRY_RUN_PASSED: v2 test_level=$TEST_LEVEL"
if [[ "$OPERATION" == plan ]]; then
  echo "SDOA_M42_PLAN_OK: v2 sandbox dry-run passed, no persistent metadata write."
  exit 0
fi
[[ "$CONFIRMATION" == "DEPLOY $TARGET $PACKAGE_ID" && "$(git rev-parse HEAD)" == "$GITHUB_SHA" && "$GITHUB_RUN_ATTEMPT" == 1 ]] || abort SDOA_V2_FINAL_GATE_DENIED 'Deploy authorization changed.'
echo '::warning title=SDOA v2 drift::Compare before deploy is recommended; org-side metadata may be overwritten.'
echo "SDOA_V2_REAL_DEPLOY_STARTING: sandbox=$TARGET immutable_commit=$GITHUB_SHA"
exit_code=0
sf project deploy start --metadata-dir "$WORK/candidate" "${test_args[@]}" --target-org sdoa-v2 --wait 60 --json > "$WORK/deploy.json" 2> "$WORK/deploy.err" || exit_code=$?
safe_report "$WORK/deploy.json" "$exit_code" REAL_DEPLOY
private_export "$WORK/deploy.json" deploy.json
if [[ "$exit_code" != 0 ]] || ! jq -e '.status==0 and .result.success==true and (.result.done==true or .result.status=="Succeeded") and ((.result.numberComponentErrors // 0)==0) and ((.result.numberTestErrors // 0)==0)' "$WORK/deploy.json" >/dev/null 2>&1; then
  abort SDOA_V2_DEPLOY_UNCONFIRMED 'Real deploy failed or unknown. Reconcile Salesforce Deployment Status; NEVER rerun.'
fi
echo "SDOA_REAL_DEPLOY_SUCCEEDED: Salesforce confirmed persistent deployment."
