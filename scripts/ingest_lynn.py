#!/usr/bin/env python3
"""
Lynn v0 - Ingestion registry (DEV-FAST)
- Walk data/lynn/raw/*
- Compute sha256 and basic file facts
- Classify (doc_type, vendor, trade) using data/lynn/vendor_rules.yaml
- Emit data/lynn/working/registry.json
Guardrails: Only touches data/lynn; never deletes.
"""
from __future__ import annotations

import os
import re
import sys
import json
import hashlib
import datetime as dt
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import yaml  # pyyaml
except Exception:
    yaml = None  # best-effort; will run without rules if not available

REPO_ROOT = Path(__file__).resolve().parents[1]
LYNN_ROOT = REPO_ROOT / "data" / "lynn"
RAW_ROOT = LYNN_ROOT / "raw"
WORKING_ROOT = LYNN_ROOT / "working"
RULES_PATH = LYNN_ROOT / "vendor_rules.yaml"
REGISTRY_PATH = WORKING_ROOT / "registry.json"

def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _load_rules() -> Dict[str, Any]:
    rules: Dict[str, Any] = {"rules": [], "defaults": {"doc_type_by_ext": {}}}
    if yaml is None or not RULES_PATH.exists():
        return rules
    try:
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if isinstance(data, dict):
                rules.update(data)
    except Exception:
        pass
    return rules

def _classify(path: Path, rules: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Classify using simple regex 'match' over filename or any parent dir segment (case-insensitive).
    Fallback doc_type by extension via defaults.doc_type_by_ext.
    """
    text = str(path).lower()
    vendor = None
    trade = None
    doc_type = None

    # Extension -> doc_type map
    ext_map = (rules.get("defaults") or {}).get("doc_type_by_ext") or {}
    doc_type = ext_map.get(path.suffix.lower())

    # Regex rules
    for r in (rules.get("rules") or []):
        pat = (r.get("match") or "").strip()
        if not pat:
            continue
        try:
            if re.search(pat, text, flags=re.IGNORECASE):
                vendor = vendor or r.get("vendor")
                trade = trade or r.get("trade")
                doc_type = doc_type or r.get("doc_type")
        except re.error:
            # treat as a literal contains if regex fails to compile
            if pat.lower() in text:
                vendor = vendor or r.get("vendor")
                trade = trade or r.get("trade")
                doc_type = doc_type or r.get("doc_type")

    return {"vendor": vendor, "trade": trade, "doc_type": doc_type or "file"}

def main() -> int:
    # Ensure roots
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    WORKING_ROOT.mkdir(parents=True, exist_ok=True)

    rules = _load_rules()

    files: List[Dict[str, Any]] = []
    for root, dirs, filenames in os.walk(RAW_ROOT):
        for fn in filenames:
            p = Path(root) / fn
            # Ignore placeholders like .gitkeep
            if fn.lower() == ".gitkeep":
                continue
            try:
                stat = p.stat()
                entry: Dict[str, Any] = {}
                rel = p.relative_to(RAW_ROOT)
                entry["path"] = str(rel).replace("\\", "/")
                entry["bytes"] = int(stat.st_size)
                entry["ext"] = p.suffix.lower()
                entry["sha256"] = _sha256_file(p)
                entry["mtime"] = dt.datetime.fromtimestamp(stat.st_mtime).isoformat()
                entry["ctime"] = dt.datetime.fromtimestamp(stat.st_ctime).isoformat()
                entry.update(_classify(p, rules))
                files.append(entry)
            except Exception as e:
                files.append({
                    "path": str(p).replace("\\", "/"),
                    "error": str(e)
                })

    registry = {
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "root": str(RAW_ROOT.relative_to(REPO_ROOT)).replace("\\", "/"),
        "count": len(files),
        "files": files,
    }

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

    print(f"Wrote {REGISTRY_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
