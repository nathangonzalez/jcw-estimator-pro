# Proposed Execution Plan (Guardrailed)

## Preconditions
- FastAPI app file: web/backend/app_comprehensive.py
- Endpoint: /v1/estimate

## Steps (Plan Only)
1) Create venv (if missing)
2) Install minimal deps
3) Launch FastAPI locally
4) Send a single POST to /v1/estimate
5) Shut down server

## Rollback & Cleanup
- Remove venv if created
- Kill any processes on port 8001

## Risk & Mitigation
- **Risk**: Server might not start or hang
- **Mitigation**: Timeout after 60 seconds, process kill
- **Risk**: Disk space usage
- **Mitigation**: Use temp directories
- **Risk**: Network conflicts
- **Mitigation**: Use non-standard port (8001)

## Files to Create
- scripts/proposed/smoke_estimate.ps1
- output/EXEC_RESULT.md (to be written after run)
