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
FOLDERS = {"ApexClass": "classes", "LightningComponentBundle": "lwc", "PermissionSet": "permissionsets"}
PERMISSIONSET_PACKAGE = "branch-monitor-reader-visibility"
PERMISSIONSET_MEMBER = "DevSreBranchMonitor_Reader"
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
    if "PermissionSet" in allowed and (package != PERMISSIONSET_PACKAGE or allowed != ["PermissionSet"]):
        raise PolicyError("Only reviewed Branch Monitor Reader permission change allowed")
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

def canonical_apex_class_core(root):
    """Canonicalize *only* the reviewed two-field ApexClass metadata schema.

    XML formatting, order and surrounding whitespace in known scalar fields
    are not metadata drift. Extra/unknown fields and attributes are not
    silently discarded: the caller falls back to strict XML comparison.
    """
    ns = "{http://soap.sforce.com/2006/04/metadata}"
    if (root.tag != f"{ns}ApexClass" or root.attrib or
            len(root) != 2 or (root.text or "").strip()):
        return None
    values = {}
    for child in root:
        if (child.tag not in (f"{ns}apiVersion", f"{ns}status") or
                child.tag in values or child.attrib or len(child) or
                (child.tail or "").strip()):
            return None
        values[child.tag] = (child.text or "").strip()
    if set(values) != {f"{ns}apiVersion", f"{ns}status"}:
        return None
    version, status = values[f"{ns}apiVersion"], values[f"{ns}status"]
    if (not re.fullmatch(r"[0-9]{1,3}\.[0-9]{1,2}", version) or
            status not in ("Active", "Inactive", "Deleted")):
        return None
    return f"ApexClass|apiVersion={version}|status={status}".encode("ascii")


def normalized(data, path):
    raw = data.replace(b"\r\n", b"\n").rstrip(b"\n")
    if path.endswith(".xml"):
        try:
            root = ET.fromstring(raw)
            if path.endswith(".cls-meta.xml"):
                canonical = canonical_apex_class_core(root)
                if canonical is not None:
                    return canonical
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
            elif typ == "LightningComponentBundle":
                required.add(f"lwc/{name}/{name}.js-meta.xml")
            elif typ == "PermissionSet":
                required.add(f"permissionsets/{name}.permissionset")
            else:
                raise PolicyError("Unsupported metadata type")
    for name in manifest.get("PermissionSet", []):
        # Exact member only. A broad permission set can grant unintended privileges.
        if name != PERMISSIONSET_MEMBER or manifest != {"PermissionSet": [PERMISSIONSET_MEMBER]}:
            raise PolicyError("PermissionSet member outside reviewed scope")
    actual = set(files) - {"package.xml"}
    for path in actual:
        parts = PurePosixPath(path).parts
        allowed = any(
            (typ == "ApexClass" and len(parts) == 2 and parts[0] == "classes" and parts[1] in {f"{n}.cls" for n in names} | {f"{n}.cls-meta.xml" for n in names})
            or (typ == "LightningComponentBundle" and len(parts) >= 3 and parts[0] == "lwc" and parts[1] in names)
            or (typ == "PermissionSet" and len(parts) == 2 and parts[0] == "permissionsets" and parts[1] in {f"{n}.permissionset" for n in names})
            for typ, names in manifest.items()
        )
        if not allowed:
            raise PolicyError("Package contains components outside manifest")
    if not required.issubset(actual):
        raise PolicyError("Required source file is absent")
    if "PermissionSet" in manifest:
        verify_reader_visibility_change(files[f"permissionsets/{PERMISSIONSET_MEMBER}.permissionset"])
    return actual


