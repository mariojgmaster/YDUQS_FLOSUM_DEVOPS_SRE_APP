#!/usr/bin/env bash
# Sandbox-only destructive cleanup, AFTER original tab has migrated.
set -euo pipefail
umask 077
fail() { echo "::error title=$1::$2"; exit 1; }

[[ "$EXPECTED_REF" == refs/heads/master ]] || fail CLEANUP_BRANCH_DENIED "master only"
[[ "$EXPECTED_ACTOR" == "$EXPECTED_OWNER" ]] || fail CLEANUP_ACTOR_DENIED "owner only"
[[ "$EXPECTED_ATTEMPT" == 1 ]] || fail CLEANUP_RERUN_DENIED "rerun denied"
[[ "$CONFIRMATION" == 'DELETE DevSre_Incident_Intake DevSreFeat' ]] ||
  fail CLEANUP_CONFIRMATION_DENIED "literal confirmation required"
[[ "$REQUESTED_SHA" =~ ^[a-f0-9]{40}$ && "$REQUESTED_SHA" == "$EXPECTED_SHA" ]] ||
  fail CLEANUP_SHA_DENIED "SHA mismatch"
[[ "$(git rev-parse HEAD)" == "$EXPECTED_SHA" ]] || fail CLEANUP_CHECKOUT_DENIED "unexpected checkout"
[[ "$SF_INSTANCE_URL" == 'https://yduqs--devsrefeat.sandbox.my.salesforce.com' ]] ||
  fail CLEANUP_TARGET_DENIED "DevSreFeat only"
[[ -n "$SF_CLIENT_ID" && -n "$SF_USERNAME" && -n "$SF_JWT_KEY" ]] ||
  fail CLEANUP_ECA_DENIED "missing ECA configuration"
python3 scripts/ci/sf-incident-cleanup-preflight.py ||
  fail CLEANUP_SCOPE_DENIED "delete manifest not allowlisted"

tmp="$(mktemp -d "$RUNNER_TEMP/incident-cleanup.XXXXXXXX")"
trap 'rm -rf -- "$tmp"' EXIT
printf '%s' "$SF_JWT_KEY" > "$tmp/key.pem"
chmod 600 "$tmp/key.pem"
openssl pkey -in "$tmp/key.pem" -noout -passin pass: >/dev/null 2>&1 ||
  fail CLEANUP_KEY_DENIED "invalid JWT key"

sf org login jwt --client-id "$SF_CLIENT_ID" --username "$SF_USERNAME" \
  --jwt-key-file "$tmp/key.pem" --instance-url "$SF_INSTANCE_URL" \
  --alias incidents-cleanup --json > "$tmp/auth.json" 2>"$tmp/auth.err" ||
  fail CLEANUP_AUTH_DENIED "JWT login failed"
echo "PASS: INCIDENT_CLEANUP_AUTH"

mkdir -p "$tmp/remote"
sf project retrieve start \
  --metadata CustomTab:incidentsRollbacks \
  --metadata CustomTab:DevSre_Incident_Intake \
  --target-org incidents-cleanup --target-metadata-dir "$tmp/remote" \
  --zip-file-name tabs.zip --wait 60 --json > "$tmp/retrieve.json" 2>"$tmp/retrieve.err" ||
  fail CLEANUP_REMOTE_READ_DENIED "could not inspect both custom tabs"
jq -e '.status==0' "$tmp/retrieve.json" >/dev/null ||
  fail CLEANUP_REMOTE_READ_UNCONFIRMED "retrieve result invalid"
python3 scripts/ci/sf-incident-cleanup-preflight.py --zip "$tmp/remote/tabs.zip" ||
  fail CLEANUP_ORIGINAL_TAB_NOT_MIGRATED "original must point to host"

pkg="manifest/incidents-cleanup/package.xml"
del="manifest/incidents-cleanup/destructiveChangesPost.xml"
dry_exit=0
sf project deploy start --dry-run --manifest "$pkg" --post-destructive-changes "$del" \
  --test-level RunSpecifiedTests --tests DevSreIncidentControllerTest \
  --target-org incidents-cleanup --wait 60 --json > "$tmp/dry.json" 2>"$tmp/dry.err" ||
  dry_exit=$?
python3 scripts/ci/sf-deploy-safe-diagnostic.py --file "$tmp/dry.json" --exit "$dry_exit" --phase DRY_RUN
[[ "$dry_exit" == 0 ]] &&
  jq -e '.status==0 and .result.success==true and (.result.numberComponentErrors // 0)==0 and (.result.numberTestErrors // 0)==0' "$tmp/dry.json" >/dev/null ||
  fail CLEANUP_DRY_RUN_FAILED "deletion not attempted"
echo "PASS: INCIDENT_DUPLICATE_ONLY_DRY_RUN"

python3 scripts/ci/sf-incident-cleanup-preflight.py ||
  fail CLEANUP_SCOPE_CHANGED "invalid delete manifest"
real_exit=0
sf project deploy start --manifest "$pkg" --post-destructive-changes "$del" \
  --test-level RunSpecifiedTests --tests DevSreIncidentControllerTest \
  --target-org incidents-cleanup --wait 60 --json > "$tmp/real.json" 2>"$tmp/real.err" ||
  real_exit=$?
python3 scripts/ci/sf-deploy-safe-diagnostic.py --file "$tmp/real.json" --exit "$real_exit" --phase REAL_DEPLOY
[[ "$real_exit" == 0 ]] &&
  jq -e '.status==0 and .result.success==true and (.result.numberComponentErrors // 0)==0 and (.result.numberTestErrors // 0)==0' "$tmp/real.json" >/dev/null ||
  fail CLEANUP_UNCONFIRMED "inspect Salesforce Deployment Status before retrying"
echo "PASS: INCIDENT_DUPLICATE_TAB_DELETED"
