# Contract Check — /v1/estimate
- source_contract: openapi/contracts/estimate.v1.contract.json
- schema_module: web/backend/schemas.py
- findings: Schema quality field lacks enum restriction (contract requires ["standard", "premium", "lux"]), schema allows any string
- proposed_fix: Add quality enum validation to Pydantic model to match contract: quality: Literal["standard", "premium", "lux"] = "standard"
- action: open-PR
