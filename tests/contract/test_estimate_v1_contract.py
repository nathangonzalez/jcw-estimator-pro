# No execution in CI by default. This is a placeholder showing intent.
# When execution is approved, this will:
#  - POST legacy body and M01 body to /v1/estimate
#  - validate 200 response against estimate_response.schema.json
#
# SYNC-ONLY: Do not import FastAPI app or run TestClient here.

LEGACY_BODY = {"area_sqft": 2800, "quality": "standard", "complexity": "normal"}

from pathlib import Path
import json

M01_BODY = {
    "project_id": "LYNN-001",
    "region": "US-MA-Boston",
    "policy": "default.us-ma.boston.2025",
    "quantities": json.loads(Path("data/quantities.sample.json").read_text(encoding="utf-8"))
}

def test_contract_shapes_documented_only():
    # This is intentionally a non-executing placeholder to document the exact bodies.
    assert LEGACY_BODY["area_sqft"] == 2800
    assert M01_BODY["quantities"]["version"] == "v0"
