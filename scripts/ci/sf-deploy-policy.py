#!/usr/bin/env python3
"""Fail-closed Metadata API package policy, ZIP reader and baseline comparator."""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, BadZipFile

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "config/salesforce-devops/catalog.json"
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,59}$")
ENV = re.compile(r"^sf-[a-z0-9-]{4,80}$")
FOLDERS = {"ApexClass": "classes", "LightningComponentBundle": "lwc"}
NS = {"m": "http://soap.sforce.com/2006/04/metadata"}
MAX_FILE = 2_000_000
MAX_FILES = 300
MAX_TOTAL = 15_000_000

class PolicyError(Exception):
    pass

def registry():
    d = json.loads(CATALOG.read_text("utf-8"))
    if d.get("schema") != 1 or not isinstance(d.get("targets"), dict) or not isinstance(d.get("packages"), dict):
        raise PolicyError("Unreviewed catalog schema")
    return d

def pkg_info(d, package):
    if not KEY.fullmatch(package) or package not in d["packages"]:
        raise PolicyError("Unregistered package")
    info = d["packages"][package]
    if not re.fullmatch(r"manifest/[A-Za-z0-9_-]+\.xml", info.get("manifest", "")):
        raise PolicyError("Manifest path outside reviewed directory")
    if info.get("test_level") != "RunSpecifiedTests":
        raise PolicyError("Apex test level not allowed")
    tests = info.get("tests")
    if not isinstance(tests, list) or not (1 <= len(tests) <= 15) or any(not isinstance(t, str) or not NAME.fullmatch(t) for t in tests):
        raise PolicyError("Explicit Apex tests required")
    allowed = info.get("allowed_types")
    if not isinstance(allowed, list) or not allowed or len(allowed) != len(set(allowed)) or any(t not in FOLDERS for t in allowed):
        raise PolicyError("Metadata type not supported")
    return info

def members(info):
    path = ROOT / info["manifest"]
    if path.is_symlink() or not path.is_file():
        raise PolicyError("Manifest missing/symlink")
    root = ET.parse(path).getroot()
    if root.tag != "{http://soap.sforce.com/2006/04/metadata}Package" or root.findtext("m:version", namespaces=NS) != "67.0":
        raise PolicyError("Manifest schema or version not reviewed")
    groups = root.findall("m:types", NS)
    if len(groups) != len(info["allowed_types"]):
        raise PolicyError("Manifest type count does not match catalog")
    output = {}
    for group in groups:
        typ = group.findtext("m:name", namespaces=NS)
        names = [node.text or "" for node in group.findall("m:members", NS)]
        if typ not in info["allowed_types"] or typ in output:
            raise PolicyError("Unapproved or duplicated type")
        if not names or len(names) != len(set(names)) or any(not NAME.fullmatch(name) for name in names):
            raise PolicyError("Invalid, repeated or wildcard member")
        output[typ] = names
    if set(output) != set(info["allowed_types"]):
        raise PolicyError("Wrong metadata types")
    return output

def target(d, alias):
    if alias not in d["targets"] or not KEY.fullmatch(alias):
        raise PolicyError("Unregistered target")
    t = d["targets"][alias]
    if not ENV.fullmatch(t.get("github_environment", "")):
        raise PolicyError("GitHub Environment name rejected")
    if t.get("kind") != "sandbox" or not re.fullmatch(r"https://[A-Za-z0-9-]+\.sandbox\.my\.salesforce\.com", t.get("instance_url", "")):
        raise PolicyError("Only approved sandbox My Domains supported")
    return t

def validate_map(files):
    if len(files) > MAX_FILES or sum(map(len, files.values())) > MAX_TOTAL:
        raise PolicyError("Package too large")
    for path, data in files.items():
        parts = PurePosixPath(path).parts
        if path.startswith("/") or "." in parts or ".." in parts or (len(parts) < 2 and path != "package.xml") or len(data) > MAX_FILE:
            raise PolicyError("Invalid metadata path or size")
    return files

def from_dir(path):
    folder = Path(path)
    if not folder.is_dir() or folder.is_symlink():
        raise PolicyError("Converted package directory missing")
    files = {}
    for p in folder.rglob("*"):
        if p.is_symlink():
            raise PolicyError("Symlink in package")
        if p.is_file():
            if p.stat().st_size > MAX_FILE:
                raise PolicyError("Metadata file exceeds limit")
            files[p.relative_to(folder).as_posix()] = p.read_bytes()
    return validate_map(files)

