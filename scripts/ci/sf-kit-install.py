#!/usr/bin/env python3
"""Idempotent installer for REVIEWED Salesforce DevOps Kit templates only.

Run from the reference repo checkout, with a separately reviewed destination
checkout. Do NOT generate or modify workflows when a destination file differs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

SOURCE_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path("templates/salesforce-devops-kit/v1/manifest.json")
PREFIX = "templates/salesforce-devops-kit/v1/files/"
DEST_PREFIXES = (".github/workflows/", "scripts/ci/", "tests/")


class InstallationError(ValueError):
    pass


def git_blob_sha(blob):
    return hashlib.sha1(b"blob " + str(len(blob)).encode("ascii") + b"\0" + blob).hexdigest()


def safe_child(root, rel):
    p = PurePosixPath(rel)
    if not rel or rel.startswith("/") or any(x in (".", "..") for x in p.parts) or "\\" in rel:
        raise InstallationError("Unsafe template path")
    selected = root
    for part in p.parts:
        selected = selected / part
        if selected.is_symlink():
            raise InstallationError("Symlink in template or target path")
    return selected


def inventory(source_root, target_root, require_approved=False):
    manifest_file = safe_child(source_root, MANIFEST.as_posix())
    doc = json.loads(manifest_file.read_text(encoding="utf8"))
    if doc.get("schema") != 1 or doc.get("kit") != "sdoa-salesforce-metadata-four-ops":
        raise InstallationError("Unrecognized kit manifest")
    if require_approved and doc.get("status") != "approved":
        raise InstallationError("Kit templates have not passed review/acceptance")
    if doc.get("operations") != ["retrieve", "compare", "validate", "deploy"]:
        raise InstallationError("Nonstandard kit operations")
    files = doc.get("files")
    if not isinstance(files, list) or len(files) != 9:
        raise InstallationError("Unexpected kit file count")
    if not target_root.is_dir() or target_root.is_symlink():
        raise InstallationError("Target root unavailable")
    for required in doc.get("required_project_files", []):
        p = safe_child(target_root, required)
        if not p.is_file():
            raise InstallationError("Destination project/catalog missing")
    target_catalog = json.loads(safe_child(target_root, "config/salesforce-devops/catalog.json").read_text("utf8"))
    if (target_catalog.get("schema") != 1 or not target_catalog.get("targets") or
            not target_catalog.get("packages")):
        raise InstallationError("Target/catalog not configured")
    results = []
    seen = set()
    for record in files:
        source, dest, sha = (record.get("source"), record.get("destination"), record.get("git_blob_sha"))
        if (not isinstance(source, str) or not source.startswith(PREFIX) or
                not isinstance(dest, str) or not dest.startswith(DEST_PREFIXES) or
                source != PREFIX + dest or not isinstance(sha, str) or len(sha) != 40 or
                any(c not in "0123456789abcdef" for c in sha)):
            raise InstallationError("Unexpected template target or digest")
        if dest in seen:
            raise InstallationError("Duplicate destination in kit")
        seen.add(dest)
        template = safe_child(source_root, source)
        candidate = template.read_bytes()
        if git_blob_sha(candidate) != sha:
            raise InstallationError("Template content hash differs from reviewed manifest")
        path = safe_child(target_root, dest)
        if path.exists():
            if not path.is_file():
                raise InstallationError("Target path is not a file")
            current = path.read_bytes()
            if current != candidate:
                raise InstallationError("Existing workflow/script differs; never overwrite automatically: " + dest)
            state = "unchanged"
        else:
            state = "missing"
        results.append((path, candidate, state, dest))
    return results


def install(source_root, target_root, apply=False):
    checks = inventory(source_root, target_root, require_approved=apply)
    if not apply:
        return [(dest, state) for _, _, state, dest in checks]
    created = []
    try:
        for path, content, state, dest in checks:
            if state != "missing":
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            # Ensure newly created path is still inside the destination root.
            if not path.parent.resolve().is_relative_to(target_root.resolve()):
                raise InstallationError("Target path escaped root")
            with path.open("xb") as out:
                out.write(content)
            created.append(path)
    except (OSError, InstallationError):
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    return [(dest, state if state == "unchanged" else "created") for _, _, state, dest in checks]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--target-root", required=True, type=Path)
    p.add_argument("--source-root", type=Path, default=SOURCE_ROOT)
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()
    try:
        statuses = install(args.source_root, args.target_root, args.apply)
        for path, state in statuses:
            print(f"SDOA_KIT_FILE: {state} {path}")
        print(f"SDOA_KIT_INSTALL_OK: apply={str(args.apply).lower()} files={len(statuses)}")
    except (OSError, ValueError, json.JSONDecodeError):
        print("::error title=SDOA_KIT_INSTALL_DENIED::Kit unavailable, hash mismatch, target invalid or conflicting existing file.")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
