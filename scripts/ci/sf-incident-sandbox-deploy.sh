#!/usr/bin/env bash
# REAL deployment script. Only workflow_dispatch from protected master.
set -euo pipefail
umask 077

manifest="manifest/sf-devops-sre-incidents-navigation.xml"
target_url="https://yduqs--devsrefeat.sandbox.my.salesforce.com"
target_alias="devsrefeat-incidents-deploy"
test_class="DevSreIncidentControllerTest"

fail() { echo "::error title=$1::$2"; exit 1; }
[[ "${EXPECTED_EVENT:-}" == "workflow_dispatch" ]] || fail INCIDENT_MANUAL_ONLY "Deploy requer workflow_dispatch manual."
[[ "${EXPECTED_REF:-}" == "refs/heads/master" ]] || fail INCIDENT_BRANCH_DENIED "Somente master e permitida."
[[ "${EXPECTED_ACTOR:-}" == "${EXPECTED_OWNER:-}" ]] || fail INCIDENT_OWNER_DENIED "Somente proprietario do repo."
[[ "${EXPECTED_ATTEMPT:-}" == "1" ]] || fail INCIDENT_RERUN_DENIED "Nao execute rerun de escrita."
[[ "${CONFIRMATION:-}" == "DEPLOY DevSreFeat" ]] || fail INCIDENT_CONFIRMATION_DENIED "Confirmacao literal obrigatoria."
[[ "${REQUESTED_SHA:-}" =~ ^[0-9a-fA-F]{40}$ ]] || fail INCIDENT_SHA_INVALID "SHA deve ter 40 caracteres."
[[ "${REQUESTED_SHA,,}" == "${EXPECTED_SHA,,}" ]] || fail INCIDENT_SHA_MISMATCH "SHA diverge do checkout solicitado."
[[ "$(git rev-parse HEAD)" == "${EXPECTED_SHA:-}" ]] || fail INCIDENT_CHECKOUT_MISMATCH "HEAD inesperado."
[[ "${SF_INSTANCE_URL:-}" == "$target_url" ]] || fail INCIDENT_TARGET_DENIED "Destino nao e DevSreFeat."
for key in SF_CLIENT_ID SF_USERNAME SF_JWT_KEY; do
  [[ -n "${!key:-}" ]] || fail INCIDENT_ECA_UNAVAILABLE "Configuracao ECA ausente."
done

# Same exact approved package in DRY-RUN and REAL DEPLOY.
python3 scripts/ci/verify-incident-navigation-scope.py >/dev/null ||
  fail INCIDENT_MANIFEST_DENIED "Manifesto/config nao aprovado."
[[ -f "$manifest" ]] || fail INCIDENT_MANIFEST_MISSING "Manifesto fixo ausente."
tmp_dir="$(mktemp -d "$RUNNER_TEMP/incidents-deploy.XXXXXXXX")"
trap 'rm -rf -- "$tmp_dir"' EXIT
printf '%s' "$SF_JWT_KEY" > "$tmp_dir/jwt.pem"
chmod 600 "$tmp_dir/jwt.pem"
openssl pkey -in "$tmp_dir/jwt.pem" -noout -passin pass: >/dev/null 2>&1 ||
  fail INCIDENT_JWT_INVALID "Chave JWT invalida."

if ! sf org login jwt \
  --client-id "$SF_CLIENT_ID" --username "$SF_USERNAME" \
  --jwt-key-file "$tmp_dir/jwt.pem" --instance-url "$target_url" \
  --alias "$target_alias" --json >"$tmp_dir/login.json" 2>"$tmp_dir/login.err"; then
  fail INCIDENT_AUTH_FAILED "Falha de autenticacao; consulte Login History sem publicar dados."
fi
echo "PASS: INCIDENT_DEPLOY_ECA_AUTH"

# Preview only. Treat conflicts, deletions and ignored components as blockers.
preview_exit=0
sf project deploy preview --manifest "$manifest" --target-org "$target_alias" --json \
  >"$tmp_dir/preview.json" 2>"$tmp_dir/preview.err" || preview_exit=$?
if [[ "$preview_exit" != "0" ]] || ! jq -e \
  '.status == 0 and (.result|type)=="object" and
   (.result.toDeploy|type)=="array" and
   (.result.conflicts|type)=="array" and
   (.result.toDelete|type)=="array" and
   (.result.ignored|type)=="array"' "$tmp_dir/preview.json" >/dev/null 2>&1; then
  fail INCIDENT_PREVIEW_FAILED "Preview Salesforce nao confirmou estrutura/estado sem conflitos."
fi
# Each jq expression is parenthesized inside the versioned jq filter.
# Check jq exit explicitly rather than process substitution (which hides failure).
preview_summary="$(jq -erf scripts/ci/incident-preview-counts.jq "$tmp_dir/preview.json")" ||
  fail INCIDENT_PREVIEW_PARSE_FAILED "JSON de preview nao pode ser interpretado com seguranca."
read -r deploy_count conflict_count delete_count ignored_count <<< "$preview_summary"
for amount in "$deploy_count" "$conflict_count" "$delete_count" "$ignored_count"; do
  [[ "$amount" =~ ^[0-9]+$ ]] || fail INCIDENT_PREVIEW_PARSE_FAILED "Contagem de preview invalida."
done
echo "INFO: INCIDENT_PREVIEW_SUMMARY to_deploy=$deploy_count conflicts=$conflict_count to_delete=$delete_count ignored=$ignored_count"
gate() { fail "$1" "Falha na verificacao do pacote ou do estado original da sandbox."; }

