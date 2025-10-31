# UAT Smoke Test Execution Plan

## Target Endpoint
- **URL:** http://127.0.0.1:8000/v1/estimate
- **Method:** POST
- **Schema:** web/backend/schemas.py (EstimateRequest, EstimateResponse)

## Test Payload (Small, Valid)
Use the existing `scripts/smoke_estimate_v1.json` payload:
- area_sqft: 3200
- bedrooms: 4
- bathrooms: 3
- quality: "standard"
- complexity: 3

## Steps
1. Check if FastAPI is already running on port 8000
2. If not running, start: `uvicorn web.backend.app_comprehensive:app --host 127.0.0.1 --port 8000`
3. Wait for health check (/health endpoint)
4. Send single POST request to /v1/estimate
5. Validate response schema (total_cost, breakdown, confidence, etc.)
6. Stop the server (kill process)
7. Record result and duration

## Expected Success Criteria
- HTTP 200 response
- Valid response schema matching EstimateResponse
- Response time < 5 seconds

## Artifacts to Create
- output/SMOKE_ESTIMATE_RUN.json (raw API response)
- output/SMOKE_ESTIMATE_RUN.md (human summary)
- output/SMOKE_STDOUT.log (command output and errors)
