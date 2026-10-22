#!/usr/bin/env bash
# Salesforce Metadata API M3 pilot - only DevSreFeat, no deploy, no raw org data in logs.
set -euo pipefail
umask 077

abort() { echo "::error title=$1::$2"; exit 1; }

case "$OPERATION" in
  retrieve|compare|validate) ;;
  *) abort "M3_INVALID_OPERATION" "Choose retrieve, compare, or validate only." ;;
esac

if [[ "$SF_INSTANCE_URL" != "https://yduqs--devsrefeat.sandbox.my.salesforce.com" ]]; then
  abort "M3_WRONG_TARGET" "The GitHub Environment must point exclusively to DevSreFeat."
fi
if [[ -z "$SF_CLIENT_ID" || -z "$SF_USERNAME" || -z "$SF_JWT_KEY" ]]; then
  abort "M3_MISSING_SECRET" "GitHub Environment ECA/JWT Secrets are not configured."
fi

MANIFEST="manifest/sf-devsrefeat-m3.xml"
if [[ ! -s "$MANIFEST" ]]; then
  abort "M3_MANIFEST_MISSING" "The allowlisted manifest file is missing."
fi
# Prevent accidentally expanding M3's narrow metadata scope by editing the manifest.
python3 - "$MANIFEST" <<'PY' || exit 1
import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
ns = {"m": "http://soap.sforce.com/2006/04/metadata"}
types = root.findall("m:types", ns)
expected = {"CompareSecurityCode", "CompareSecurityCodeTest"}
if len(types) != 1 or types[0].findtext("m:name", namespaces=ns) != "ApexClass":
    print("::error title=M3_MANIFEST_SCOPE::Only explicitly selected ApexClass metadata is allowed.")
    sys.exit(1)
names = [e.text for e in types[0].findall("m:members", ns)]
if set(names) != expected or len(names) != 2:
    print("::error title=M3_MANIFEST_SCOPE::The pilot manifest must name exactly two authorized classes.")
    sys.exit(1)
print("Manifest scope verified: two explicit Apex classes, no wildcards.")
PY

TEMP_DIR="$(mktemp -d "$GITHUB_WORKSPACE/.sf-devops-m3.XXXXXXXX")"
cleanup() {
  # Secrets and retrieved org metadata are never uploaded as artifacts or committed.
  rm -rf -- "$TEMP_DIR"
}
trap cleanup EXIT
printf '%s' "$SF_JWT_KEY" > "$TEMP_DIR/jwt.key"
if ! openssl pkey -in "$TEMP_DIR/jwt.key" -noout -passin pass: >/dev/null 2>&1; then
  abort "M3_INVALID_KEY" "GitHub Environment SF_JWT_KEY must be a valid unencrypted PEM private key."
fi

if ! sf org login jwt \
  --client-id "$SF_CLIENT_ID" \
  --username "$SF_USERNAME" \
  --jwt-key-file "$TEMP_DIR/jwt.key" \
  --instance-url "$SF_INSTANCE_URL" \
  --alias devsrefeat-m3 \
  --json > "$TEMP_DIR/login.json" 2> "$TEMP_DIR/login.err"; then
  abort "M3_AUTH_FAILED" "JWT login failed; review ECA, integration user, GitHub Secrets and Salesforce Login History."
fi
echo "JWT authorization succeeded for the configured sandbox (details withheld)."

if [[ "$OPERATION" == "retrieve" || "$OPERATION" == "compare" ]]; then
  if ! sf project retrieve start \
    --manifest "$MANIFEST" \
    --output-dir "$TEMP_DIR/retrieved" \
    --target-org devsrefeat-m3 \
    --wait 30 \
    --json > "$TEMP_DIR/retrieve.json" 2> "$TEMP_DIR/retrieve.err"; then
    abort "M3_RETRIEVE_FAILED" "Metadata retrieval failed; inspect permissions/API access using a secure Salesforce client."
  fi
  if ! jq -e '.status == 0' "$TEMP_DIR/retrieve.json" >/dev/null 2>&1; then
    abort "M3_RETRIEVE_INCOMPLETE" "Retrieval returned a non-success status; org output intentionally withheld."
  fi

  # Only count exact allowlisted files. Never print retrieved source or SHA hashes.
  if [[ "$OPERATION" == "retrieve" ]]; then
    python3 - "$TEMP_DIR/retrieved" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
