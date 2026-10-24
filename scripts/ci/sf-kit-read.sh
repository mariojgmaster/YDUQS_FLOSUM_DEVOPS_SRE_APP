#!/usr/bin/env bash
# Standard read-only Salesforce Metadata API operations for reviewed packages.
set -euo pipefail
umask 077
die() { echo "::error title=$1::$2"; exit 1; }
: "${OPERATION:?}" "${TARGET:?}" "${PACKAGE_ID:?}"
[[ "$OPERATION" == retrieve || "$OPERATION" == compare ]] || die SDOA_KIT_READ_DENIED "Retrieve or compare only."
[[ "$GITHUB_EVENT_NAME" == issues && "$GITHUB_REF" == refs/heads/master ]] || die SDOA_KIT_TRIGGER_DENIED "Owner Issue on master required."
[[ "$GITHUB_ACTOR" == "$GITHUB_REPOSITORY_OWNER" && "$GITHUB_RUN_ATTEMPT" == 1 ]] || die SDOA_KIT_ACTOR_DENIED "Owner and first attempt required."
[[ "$GITHUB_SHA" =~ ^[a-f0-9]{40}$ && "$(git rev-parse HEAD)" == "$GITHUB_SHA" ]] || die SDOA_KIT_SHA_DENIED "Checkout SHA mismatch."
python3 scripts/ci/sf-m5-chatops-intent.py --event "$GITHUB_EVENT_PATH" --owner "$GITHUB_REPOSITORY_OWNER" \
  --repository "$GITHUB_REPOSITORY" --operation "$OPERATION" --target "$TARGET" --package "$PACKAGE_ID" \
  --commit-sha "$GITHUB_SHA" || die SDOA_KIT_INTENT_DENIED "Issue intent mismatch."
[[ -n "${SF_CLIENT_ID:-}" && -n "${SF_USERNAME:-}" && -n "${SF_JWT_KEY:-}" ]] || die SDOA_KIT_AUTH_CONFIG "Missing ECA/JWT secrets."
[[ -n "${SF_INSTANCE_URL:-}" && "$SF_INSTANCE_URL" == "${EXPECTED_INSTANCE_URL:-}" ]] || die SDOA_KIT_TARGET_DENIED "Registered target differs from configured org."

TMP="$(mktemp -d "$RUNNER_TEMP/sdoa-kit-read.XXXXXXXX")"
cleanup() { rm -rf -- "$TMP"; }
trap cleanup EXIT
python3 scripts/ci/sf-deploy-policy.py resolve --target "$TARGET" --package "$PACKAGE_ID" --output-file "$TMP/catalog" > /dev/null \
  || die SDOA_KIT_CATALOG_DENIED "Target/package not approved."
[[ "$(sed -n 's/^github_environment=//p' "$TMP/catalog" | tail -1)" == "$GITHUB_ENVIRONMENT_NAME" ]] \
  || die SDOA_KIT_ENV_DENIED "Environment mismatch."
MANIFEST="$(sed -n 's/^manifest=//p' "$TMP/catalog" | tail -1)"
[[ -f "$MANIFEST" && ! -L "$MANIFEST" ]] || die SDOA_KIT_MANIFEST_DENIED "Manifest unavailable."

printf '%s' "$SF_JWT_KEY" > "$TMP/key.pem"
openssl pkey -in "$TMP/key.pem" -noout -passin pass: >/dev/null 2>&1 \
  || die SDOA_KIT_KEY_DENIED "Invalid private key."
sf org login jwt --client-id "$SF_CLIENT_ID" --username "$SF_USERNAME" --jwt-key-file "$TMP/key.pem" \
  --instance-url "$SF_INSTANCE_URL" --alias sdoa-kit-read --json > "$TMP/auth.json" 2> "$TMP/auth.err" \
  || die SDOA_KIT_AUTH_FAILED "JWT login rejected."
jq -e '.status==0' "$TMP/auth.json" >/dev/null 2>&1 \
  || die SDOA_KIT_AUTH_FAILED "JWT response not confirmed."
echo "SDOA_KIT_AUTH_OK: owner-authorized sandbox."

mkdir -p "$TMP/remote"
sf project retrieve start --manifest "$MANIFEST" --target-org sdoa-kit-read --target-metadata-dir "$TMP/remote" \
  --zip-file-name package.zip --wait 60 --json > "$TMP/retrieve.json" 2> "$TMP/retrieve.err" \
  || die SDOA_KIT_RETRIEVE_FAILED "Retrieve failed; raw details withheld."
jq -e '.status==0' "$TMP/retrieve.json" >/dev/null 2>&1 \
  || die SDOA_KIT_RETRIEVE_UNCONFIRMED "Salesforce retrieve result not confirmed."
[[ -f "$TMP/remote/package.zip" && ! -L "$TMP/remote/package.zip" ]] \
  || die SDOA_KIT_ZIP_MISSING "Expected Metadata API ZIP missing."

if [[ "$OPERATION" == compare ]]; then
  mkdir -p "$TMP/candidate"
  sf project convert source --manifest "$MANIFEST" --output-dir "$TMP/candidate" --json \
    > "$TMP/convert.json" 2> "$TMP/convert.err" \
    || die SDOA_KIT_CONVERT_FAILED "Could not convert approved Git manifest."
  jq -e '.status==0' "$TMP/convert.json" >/dev/null 2>&1 \
    || die SDOA_KIT_CONVERT_UNCONFIRMED "Conversion not confirmed."
  python3 scripts/ci/sf-deploy-policy.py compare --package "$PACKAGE_ID" --left "$TMP/candidate" \
    --right "$TMP/candidate" --label candidate >/dev/null \
    || die SDOA_KIT_CANDIDATE_DENIED "Candidate metadata invalid."
  python3 scripts/ci/sf-kit-read-report.py --operation compare --package "$PACKAGE_ID" \
    --candidate-dir "$TMP/candidate" --remote-zip "$TMP/remote/package.zip" \
    --report "$RUNNER_TEMP/sdoa-safe-report.json" \
    || die SDOA_KIT_COMPARE_FAILED "Comparison blocked by metadata shape."
else
  python3 scripts/ci/sf-kit-read-report.py --operation retrieve --package "$PACKAGE_ID" \
    --remote-zip "$TMP/remote/package.zip" --report "$RUNNER_TEMP/sdoa-safe-report.json" \
    || die SDOA_KIT_RETRIEVE_SCOPE_DENIED "Remote metadata invalid or outside allowlist."
fi

# Export raw metadata only if explicitly enabled in a PRIVATE GitHub repo.
if [[ "${GITHUB_EVENT_REPOSITORY_PRIVATE:-false}" == true && "${SDOA_EXPORT_RAW:-false}" == true ]]; then
  mkdir -p "$RUNNER_TEMP/sdoa-private-raw"
  cp "$TMP/remote/package.zip" "$RUNNER_TEMP/sdoa-private-raw/metadata.zip"
  cp "$TMP/retrieve.json" "$RUNNER_TEMP/sdoa-private-raw/retrieve.json"
  echo "SDOA_KIT_PRIVATE_RAW_READY: restricted artifact, requires Actions read."
else
  echo "SDOA_KIT_PUBLIC_SAFE_ONLY: raw response not exported."
fi
echo "SDOA_KIT_READ_COMPLETE: operation=$OPERATION target=$TARGET package=$PACKAGE_ID write=false"
