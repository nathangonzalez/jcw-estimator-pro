import json
from fastapi.testclient import TestClient

try:
    from web.backend.app_comprehensive import app
except Exception:
    from web.backend.app import app

def test_estimate_v1_contract():
    client = TestClient(app)

    # Load contract to validate required/optional shape
    with open("openapi/contracts/estimate.v1.contract.json", "r", encoding="utf-8") as f:
        contract = json.load(f)

    payload = {
        "area_sqft": 2500,
        "bedrooms": 3,
        "bathrooms": 2.5,
        "quality": "standard",
        "complexity": 3,
        "location_zip": "02139",
        "features": {"garage": True},
        "blueprint": {"scale": "1/8\"=1'-0\"", "sheet_name": "A1"}
    }

    res = client.post(contract["endpoint"], json=payload)
    assert res.status_code == 200, res.text
    data = res.json()

    # Minimal schema assertions (smoke-level)
    for k in contract["response"]["required"]:
        assert k in data, f"missing key in response: {k}"

    # Type sanity checks
    assert isinstance(data["total_cost"], (int, float))
    bd = data["breakdown"]
    for k in ["structure","finishes","systems","sitework","overhead_profit"]:
        assert k in bd and isinstance(bd[k], (int, float))
    assert 0 <= data["confidence"] <= 1
    assert isinstance(data["model_version"], str)
    assert isinstance(data["assumptions"], list)