names = {"CompareSecurityCode.cls", "CompareSecurityCodeTest.cls"}
files = [p for p in root.rglob("*.cls") if p.parent.name == "classes" and p.name in names]
count = len({p.name for p in files})
print("M3_RETRIEVE_SUMMARY: Apex classes retrieved=" + str(count) + " expected=2")
if count != 2 or len(files) != 2:
    print("::error title=M3_RETRIEVE_MISSING::The selected source files were not returned.")
    sys.exit(1)
PY
  else
    python3 - "$TEMP_DIR/retrieved" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
local = pathlib.Path("force-app/main/default/classes")
names = [
    "CompareSecurityCode.cls",
    "CompareSecurityCode.cls-meta.xml",
    "CompareSecurityCodeTest.cls",
    "CompareSecurityCodeTest.cls-meta.xml",
]
same, different, missing = 0, 0, 0
for name in names:
    candidates = [p for p in root.rglob(name) if p.parent.name == "classes" and p.is_file()]
    path = local / name
    if len(candidates) != 1 or not path.is_file():
        missing += 1
        continue
    # Normalize line endings only; no retrieved content or hashes leave the runner.
    normalized = lambda x: x.read_bytes().replace(b"\r\n", b"\n").rstrip(b"\n")
    if normalized(candidates[0]) == normalized(path):
        same += 1
    else:
        different += 1
print(f"M3_COMPARE_SUMMARY: same={same} different={different} missing={missing}")
if different or missing:
    print("::error title=M3_METADATA_DRIFT::Apex metadata differs or is missing; inspect comparison privately before a deployment.")
    sys.exit(1)
PY
  fi
else
  # Salesforce recommends deploy start --dry-run for sandbox validation, not deploy validate.
  exit_code=0
  sf project deploy start \
    --dry-run \
    --manifest "$MANIFEST" \
    --test-level RunSpecifiedTests \
    --tests CompareSecurityCodeTest \
    --target-org devsrefeat-m3 \
    --wait 40 \
    --json > "$TEMP_DIR/validate.json" 2> "$TEMP_DIR/validate.err" || exit_code=$?

  if jq -e 'type=="object"' "$TEMP_DIR/validate.json" >/dev/null 2>&1; then
    tests=$(jq -r '.result.numberTestsCompleted // .result.details.runTestResult.numTestsRun // "unknown" | tostring | if test("^[0-9]+$") then . else "unknown" end' "$TEMP_DIR/validate.json" 2>/dev/null || echo unknown)
    test_errors=$(jq -r '.result.numberTestErrors // .result.details.runTestResult.numFailures // "unknown" | tostring | if test("^[0-9]+$") then . else "unknown" end' "$TEMP_DIR/validate.json" 2>/dev/null || echo unknown)
    echo "M3_VALIDATE_SUMMARY: executed_tests=$tests test_errors=$test_errors persisted_deploy=no"
  fi
  if [[ "$exit_code" -ne 0 ]] || ! jq -e '.status == 0 and .result.success == true and (.result.done == true or .result.status == "Succeeded")' "$TEMP_DIR/validate.json" >/dev/null 2>&1; then
    abort "M3_VALIDATE_FAILED" "Dry-run validation failed or is incomplete; consult Setup > Deployment Status and Apex Test Execution privately."
  fi
  echo "M3_VALIDATION_PASSED: selected Apex metadata validated without persistent deployment."
fi
