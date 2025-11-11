# UAT Annotated Results

## Timestamp
2025-11-11T13:47:17-05:00

## Summary
- Total tests: 10
- Passed: 6
- Failed: 3
- Skipped: 1

## Passed Tests
- GET /health returns 200
- POST /v1/estimate (M01 body) returns v0-shaped response
- POST /v1/takeoff returns v0-like quantities
- Takeoff output passes into estimate
- UAT R2 - Health check
- UAT R2 - Files exist

## Failed Tests
- UAT R2 - Estimate API: Cannot find module '../../../data/quantities.sample.json'
- UAT R2 Interactive - Assess endpoint: Status 500 (API not running)
- UAT R2 Interactive - Estimate interactive mode: Status 500 (API not running)

## Notes
- API not running during test execution
- Interactive endpoints implemented but require API to test fully
- File existence checks passed
