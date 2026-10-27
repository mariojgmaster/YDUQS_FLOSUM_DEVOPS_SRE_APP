#!/usr/bin/env python3
"""SDOA kit v2: explicit Metadata API manifests, proportional tests and safe reports.

No Salesforce authentication or write occurs here. Existing kit v1 stays intact.
"""
import argparse
import importlib.util
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, BadZipFile

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "config/salesforce-devops/catalog.json"
NS = "{http://soap.sforce.com/2006/04/metadata}"
TYPE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,99}$")
PACKAGE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,59}$")
MEMBER = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_ .:/-]{0,254}$")
TEST = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,119}$")
CODE_TYPES = frozenset({"ApexClass", "ApexTrigger", "Flow", "FlowDefinition",
                        "CustomObject", "CustomField", "ValidationRule",
                        "Workflow", "WorkflowRule"})
SENSITIVE_TYPES = frozenset({"Profile", "PermissionSet", "PermissionSetGroup",
    "ConnectedApp", "AuthProvider", "NamedCredential", "ExternalCredential",
    "RemoteSiteSetting", "SharingRules", "CustomApplication", "Network",
    "Certificate", "CustomSite", "ExperienceBundle", "TransactionSecurityPolicy"})
MAX_FILES = 1500
MAX_BYTES = 100_000_000
MAX_FILE = 15_000_000

class PolicyError(Exception):
    pass

def catalog():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    if data.get("schema") != 1 or not isinstance(data.get("packages"), dict):
        raise PolicyError("Invalid catalog")
    return data

def get_package(name):
    data = catalog()
    if not PACKAGE.fullmatch(name) or name not in data["packages"]:
        raise PolicyError("Unregistered package")
    info = data["packages"][name]
    if info.get("policy_version") != 2:
        raise PolicyError("Not a v2 reviewed package")
    if info.get("reviewed") is not True:
        raise PolicyError("v2 package must be reviewed in Git")
    path = info.get("manifest", "")
    if not re.fullmatch(r"manifest/[A-Za-z0-9_-]+\.xml", path):
        raise PolicyError("Manifest outside reviewed directory")
    types = info.get("allowed_types")
    if not isinstance(types, list) or not types or len(types) > 50 or len(types) != len(set(types)):
        raise PolicyError("Invalid type allowlist")
    if any(not isinstance(t, str) or not TYPE.fullmatch(t) for t in types):
        raise PolicyError("Invalid metadata type")
    if SENSITIVE_TYPES.intersection(types) and info.get("sensitive_change_reviewed") is not True:
        raise PolicyError("Sensitive metadata requires explicit Git-reviewed flag")
    tests = info.get("tests", [])
    if not isinstance(tests, list) or len(tests) > 100 or len(tests) != len(set(tests)):
        raise PolicyError("Invalid tests")
    if any(not isinstance(t, str) or not TEST.fullmatch(t) for t in tests):
        raise PolicyError("Invalid Apex test name")
    specified = info.get("test_level", "auto")
    if specified not in ("auto", "RunLocalTests", "RunSpecifiedTests", "NoTestRun"):
        raise PolicyError("Unapproved test level")
    if specified == "NoTestRun" and CODE_TYPES.intersection(types):
        raise PolicyError("Apex-impacting metadata cannot opt out of tests")
    if specified == "RunSpecifiedTests" and not tests:
        raise PolicyError("Specified Apex tests missing")
    if specified == "auto":
        level = "RunSpecifiedTests" if tests else ("RunLocalTests" if CODE_TYPES.intersection(types) else "NoTestRun")
    else:
        level = specified
    if level == "NoTestRun" and tests:
        raise PolicyError("Configured tests must be executed")
    if level != "RunSpecifiedTests" and tests:
        raise PolicyError("Test names are only valid with RunSpecifiedTests")
    info = dict(info, effective_test_level=level)
    return info

