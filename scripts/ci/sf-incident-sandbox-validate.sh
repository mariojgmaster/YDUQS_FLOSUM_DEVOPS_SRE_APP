#!/usr/bin/env bash
set -euo pipefail
umask 077
[[ "${EXPECTED_REF:-}" == "refs/heads/master" ]] || { echo "::error title=SANDBOX_REF_DENIED::Run only from master."; exit 1; }
[[ "${EXPECTED_ACTOR:-}" == "${EXPECTED_OWNER:-}" ]] || { echo "::error title=SANDBOX_ACTOR_DENIED::Only repository owner may run."; exit 1; }
[[ "${EXPECTED_RUN_ATTEMPT:-}" == "1" ]] || { echo "::error title=SANDBOX_RERUN_DENIED::Start a fresh owner-authored request."; exit 1; }
case "${EXPECTED_EVENT_NAME:-}" in
  workflow_dispatch) ;;
  issues)
    python3 scripts/ci/sf-incident-chatops-intent.py \
      --event "$GITHUB_EVENT_PATH" \
      --owner "$GITHUB_REPOSITORY_OWNER" \
      --repository "$GITHUB_REPOSITORY" || exit 1
    ;;
  *) echo "::error title=SANDBOX_EVENT_DENIED::Only manual or owner-authored Issue intent supported."; exit 1 ;;
esac
[[ "$(git rev-parse HEAD)" == "${EXPECTED_COMMIT_SHA:-}" ]] || { echo "::error title=SANDBOX_SHA_MISMATCH::Unexpected checkout."; exit 1; }

expected_url="https://yduqs--devsrefeat.sandbox.my.salesforce.com"
[[ "${SF_INSTANCE_URL:-}" == "$expected_url" ]] || { echo "::error title=SANDBOX_TARGET_DENIED::DevSreFeat only."; exit 1; }
for name in SF_CLIENT_ID SF_USERNAME SF_JWT_KEY; do
  [[ -n "${!name:-}" ]] || { echo "::error title=SANDBOX_SECRET_MISSING::Environment configuration incomplete."; exit 1; }
done

work_dir="$(mktemp -d "$RUNNER_TEMP/devsre-incidents.XXXXXXXX")"
trap 'rm -rf -- "$work_dir"' EXIT
printf '%s' "$SF_JWT_KEY" > "$work_dir/key.pem"
chmod 600 "$work_dir/key.pem"
if ! openssl pkey -in "$work_dir/key.pem" -noout -passin pass: > /dev/null 2>&1; then
  echo "::error title=SANDBOX_KEY_INVALID::JWT private key invalid."
  exit 1
fi

if ! sf org login jwt \
  --client-id "$SF_CLIENT_ID" \
  --username "$SF_USERNAME" \
  --jwt-key-file "$work_dir/key.pem" \
  --instance-url "$expected_url" \
  --alias devsrefeat-incidents \
  --json > "$work_dir/auth.json" 2> "$work_dir/auth.err"; then
  echo "::error title=SANDBOX_AUTH_FAILED::ECA/JWT authentication failed; raw data suppressed."
  exit 1
fi
echo "PASS: DEV_SRE_FEAT_AUTHENTICATED"
# Read-only inspection: find the ORIGINAL "Incidents & Rollbacks" navigation tab.
# Never print the full org metadata ZIP or retrieve it into the Git repo.
mkdir -p "$work_dir/navigation"
navigation_exit=0
sf project retrieve start --metadata CustomTab \
  --target-org devsrefeat-incidents \
  --target-metadata-dir "$work_dir/navigation" \
  --zip-file-name customtabs.zip \
  --wait 60 --json > "$work_dir/navigation-retrieve.json" 2> "$work_dir/navigation-retrieve.err" || navigation_exit=$?
if [[ "$navigation_exit" -ne 0 ]] ||
  ! jq -e '.status==0' "$work_dir/navigation-retrieve.json" >/dev/null 2>&1 ||
  [[ ! -s "$work_dir/navigation/customtabs.zip" ]]; then
  echo "::error title=INCIDENT_NAV_RETRIEVE_FAILED::Nao foi possivel recuperar definicoes de CustomTab sem escrever na org."
  exit 1
fi
python3 scripts/ci/sf-incident-original-tab-report.py --zip "$work_dir/navigation/customtabs.zip"
# Diagnostic preview only. This is NOT a deploy and never ignores conflicts.
python3 scripts/ci/verify-incident-navigation-scope.py
nav_exit=0
sf project deploy preview \
  --manifest manifest/sf-devops-sre-incidents-navigation.xml \
  --target-org devsrefeat-incidents --json \
  > "$work_dir/nav-preview.json" 2> "$work_dir/nav-preview.err" || nav_exit=$?
python3 scripts/ci/sf-incident-navigation-preview-report.py --file "$work_dir/nav-preview.json"
echo "INFO: INCIDENT_NAV_PREVIEW_EXIT=$nav_exit"
if [[ "$nav_exit" -ne 0 ]]; then
  echo "::error title=INCIDENT_NAV_PREVIEW_CLI_FAILED::Preview CLI exit diferente de zero."
  exit 1
fi

gate() { echo "::error title=$1::A safe metadata preflight failed."; exit 1; }
WORK="$work_dir"
ORG="devsrefeat-incidents"

