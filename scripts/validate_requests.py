"""
Offline validator for .assistant/requests.
This is NOT executed by CI in this sync-only step.
"""
from pathlib import Path
import json

REQ_DIR = Path(".assistant/requests")

def validate_file(p: Path):
    if p.suffix.lower() == ".jsonl":
        lines = p.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except Exception as e:
                raise ValueError(f"{p} line {i} invalid JSON: {e}")
            if payload.get("approved") is not True:
                raise ValueError(f"{p} line {i} missing approved flag.")
    else:
        payload = json.loads(p.read_text(encoding="utf-8"))
        if payload.get("approved") is not True:
            raise ValueError(f"{p} missing approved flag.")

def main():
    for p in sorted(REQ_DIR.rglob("*")):
        if p.suffix.lower() not in {".json", ".jsonl"}:
            continue
        validate_file(p)

if __name__ == "__main__":
    main()