def manifest(path):
    if path.is_symlink() or not path.is_file():
        raise PolicyError("Missing or symlinked manifest")
    root = ET.parse(path).getroot()
    if root.tag != NS + "Package" or root.attrib:
        raise PolicyError("Invalid Metadata API Package")
    version = root.findtext(NS + "version")
    project = json.loads((ROOT / "sfdx-project.json").read_text(encoding="utf-8"))
    if version != project.get("sourceApiVersion"):
        raise PolicyError("Manifest API version differs from project")
    groups = root.findall(NS + "types")
    if not groups or len(groups) > 50:
        raise PolicyError("Missing or oversized metadata types")
    found = {}
    total = 0
    for group in groups:
        typ = group.findtext(NS + "name")
        names = [x.text for x in group.findall(NS + "members")]
        if not isinstance(typ, str) or not TYPE.fullmatch(typ) or typ in found:
            raise PolicyError("Invalid or repeated type")
        if not names or len(names) != len(set(names)):
            raise PolicyError("Missing or repeated members")
        for name in names:
            if not isinstance(name, str) or not MEMBER.fullmatch(name):
                raise PolicyError("Invalid, wildcard or dynamic member")
            if name.strip() != name or ".." in name or "//" in name or name.endswith("/"):
                raise PolicyError("Unsafe member path")
        found[typ] = sorted(names)
        total += len(names)
    if total > 600 or any(child.tag not in {NS + "types", NS + "version"} for child in root):
        raise PolicyError("Unreviewed manifest element or size")
    return found

def verify_config(package):
    info = get_package(package)
    names = manifest(ROOT / info["manifest"])
    if set(names) != set(info["allowed_types"]):
        raise PolicyError("Manifest does not match package type allowlist")
    return info, names

def safe_path(name):
    p = PurePosixPath(name)
    if not name or name.startswith("/") or "\\" in name or ".." in p.parts or "." in p.parts or name.endswith("/"):
        raise PolicyError("Unsafe Metadata API path")
    if p.name.lower().startswith("destructivechanges") or name in ("destructiveChanges.xml", "destructiveChangesPre.xml", "destructiveChangesPost.xml"):
        raise PolicyError("Destructive changes require distinct change control")
    if len(p.parts) > 15:
        raise PolicyError("Metadata path too deep")
    return name

def from_dir(root):
    if root.is_symlink() or not root.is_dir():
        raise PolicyError("Candidate directory invalid")
    out = {}
    for file in root.rglob("*"):
        if file.is_symlink():
            raise PolicyError("Symlink denied")
        if file.is_file():
            key = safe_path(file.relative_to(root).as_posix())
            if file.stat().st_size > MAX_FILE:
                raise PolicyError("Oversized component")
            out[key] = file.read_bytes()
    return checked(out)

def from_zip(path):
    try:
        with ZipFile(path) as z:
            files = [i for i in z.infolist() if not i.is_dir()]
            if len(files) > MAX_FILES or sum(i.file_size for i in files) > MAX_BYTES:
                raise PolicyError("ZIP package too large")
            for item in files:
                safe_path(item.filename)
                if ((item.external_attr >> 16) & 0o170000) == 0o120000:
                    raise PolicyError("ZIP symlink")
            roots = [PurePosixPath(i.filename).parts[:-1] for i in files if PurePosixPath(i.filename).name == "package.xml"]
            if len(roots) != 1:
                raise PolicyError("Missing or multiple package manifests")
            prefix = roots[0]
            out = {}
            for i in files:
                parts = PurePosixPath(i.filename).parts
                if parts[:len(prefix)] != prefix:
                    raise PolicyError("Unreviewed ZIP root")
                name = safe_path("/".join(parts[len(prefix):]))
                if name in out or i.file_size > MAX_FILE:
                    raise PolicyError("Duplicate or oversized metadata")
                out[name] = z.read(i)
            return checked(out)
    except BadZipFile as exc:
        raise PolicyError("Invalid Metadata API ZIP") from exc

def checked(files):
    if len(files) > MAX_FILES or sum(len(x) for x in files.values()) > MAX_BYTES:
        raise PolicyError("Metadata package exceeds limits")
    if "package.xml" not in files or len(files) < 2:
        raise PolicyError("Empty or manifest-less Metadata API package")
    for key in files:
        safe_path(key)
    return files

def payload_members(files):
    raw = files["package.xml"]
    if len(raw) > 100000:
        raise PolicyError("Unbounded package.xml")
    root = ET.fromstring(raw)
    if root.tag != NS + "Package":
        raise PolicyError("Invalid converted package.xml")
    result = {}
    for group in root.findall(NS + "types"):
        typ = group.findtext(NS + "name")
        if typ in result:
            raise PolicyError("Duplicate converted type")
        result[typ] = sorted(n.text for n in group.findall(NS + "members"))
    return result