# Safely convert reviewed THREE components to Metadata API format.
# Read live original tab and test class; reject drift, preserve all other tab settings.
mkdir -p "$WORK/remote-tabs" "$WORK/remote-class" "$WORK/mdapi"
sf project retrieve start --metadata CustomTab:incidentsRollbacks \
  --target-org "$ORG" --target-metadata-dir "$WORK/remote-tabs" \
  --zip-file-name tabs.zip --wait 60 --json >"$WORK/tabs.json" 2>"$WORK/tabs.err" ||
  gate INCIDENT_ORIGINAL_TAB_RETRIEVE_FAILED
jq -e '.status==0' "$WORK/tabs.json" >/dev/null || gate INCIDENT_ORIGINAL_TAB_READ_UNCONFIRMED
sf project retrieve start --metadata ApexClass:DevSreIncidentControllerTest \
  --target-org "$ORG" --target-metadata-dir "$WORK/remote-class" \
  --zip-file-name class.zip --wait 60 --json >"$WORK/class.json" 2>"$WORK/class.err" ||
  gate INCIDENT_TEST_CLASS_RETRIEVE_FAILED
jq -e '.status==0' "$WORK/class.json" >/dev/null || gate INCIDENT_TEST_CLASS_READ_UNCONFIRMED
sf project convert source --manifest manifest/sf-devops-sre-incidents-navigation.xml \
  --output-dir "$WORK/mdapi" --json >"$WORK/convert.json" 2>"$WORK/convert.err" ||
  gate INCIDENT_CONVERT_FAILED
jq -e '.status==0' "$WORK/convert.json" >/dev/null || gate INCIDENT_CONVERT_UNCONFIRMED
python3 scripts/ci/sf-incident-navigation-stage.py \
  --tabs "$WORK/remote-tabs/tabs.zip" \
  --klass "$WORK/remote-class/class.zip" \
  --candidate "$WORK/mdapi" --preview "$WORK/preview.json" ||
  gate INCIDENT_DELTA_SECURITY_FAILED

sf project deploy start --dry-run --metadata-dir "$work_dir/mdapi" \
  --test-level RunSpecifiedTests --tests DevSreIncidentControllerTest \
  --target-org devsrefeat-incidents --wait 60 --json \
  >"$work_dir/mdapi-dry.json" 2>"$work_dir/mdapi-dry.err" ||
  gate INCIDENT_SCOPED_DRY_RUN_FAILED
jq -e '.status==0 and .result.success==true and (.result.numberTestErrors // 0)==0' "$work_dir/mdapi-dry.json" >/dev/null ||
  gate INCIDENT_SCOPED_DRY_RUN_UNCONFIRMED
echo "PASS: INCIDENT_SCOPED_MDAPI_DRY_RUN"




sf_exit=0
sf project deploy start \
  --dry-run \
  --manifest manifest/sf-devops-sre-incidents-sandbox-validate.xml \
  --test-level RunSpecifiedTests \
  --tests DevSreIncidentControllerTest \
  --target-org devsrefeat-incidents \
  --wait 60 \
  --json > "$work_dir/dry-run.json" 2> "$work_dir/dry-run.err" || sf_exit=$?

if ! jq -e 'type=="object"' "$work_dir/dry-run.json" > /dev/null 2>&1; then
  python3 scripts/ci/sf-deploy-safe-diagnostic.py --file "$work_dir/dry-run.json" --exit "$sf_exit" --phase DRY_RUN
  python3 scripts/ci/sf-incident-component-diagnostics.py --file "$work_dir/dry-run.json"
  python3 scripts/ci/sf-incident-apex-test-diagnostics.py --file "$work_dir/dry-run.json"
  echo "::error title=INCIDENT_DRY_RUN_NO_RESULT::Metadata API gave no structured response."
  exit 1
fi
status="$(jq -r '.status // -1' "$work_dir/dry-run.json")"
success="$(jq -r '.result.success // false' "$work_dir/dry-run.json")"
result_status="$(jq -r '.result.status // "Unknown"' "$work_dir/dry-run.json")"
done="$(jq -r '.result.done // false' "$work_dir/dry-run.json")"
if [[ "$sf_exit" -ne 0 || "$status" != "0" || "$success" != "true" || ( "$done" != "true" && "$result_status" != "Succeeded" ) ]]; then
  # Existing M4 privacy-safe diagnostic exposes only bounded counts / enums,
  # never org identifiers, Apex names, component bodies or raw Salesforce errors.
  python3 scripts/ci/sf-deploy-safe-diagnostic.py --file "$work_dir/dry-run.json" --exit "$sf_exit" --phase DRY_RUN
  python3 scripts/ci/sf-incident-component-diagnostics.py --file "$work_dir/dry-run.json"
  python3 scripts/ci/sf-incident-apex-test-diagnostics.py --file "$work_dir/dry-run.json"
  echo "::error title=INCIDENT_DRY_RUN_FAILED::Salesforce rejected the dry-run. See privacy-safe category/counts above and DevSreFeat Deployment Status for details."
  exit 1
fi
echo "PASS: DEV_SRE_FEAT_INCIDENT_DRY_RUN"
echo "PASS: DEV_SRE_FEAT_INCIDENT_APEX_TEST_GATE"
echo "INFO: SANDBOX_NO_METADATA_WRITES"