def from_zip(path):
    try:
        with ZipFile(path) as archive:
            entries = [e for e in archive.infolist() if not e.is_dir()]
            if len(entries) > MAX_FILES:
                raise PolicyError("Too many ZIP members")
            roots = [PurePosixPath(e.filename).parts[:-1] for e in entries if PurePosixPath(e.filename).name == "package.xml"]
            if len(roots) != 1:
                raise PolicyError("Exactly one Metadata API manifest required")
            prefix = roots[0]
            files = {}
            for e in entries:
                parts = PurePosixPath(e.filename).parts
                if e.filename.startswith("/") or ".." in parts or parts[:len(prefix)] != prefix or ((e.external_attr >> 16) & 0o170000) == 0o120000:
                    raise PolicyError("Unsafe ZIP member")
                if e.file_size > MAX_FILE:
                    raise PolicyError("Oversized ZIP member")
                rel = "/".join(parts[len(prefix):])
                if not rel or rel in files:
                    raise PolicyError("Repeated ZIP member")
                files[rel] = archive.read(e)
            return validate_map(files)
    except BadZipFile as e:
        raise PolicyError("Invalid Metadata API archive") from e

def normalized(data, path):
    raw = data.replace(b"\r\n", b"\n").rstrip(b"\n")
    if path.endswith(".xml"):
        try:
            root = ET.fromstring(raw)
            def trim(el):
                if len(el) and el.text is not None and not el.text.strip():
                    el.text = None
                if el.tail is not None and not el.tail.strip():
                    el.tail = None
                for child in el: trim(child)
            trim(root)
            return ET.tostring(root, encoding="utf-8")
        except ET.ParseError as e:
            raise PolicyError("Invalid XML in package") from e
    return raw

def selected(files, manifest):
    required = set()
    for typ, names in manifest.items():
        for name in names:
            if typ == "ApexClass":
                required.update([f"classes/{name}.cls", f"classes/{name}.cls-meta.xml"])
            else:
                required.add(f"lwc/{name}/{name}.js-meta.xml")
    actual = set(files) - {"package.xml"}
    for path in actual:
        parts = PurePosixPath(path).parts
        allowed = any(
            (typ == "ApexClass" and len(parts) == 2 and parts[0] == "classes" and parts[1] in {f"{n}.cls" for n in names} | {f"{n}.cls-meta.xml" for n in names})
            or (typ == "LightningComponentBundle" and len(parts) >= 3 and parts[0] == "lwc" and parts[1] in names)
            for typ, names in manifest.items()
        )
        if not allowed:
            raise PolicyError("Package contains components outside manifest")
    if not required.issubset(actual):
        raise PolicyError("Required source file is absent")
    return actual

def compare(a, b, manifest):
    aa, bb = selected(a, manifest), selected(b, manifest)
    if aa != bb:
        return False, len(aa.symmetric_difference(bb))
    changed = sum(normalized(a[path], path) != normalized(b[path], path) for path in aa)
    return changed == 0, changed

def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["resolve", "compare"])
    p.add_argument("--target", default="")
    p.add_argument("--package", required=True)
    p.add_argument("--left", default="")
    p.add_argument("--right", default="")
    p.add_argument("--right-zip", action="store_true")
    p.add_argument("--label", default="")
    p.add_argument("--output-file", default="")
    a = p.parse_args()
    d = registry()
    info = pkg_info(d, a.package)
    manifest = members(info)
    if a.command == "resolve":
        t = target(d, a.target)
        if not a.output_file:
            raise PolicyError("No GitHub output file")
        with open(a.output_file, "a", encoding="utf8") as fp:
            for name, value in [("github_environment", t["github_environment"]), ("instance_url", t["instance_url"]), ("manifest", info["manifest"])]:
                fp.write(f"{name}={value}\n")
        print("SDOA_RESOLVE_OK: reviewed target and package")
        return 0
    if a.label not in ("candidate", "remote", "recheck"):
        raise PolicyError("Invalid compare label")
    same, diff = compare(from_dir(a.left), from_zip(a.right) if a.right_zip else from_dir(a.right), manifest)
    print(f"SDOA_{a.label.upper()}_COMPARE: equal={str(same).lower()} differences={diff}")
    return 0 if same else 4

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (PolicyError, OSError, ValueError, ET.ParseError, KeyError, TypeError):
        # Always fail closed; never print org payload, local paths or raw exceptions.
        print("::error title=SDOA_POLICY::Registry, package or metadata validation failed.")
        sys.exit(2)
