#!/usr/bin/env python3
"""Review-only Metadata API retrieval and Git↔Salesforce comparison report.

Output is safe for a PUBLIC GitHub repository: member names are allowlisted by
a reviewed manifest. No remote source, hashes, XML, file paths or raw errors.
"""
import argparse
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
POLICY = BASE / "scripts/ci/sf-deploy-policy.py"
spec = importlib.util.spec_from_file_location("sf_deploy_policy", POLICY)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


def produce(operation, package, zip_path, candidate_dir=None):
    if operation not in ("retrieve", "compare"):
        raise policy.PolicyError("Unreviewed read operation")
    catalog = policy.registry()
    info = policy.pkg_info(catalog, package)
    listed = policy.members(info)
    remote = policy.from_zip(zip_path)
    # Refuse unreviewed files and missing required metadata.
    policy.selected(remote, listed)
    names = [{"type": kind, "name": name} for kind, items in sorted(listed.items()) for name in sorted(items)]
    result = {
        "schema": "SDOA-KIT-READ/1",
        "operation": operation,
        "package_id": package,
        "components": names,
        "component_count": len(names),
        "raw_metadata_included": False,
        "remote_retrieved": True,
        "modified_salesforce": False,
        "modified_git": False,
    }
    if operation == "retrieve":
        result["result"] = "retrieved"
        result["differences"] = []
        return result
    if candidate_dir is None:
        raise policy.PolicyError("Missing reviewed source candidate")
    local = policy.from_dir(candidate_dir)
    policy.selected(local, listed)
    same, diff = policy.compare(local, remote, listed)
    changed = policy.mismatched_components(local, remote, listed) if not same else []
    parts = policy.mismatched_file_types(local, remote, listed) if not same else []
    result.update(
        result="equal" if same else "different",
        differing_files=diff,
        differing_members=changed,
        differing_parts=parts,
        differences=[{"member": item} for item in changed],
        # Only allowlisted Apex member IDs, API version/status, and bounded
        # XML shape flags. Never emit source or arbitrary metadata values.
        apex_metadata_facts=policy.mismatched_apex_metadata_facts(local, remote, listed) if not same else [],
        apex_metadata_structure=policy.differing_apex_metadata_structure(local, remote, listed) if not same else [],
    )
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--operation", choices=["retrieve", "compare"], required=True)
    p.add_argument("--package", required=True)
    p.add_argument("--remote-zip", type=Path, required=True)
    p.add_argument("--candidate-dir", type=Path)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    try:
        result = produce(args.operation, args.package, args.remote_zip, args.candidate_dir)
        args.report.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf8")
        if args.operation == "retrieve":
            print(f"SDOA_KIT_RETRIEVE_OK: reviewed_components={result['component_count']} raw_public=false")
        else:
            print(f"SDOA_KIT_COMPARE_OK: equal={str(result['result']=='equal').lower()} "
                  f"differences={result['differing_files']} reviewed_components={result['component_count']}")
    except (policy.PolicyError, OSError, ValueError, TypeError, KeyError):
        print("::error title=SDOA_KIT_READ_POLICY::Remote ZIP or registered package violates reviewed scope.")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
