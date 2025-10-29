import json
import os
from pathlib import Path

# REQUESTS_DIR = Path(".assistant/requests")
REQUESTS_DIR = Path("output/ASK_ASSISTANT")
OUT_DIR = Path(".assistant/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Hard caps to prevent accidental overloads

MAX_SINGLE_REQUEST_BYTES = 200_000 # ~200 KB per request file
MAX_BATCH_LINES = 200 # limit JSONL lines per batch
REQUIRED_APPROVAL_FLAG = True # must set "approved": true in each request

def _is_approved(payload):
    # Require explicit approval flag inside payload to run.
    return bool(payload.get("approved") is True)

def _validate_size(p: Path):
    size = p.stat().st_size
    if size > MAX_SINGLE_REQUEST_BYTES:
        raise ValueError(f"Request too large: {p} is {size} bytes (> {MAX_SINGLE_REQUEST_BYTES}).")

def _load_jsonline(line: str, n: int):
    try:
        return json.loads(line)
    except Exception as e:
        raise ValueError(f"Invalid JSON on line {n}: {e}") from e

def process_request_file(path: Path):
    _validate_size(path)
    if path.suffix.lower() == ".jsonl":
        # Validate JSONL batch
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > MAX_BATCH_LINES:
            raise ValueError(f"Batch too large: {len(lines)} lines (> {MAX_BATCH_LINES}).")
        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue
            payload = _load_jsonline(line, i)
            if not _is_approved(payload):
                raise PermissionError(f"Line {i} not approved (missing or false 'approved').")
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not _is_approved(payload):
            raise PermissionError("Request not approved (missing or false 'approved').")

def main():
    # This is intentionally a NO-OP processor for CI: validate only.
    results = []
    for p in sorted(REQUESTS_DIR.rglob("*")):
        if p.suffix.lower() not in {".json", ".jsonl"}:
            continue
        try:
            process_request_file(p)
            results.append({"file": str(p), "status": "validated"})
        except Exception as e:
            results.append({"file": str(p), "status": "failed", "error": str(e)})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUT_DIR / "gateway_validation_report.json"
    report_path.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