def verify_payload(files, names):
    if payload_members(files) != names:
        raise PolicyError("Converted or remote payload has unapproved members")
    return True

def normalized(raw, path):
    data = raw.replace(b"\r\n", b"\n").rstrip(b"\n")
    if path.endswith(".xml"):
        root = ET.fromstring(data)
        def trim(el):
            if len(el) and el.text is not None and not el.text.strip():
                el.text = None
            if el.tail is not None and not el.tail.strip():
                el.tail = None
            for child in el:
                trim(child)
        trim(root)
        return ET.tostring(root, encoding="utf-8")
    return data

def report(operation, package, remote, candidate=None):
    _, members = verify_config(package)
    right = from_zip(Path(remote))
    verify_payload(right, members)
    result = {"schema": "SDOA-KIT-V2-SAFE/1", "operation": operation,
              "package_id": package, "component_count": sum(map(len, members.values())),
              "type_count": len(members), "modified_salesforce": False,
              "modified_git": False, "raw_metadata_included": False,
              "reviewed_types": sorted(members)}
    if operation == "retrieve":
        result.update(result="retrieved", differing_files=None)
    elif operation == "compare":
        if not candidate:
            raise PolicyError("Comparison requires candidate")
        left = from_dir(Path(candidate))
        verify_payload(left, members)
        keys = (set(left) | set(right)) - {"package.xml"}
        diff_count = sum(k not in left or k not in right or normalized(left[k], k) != normalized(right[k], k) for k in keys)
        result.update(result="equal" if diff_count == 0 else "different",
                      differing_files=diff_count)
    else:
        raise PolicyError("Unapproved read operation")
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=("resolve", "verify", "report", "test-level"))
    p.add_argument("--package", required=True)
    p.add_argument("--target")
    p.add_argument("--candidate-dir")
    p.add_argument("--remote-zip")
    p.add_argument("--operation", choices=("retrieve", "compare"))
    p.add_argument("--output-file")
    args = p.parse_args()
    try:
        if args.command == "resolve":
            data = catalog()
            info = data["packages"].get(args.package)
            if not isinstance(info, dict):
                raise PolicyError("Unknown package")
            if info.get("policy_version") != 2:
                subprocess.run([sys.executable, str(ROOT / "scripts/ci/sf-deploy-policy.py"),
                                "resolve", "--target", args.target or "", "--package", args.package,
                                "--output-file", args.output_file], cwd=ROOT, check=True)
                with Path(args.output_file).open("a", encoding="utf-8") as out:
                    out.write("policy_version=1\n")
                return
            info, _ = verify_config(args.package)
            # Reuse the existing target validator; v2 never grants production access.
            spec = importlib.util.spec_from_file_location("legacy_policy", ROOT / "scripts/ci/sf-deploy-policy.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            target = mod.target(mod.registry(), args.target)
            if not args.output_file:
                raise PolicyError("Missing output file")
            with Path(args.output_file).open("a", encoding="utf-8") as out:
                for key, value in (("github_environment", target["github_environment"]),
                                   ("instance_url", target["instance_url"]),
                                   ("manifest", info["manifest"]), ("policy_version", "2")):
                    out.write(f"{key}={value}\n")
            print("SDOA_V2_CATALOG_RESOLVED")
        elif args.command == "test-level":
            info, _ = verify_config(args.package)
            print(info["effective_test_level"])
            if info["effective_test_level"] == "RunSpecifiedTests":
                print(*info["tests"], sep="\n")
        elif args.command == "verify":
            _, names = verify_config(args.package)
            verify_payload(from_dir(Path(args.candidate_dir)), names)
            print("SDOA_V2_CANDIDATE_VERIFIED")
        elif args.command == "report":
            obj = report(args.operation, args.package, args.remote_zip, args.candidate_dir)
            Path(args.output_file).write_text(json.dumps(obj, ensure_ascii=True, indent=2), encoding="utf-8")
            print("SDOA_V2_SAFE_REPORT_READY")
    except (PolicyError, OSError, ValueError, ET.ParseError, KeyError, TypeError, subprocess.CalledProcessError):
        print("::error title=SDOA_V2_POLICY_DENIED::Manifest, target, tests or metadata package invalid.")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
