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

# Classify only known CLI/Salesforce errors. Never publish raw metadata
# responses, usernames, org IDs, sources or full stack traces in this PUBLIC repo.
diagnose_retrieve() {
  local stdout="$TEMP_DIR/retrieve.json"
  local stderr="$TEMP_DIR/retrieve.err"
  if grep -Eiq 'INVALID_SESSION_ID|invalid access token|session expired|expired access token' "$stdout" "$stderr"; then
    abort "M3_RETRIEVE_SESSION" "The Salesforce session was rejected by Metadata API; inspect OAuth user/session policies."
  elif grep -Eiq 'INSUFFICIENT_ACCESS|INVALID_PERMISSION|not authorized|unauthorized|access denied|insufficient privileges|Modify Metadata Through Metadata API Functions|Modify All Data|missing.*permission|permission.*required|permission.*denied' "$stdout" "$stderr"; then
    abort "M3_RETRIEVE_PERMISSION" "The integration user might lack Metadata API permissions. Review Modify Metadata Through Metadata API Functions and required type-specific permissions with an admin; do not grant wider access automatically."
  elif grep -Eiq 'outputDirOutsideProject|outputDirOverlapsPackage|retrieveTargetDirOverlapsPackage|output directory|output-dir|outside.*project|ENOENT|EACCES|permission denied.*directory' "$stdout" "$stderr"; then
    abort "M3_RETRIEVE_LOCAL_PATH" "Salesforce CLI rejected the local retrieval path. Verify a writable directory inside the SFDX project outside force-app."
  elif grep -Eiq 'Nonexistent flag|Unexpected argument|unknown flag|flag .* not found|unknown option|invalid option|Invalid flag' "$stdout" "$stderr"; then
    abort "M3_RETRIEVE_CLI_FLAGS" "CLI arguments are not supported by the installed version. Inspect the available sf project retrieve start flags privately."
  elif grep -Eiq 'SourceConflict|source conflict|conflicts detected|conflict detected' "$stdout" "$stderr"; then
    abort "M3_RETRIEVE_SOURCE_CONFLICT" "Source tracking reported a conflict. Do not bypass or overwrite local project files."
  elif grep -Eiq 'No source-backed components|no metadata found|metadata .* not found|Could not find.*metadata|ENTITY_IS_DELETED|INVALID_TYPE|UNKNOWN_EXCEPTION' "$stdout" "$stderr"; then
    abort "M3_RETRIEVE_METADATA" "Manifest component/type may be unavailable or retrieval was rejected; verify ApexClass metadata names and org access."
  elif grep -Eiq 'REQUEST_LIMIT_EXCEEDED|rate limit|ETIMEDOUT|ECONNRESET|EAI_AGAIN|ENOTFOUND|timed out|network error' "$stdout" "$stderr"; then
    abort "M3_RETRIEVE_TRANSIENT" "The request hit a network, timeout or rate-limit error. Review limits and retry only when appropriate."
  else
    abort "M3_RETRIEVE_UNCLASSIFIED" "Retrieve failed with an unclassified error. Raw output stays private; inspect the exact error only in an authorized, non-public Salesforce CLI environment."
  fi
}