# Safely convert reviewed THREE components to Metadata API format.
# Read live original tab and test class; reject drift, preserve all other tab settings.
mkdir -p "$tmp_dir/remote-tabs" "$tmp_dir/remote-class" "$tmp_dir/mdapi"
sf project retrieve start --metadata CustomTab:incidentsRollbacks \
  --target-org "$target_alias" --target-metadata-dir "$tmp_dir/remote-tabs" \
  --zip-file-name tabs.zip --wait 60 --json >"$tmp_dir/tabs.json" 2>"$tmp_dir/tabs.err" ||
  gate INCIDENT_ORIGINAL_TAB_RETRIEVE_FAILED
jq -e '.status==0' "$tmp_dir/tabs.json" >/dev/null || gate INCIDENT_ORIGINAL_TAB_READ_UNCONFIRMED
sf project retrieve start --metadata ApexClass:DevSreIncidentControllerTest \
  --target-org "$target_alias" --target-metadata-dir "$tmp_dir/remote-class" \
  --zip-file-name class.zip --wait 60 --json >"$tmp_dir/class.json" 2>"$tmp_dir/class.err" ||
  gate INCIDENT_TEST_CLASS_RETRIEVE_FAILED
jq -e '.status==0' "$tmp_dir/class.json" >/dev/null || gate INCIDENT_TEST_CLASS_READ_UNCONFIRMED
sf project convert source --manifest manifest/sf-devops-sre-incidents-navigation.xml \
  --output-dir "$tmp_dir/mdapi" --json >"$tmp_dir/convert.json" 2>"$tmp_dir/convert.err" ||
  gate INCIDENT_CONVERT_FAILED
jq -e '.status==0' "$tmp_dir/convert.json" >/dev/null || gate INCIDENT_CONVERT_UNCONFIRMED
python3 scripts/ci/sf-incident-navigation-stage.py \
  --tabs "$tmp_dir/remote-tabs/tabs.zip" \
  --klass "$tmp_dir/remote-class/class.zip" \
  --candidate "$tmp_dir/mdapi" --preview "$tmp_dir/preview.json" ||
  gate INCIDENT_DELTA_SECURITY_FAILED


# Mandatory new dry-run in the SAME workflow, same checkout/org/tests.
dry_exit=0
sf project deploy start --dry-run --metadata-dir "$tmp_dir/mdapi" \
  --test-level RunSpecifiedTests --tests "$test_class" \
  --target-org "$target_alias" --wait 60 --json \
  >"$tmp_dir/dry.json" 2>"$tmp_dir/dry.err" || dry_exit=$?
python3 scripts/ci/sf-deploy-safe-diagnostic.py --file "$tmp_dir/dry.json" --exit "$dry_exit" --phase DRY_RUN
if [[ "$dry_exit" != "0" ]] || ! jq -e \
  '.status == 0 and .result.success == true and
   (.result.done == true or .result.status == "Succeeded") and
   (.result.numberComponentErrors // 0) == 0 and
   (.result.numberTestErrors // 0) == 0 and
   (.result.numberTestsCompleted // -1) >= 5' "$tmp_dir/dry.json" >/dev/null 2>&1; then
  python3 scripts/ci/sf-incident-component-diagnostics.py --file "$tmp_dir/dry.json"
  python3 scripts/ci/sf-incident-apex-test-diagnostics.py --file "$tmp_dir/dry.json"
  fail INCIDENT_DRY_RUN_FAILED "Nao houve validacao completa e testes Apex suficientes; nao implantado."
fi
echo "PASS: INCIDENT_SAME_RUN_DRY_RUN_AND_APEX_TESTS"

# Final authorization gate; no deploy based on a prior run.
[[ "${CONFIRMATION:-}" == "DEPLOY DevSreFeat" && "${REQUESTED_SHA,,}" == "${EXPECTED_SHA,,}" && "${EXPECTED_ATTEMPT:-}" == "1" ]] ||
  fail INCIDENT_FINAL_AUTH_DENIED "Confirmacao/SHA/attempt nao autorizados."
echo "INFO: INCIDENT_REAL_DEPLOY_STARTING target=DevSreFeat"
real_exit=0
sf project deploy start --metadata-dir "$tmp_dir/mdapi" \
  --test-level RunSpecifiedTests --tests "$test_class" \
  --target-org "$target_alias" --wait 60 --json \
  >"$tmp_dir/real.json" 2>"$tmp_dir/real.err" || real_exit=$?
python3 scripts/ci/sf-deploy-safe-diagnostic.py --file "$tmp_dir/real.json" --exit "$real_exit" --phase REAL_DEPLOY

if [[ "$real_exit" != "0" ]] || ! jq -e \
  '.status == 0 and .result.success == true and
   (.result.done == true or .result.status == "Succeeded") and
   (.result.numberComponentErrors // 0) == 0 and
   (.result.numberTestErrors // 0) == 0 and
   (.result.numberTestsCompleted // -1) >= 5' "$tmp_dir/real.json" >/dev/null 2>&1; then
  fail INCIDENT_REAL_DEPLOY_UNCONFIRMED "Falha ou estado ambiguo: verifique Deployment Status; NAO repita automaticamente."
fi
echo "PASS: INCIDENT_REAL_DEPLOY_CONFIRMED"
echo "INFO: INCIDENT_PERMISSIONSET_MEMBERSHIP_PENDING"
echo "INFO: INCIDENT_APP_MANAGER_AND_UI_HOMOLOGATION_PENDING"
