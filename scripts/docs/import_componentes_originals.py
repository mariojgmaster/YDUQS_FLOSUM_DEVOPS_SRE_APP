#!/usr/bin/env python3
"""Import the 14 original generated PNG assets into a checked-out repository.

Usage:
    python scripts/docs/import_componentes_originals.py /path/to/branch-monitor-componentes-14-originais.zip

The archive is supplied in the conversation. The importer never downloads files,
never executes them, checks SHA-256 and exact zip member names, and only writes
to docs/branch-monitor/componentes/originals/. It does not commit/push.
"""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "docs/branch-monitor/componentes/visual-manifest.json"
DEST = ROOT / "docs/branch-monitor/componentes/originals"

def main(archive_path: str) -> int:
    manifest = json.loads(CATALOG.read_text(encoding="utf-8"))
    assets = manifest["assets"]
    if len(assets) != 14 or len({a["original"] for a in assets}) != 14:
        raise ValueError("Expected exactly 14 distinct source assets.")
    if not Path(archive_path).is_file():
        raise FileNotFoundError("Source archive is absent.")
    with zipfile.ZipFile(archive_path) as zf:
        for item in assets:
            name = item["original"]
            if any(part in ("", ".", "..") for part in Path(name).parts) or "/" in name or "\\" in name:
                raise ValueError("Unsafe source name")
            member = "originais/" + name
            info = zf.getinfo(member)
            if info.file_size > 5 * 1024 * 1024:
                raise ValueError("Original image too large")
            raw = zf.read(member)
            if hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise ValueError("SHA256 mismatch for original " + item["id"])
            if not raw.startswith(bytes.fromhex("89504e470d0a1a0a")):
                raise ValueError("Not a PNG")
            target = (DEST / (item["id"] + ".png")).resolve()
            if DEST.resolve() not in target.parents:
                raise ValueError("Path outside originals")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            print(item["id"] + ": SHA-256 verified")
    print("SUCCESS: 14 original images imported. Review and git add/commit/push through normal PR controls.")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/docs/import_componentes_originals.py <archive.zip>")
    raise SystemExit(main(sys.argv[1]))