if [[ "$OPERATION" == "retrieve" || "$OPERATION" == "compare" ]]; then
  # Retrieve in Metadata API ZIP format rather than source format.
  # CLI source-format retrieve can update tracking state and/or write files
  # outside the output subtree when a sandbox has Source Tracking enabled.
  # Metadata ZIP is immutable and inspectable without converting to SFDX.
  ISOLATED_PROJECT="$TEMP_DIR/isolated-sfdx-project"
  MDAPI_DIR="$TEMP_DIR/mdapi"
  mkdir -p "$ISOLATED_PROJECT/empty-source" "$MDAPI_DIR"
  cat > "$ISOLATED_PROJECT/sfdx-project.json" <<'JSON'
{
  "packageDirectories": [{"path": "empty-source", "default": true}],
  "name": "sf-devsrefeat-m3-metadata",
  "namespace": "",
  "sourceApiVersion": "67.0"
}
JSON
  retrieve_exit=0
  (
    cd "$ISOLATED_PROJECT"
    sf project retrieve start \
      --manifest "$GITHUB_WORKSPACE/$MANIFEST" \
      --target-metadata-dir "$MDAPI_DIR" \
      --target-org devsrefeat-m3 \
      --wait 30 \
      --json
  ) > "$TEMP_DIR/retrieve.json" 2> "$TEMP_DIR/retrieve.err" || retrieve_exit=$?

  if [[ "$retrieve_exit" -ne 0 ]]; then
    diagnose_retrieve
  fi
  if ! jq -e '.status == 0' "$TEMP_DIR/retrieve.json" >/dev/null 2>&1; then
    diagnose_retrieve
  fi

  # Read only an allowlisted set of files inside the ZIP. Never extract it,
  # upload it as an artifact, print the class bodies, or print hashes.
  python3 - "$OPERATION" "$MDAPI_DIR" "$GITHUB_WORKSPACE/force-app/main/default/classes" <<'PY'
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, BadZipFile
import sys

operation, mdapi_folder, checked_out_classes = sys.argv[1:]
zip_root = Path(mdapi_folder)
local_root = Path(checked_out_classes)

def stop(code, description):
    print(f"::error title={code}::{description}")
    sys.exit(1)

archives = [p for p in zip_root.glob("*.zip") if p.is_file()]
if len(archives) != 1:
    stop("M3_RETRIEVE_ARCHIVE_MISSING",
         "The CLI succeeded but did not produce exactly one Metadata API ZIP.")

source_names = ("CompareSecurityCode.cls", "CompareSecurityCodeTest.cls")
all_names = (
    "CompareSecurityCode.cls",
    "CompareSecurityCode.cls-meta.xml",
    "CompareSecurityCodeTest.cls",
    "CompareSecurityCodeTest.cls-meta.xml",
)
try:
    with ZipFile(archives[0]) as archive:
        matched = {}
        for entry in archive.infolist():
            parts = PurePosixPath(entry.filename).parts
            if (".." in parts or entry.filename.startswith("/")):
                stop("M3_RETRIEVE_ARCHIVE_UNSAFE", "An unsafe ZIP member path was detected.")
            if entry.is_dir() or len(parts) < 2 or parts[-2] != "classes":
                continue
            if parts[-1] in all_names:
                if parts[-1] in matched or entry.file_size > 2_000_000:
                    stop("M3_RETRIEVE_ARCHIVE_UNSAFE",
                         "Duplicate or oversized metadata component in the returned ZIP.")
                matched[parts[-1]] = entry

        sources_found = sum(name in matched for name in source_names)
        if sources_found != len(source_names):
            print(f"M3_RETRIEVE_SUMMARY: Apex classes retrieved={sources_found} expected=2")
            stop("M3_RETRIEVE_MISSING",
                 "The Metadata API ZIP does not contain both expected Apex classes.")

        if operation == "retrieve":
            print("M3_RETRIEVE_SUMMARY: Apex classes retrieved=2 expected=2")
        else:
            same = different = missing = 0
            for name in all_names:
                file_path = local_root / name
                if name not in matched or not file_path.is_file():
                    missing += 1
                    continue
                if file_path.stat().st_size > 2_000_000:
                    stop("M3_COMPARE_FILE_TOO_LARGE", "An allowlisted local file is too large.")
                remote = archive.read(matched[name]).replace(b"\r\n", b"\n").rstrip(b"\n")
                local = file_path.read_bytes().replace(b"\r\n", b"\n").rstrip(b"\n")
                if remote == local:
                    same += 1
                else:
                    different += 1
            print(f"M3_COMPARE_SUMMARY: same={same} different={different} missing={missing}")
            if different or missing:
                stop("M3_METADATA_DRIFT",
                     "The retrieved metadata differs from GitHub or a file is missing; review privately.")
except BadZipFile:
    stop("M3_RETRIEVE_INVALID_ARCHIVE", "The Metadata API archive is invalid.")
PY
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