def verify_reader_visibility_change(raw):
    """Fail closed on unrelated classes, permissions or tab settings in the reviewed PS."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise PolicyError("Invalid Reader PermissionSet XML") from exc
    ns = "{http://soap.sforce.com/2006/04/metadata}"
    if root.tag != ns+"PermissionSet" or root.attrib:
        raise PolicyError("Invalid Reader PermissionSet schema")
    children = list(root)
    if len(children) != 3 or sorted(x.tag for x in children) != sorted([
            ns+"label", ns+"classAccesses", ns+"tabSettings"]):
        raise PolicyError("PermissionSet outside reviewed members")
    if root.findtext(ns+"label") != "DevOps SRE - Leitura Branch Monitor":
        raise PolicyError("Reader PermissionSet label drift")
    apex = root.find(ns+"classAccesses")
    tab = root.find(ns+"tabSettings")
    if apex is None or tab is None or len(apex) != 2 or len(tab) != 2:
        raise PolicyError("Reader PermissionSet privilege shape drift")
    if ({child.tag: child.text for child in apex} != {
           ns+"apexClass":"DevSreBranchMonitorController",ns+"enabled":"true"} or
        {child.tag: child.text for child in tab} != {
           ns+"tab":"branchMonitor",ns+"visibility":"Visible"}):
        raise PolicyError("Unexpected Reader permissions")
    if any(el.attrib or len(el) for el in children if el.tag != ns+"label"):
        # Nested scalar children must not contain additional privilege fields.
        if any(grand.attrib or len(grand) for parent in (apex,tab) for grand in parent):
            raise PolicyError("Unexpected nested permission settings")
    return True

def compare(a, b, manifest):
    aa, bb = selected(a, manifest), selected(b, manifest)
    if aa != bb:
        return False, len(aa.symmetric_difference(bb))
    changed = sum(normalized(a[path], path) != normalized(b[path], path) for path in aa)
    return changed == 0, changed


def mismatched_components(left, right, manifest):
    """Only return identifiers already disclosed by the reviewed package manifest.

    No org source, field values, hashes or arbitrary file paths enter public logs.
    """
    selected(left, manifest)
    selected(right, manifest)
    paths = set(left) | set(right)
    result = []
    for typ, names in manifest.items():
        for name in names:
            if typ == "ApexClass":
                own = {f"classes/{name}.cls", f"classes/{name}.cls-meta.xml"}
            elif typ == "LightningComponentBundle":
                own = {path for path in paths if path.startswith(f"lwc/{name}/")}
            elif typ == "PermissionSet":
                own = {f"permissionsets/{name}.permissionset"}
            else:
                raise PolicyError("Unsupported metadata type")
            if any(
                path not in left or path not in right or
                normalized(left[path], path) != normalized(right[path], path)
                for path in own
            ):
                result.append(f"{typ}:{name}")
    return sorted(result)

def mismatched_file_types(left, right, manifest):
    """Return only manifest allowlisted component names + generic file categories.

    Do not print retrieved code, metadata content, hashes, or file paths.
    """
    selected(left, manifest)
    selected(right, manifest)
    result = []
    for typ, names in manifest.items():
        for name in names:
            if typ == "ApexClass":
                candidates = (
                    ("source", f"classes/{name}.cls"),
                    ("metadata", f"classes/{name}.cls-meta.xml"),
                )
                for category, path in candidates:
                    if (path not in left or path not in right or
                            normalized(left[path], path) != normalized(right[path], path)):
                        result.append(f"ApexClass:{name}:{category}")
            elif typ == "LightningComponentBundle":
                prefix = f"lwc/{name}/"
                paths = {p for p in set(left) | set(right) if p.startswith(prefix)}
                if any(
                    p not in left or p not in right or
                    normalized(left[p], p) != normalized(right[p], p)
                    for p in paths
                ):
                    result.append(f"LightningComponentBundle:{name}:bundle")
            elif typ == "PermissionSet":
                path = f"permissionsets/{name}.permissionset"
                if (path not in left or path not in right or
                        normalized(left[path], path) != normalized(right[path], path)):
                    result.append(f"PermissionSet:{name}:metadata")
            else:
                raise PolicyError("Unsupported metadata type")
    return sorted(result)


def safe_apex_metadata_facts(raw):
    """Return only allowlisted, non-sensitive ApexClass configuration values."""
    root = ET.fromstring(raw.replace(b"\r\n", b"\n").strip())
    namespace = "http://soap.sforce.com/2006/04/metadata"
    if root.tag != f"{{{namespace}}}ApexClass":
        return "unknown", "unknown"
    version = root.findtext(f"{{{namespace}}}apiVersion") or ""
    status = root.findtext(f"{{{namespace}}}status") or ""
    if not re.fullmatch(r"[0-9]{1,3}\.[0-9]{1,2}", version):
        version = "unknown"
    if status not in ("Active", "Deleted", "Inactive"):
        status = "unknown"
    return version, status


def mismatched_apex_metadata_facts(left, right, manifest):
    """Return only reviewed ApexClass identifiers, API version and status."""
    selected(left, manifest)
    selected(right, manifest)
    results = []
    for name in manifest.get("ApexClass", []):
        path = f"classes/{name}.cls-meta.xml"
        if normalized(left[path], path) == normalized(right[path], path):
            continue
        baseline_api, baseline_status = safe_apex_metadata_facts(left[path])
        remote_api, remote_status = safe_apex_metadata_facts(right[path])
        results.append(
            f"ApexClass:{name}:baselineApi={baseline_api},remoteApi={remote_api},"
            f"baselineStatus={baseline_status},remoteStatus={remote_status}"
        )
    return sorted(results)


def differing_apex_metadata_shapes(left, right, manifest):
    """Report only core-only/extended XML shape, never source or field values."""
    selected(left, manifest)
    selected(right, manifest)
    rows = []
    for name in manifest.get("ApexClass", []):
        path = f"classes/{name}.cls-meta.xml"
        if normalized(left[path], path) == normalized(right[path], path):
            continue
        left_core = canonical_apex_class_core(ET.fromstring(left[path]))
        right_core = canonical_apex_class_core(ET.fromstring(right[path]))
        rows.append(
            f"ApexClass:{name}:baselineCoreOnly={str(left_core is not None).lower()},"
            f"remoteCoreOnly={str(right_core is not None).lower()}"
        )
    return sorted(rows)


def safe_apex_xml_shape(raw):
    """Bounded schema-only diagnostics. Never return XML text or element values."""
    root = ET.fromstring(raw.replace(b"\r\n", b"\n").strip())
    ns = "{http://soap.sforce.com/2006/04/metadata}"
    flags = []
    if root.tag != f"{ns}ApexClass":
        flags.append("nonstandardRoot")
    if root.attrib:
        flags.append("rootAttributes")
    if (root.text or "").strip():
        flags.append("rootText")
    core_counts = {"apiVersion": 0, "status": 0}
    packages = 0
    other_fields = 0
    attrs = False
    nested_core = False
    tail_text = False
    for child in root:
        if child.tag in (f"{ns}apiVersion", f"{ns}status"):
            core_counts[child.tag[len(ns):]] += 1
            if len(child):
                nested_core = True
        elif child.tag == f"{ns}packageVersions":
            packages += 1
        else:
            other_fields += 1
        attrs = attrs or bool(child.attrib)
        tail_text = tail_text or bool((child.tail or "").strip())
    if packages:
        # Safe counts only; never output managed-package namespaces or versions.
        flags.append(f"packageVersionsCount={min(packages, 100)}")
    if other_fields:
        flags.append(f"otherChildCount={min(other_fields, 100)}")
    if core_counts != {"apiVersion": 1, "status": 1}:
        flags.append("missingOrDuplicateCore")
    if attrs:
        flags.append("childAttributes")
    if nested_core:
        flags.append("nestedCore")
    if tail_text:
        flags.append("trailingText")
    if canonical_apex_class_core(root) is None and not flags:
        flags.append("nonCanonicalCore")
    return ",".join(flags) if flags else "coreOnly"


def differing_apex_metadata_structure(left, right, manifest):
    """Expose only approved member identifiers and bounded XML shape categories."""
    selected(left, manifest)
    selected(right, manifest)
    parts = []
    for name in manifest.get("ApexClass", []):
        path = f"classes/{name}.cls-meta.xml"
        if normalized(left[path], path) == normalized(right[path], path):
            continue
        parts.append(
            f"ApexClass:{name}:baseline={safe_apex_xml_shape(left[path])},"
            f"remote={safe_apex_xml_shape(right[path])}"
        )
    return sorted(parts)


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
    left = from_dir(a.left)
    right = from_zip(a.right) if a.right_zip else from_dir(a.right)
    same, diff = compare(left, right, manifest)
    print(f"SDOA_{a.label.upper()}_COMPARE: equal={str(same).lower()} differences={diff}")
    if not same and a.label in ("remote", "recheck"):
        # Only reviewed manifest member identifiers are emitted.
        names = mismatched_components(left, right, manifest)
        print(f"SDOA_{a.label.upper()}_DIFFERING_MEMBERS: {','.join(names)}")
        kinds = mismatched_file_types(left, right, manifest)
        print(f"SDOA_{a.label.upper()}_DIFFERING_PARTS: {','.join(kinds)}")
        facts = mismatched_apex_metadata_facts(left, right, manifest)
        if facts:
            print(f"SDOA_{a.label.upper()}_APEX_META_FACTS: {';'.join(facts)}")
            shapes = differing_apex_metadata_shapes(left, right, manifest)
            print(f"SDOA_{a.label.upper()}_APEX_META_SHAPES: {';'.join(shapes)}")
            structure = differing_apex_metadata_structure(left, right, manifest)
            print(f"SDOA_{a.label.upper()}_APEX_META_STRUCTURE: {';'.join(structure)}")
    return 0 if same else 4

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (PolicyError, OSError, ValueError, ET.ParseError, KeyError, TypeError):
        # Always fail closed; never print org payload, local paths or raw exceptions.
        print("::error title=SDOA_POLICY::Registry, package or metadata validation failed.")
        sys.exit(2)
