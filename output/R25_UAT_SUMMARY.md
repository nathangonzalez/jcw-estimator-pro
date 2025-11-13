# R2.5 Lynn Full-Test UAT Summary

**Test Results:** 14 passed, 6 failed, 1 skipped (66.7% pass rate)

## Passed Tests (14)
- UAT Interactive - Health check
- UAT R2 - Health check
- API happy paths › GET /health returns 200 and minimal body
- UAT Interactive - Assess endpoint with PDF
- UAT Interactive - Assess validation errors
- UAT Interactive - Assess endpoint happy-path with request_id
- API happy paths › POST /v1/takeoff returns v0-like quantities
- Takeoff output passes into estimate
- UAT Interactive - QnA endpoint with empty questions returns 422
- UAT Interactive - QnA endpoint with well-formed payload returns 200
- UAT Interactive - QnA validation errors
- UAT Interactive - Question generation determinism
- UAT Interactive - Files cleanup
- UAT R2 - Files exist

## Failed Tests (6)

### 1. UAT Interactive - QnA endpoint processes answers
**Error:** expect(received).toHaveLength(expected) Expected length: 2 Received length: 0
**Area:** Interactive
**Issue:** QnA endpoint not processing answers correctly

### 2. UAT R2 - Estimate API
**Error:** Cannot find module '../../../data/quantities.sample.json'
**Area:** Estimate
**Issue:** Missing quantities.sample.json file

### 3. UAT R2 Interactive - Assess endpoint
**Error:** Expected: 200 Received: 500
**Area:** Interactive
**Issue:** Assess endpoint returning 500 error

### 4. UAT R2 Interactive - Estimate interactive mode
**Error:** Expected: 200 Received: 500
**Area:** Estimate
**Issue:** Interactive estimate mode returning 500 error

### 5. POST /v1/estimate (M01 body) returns v0-shaped response
**Error:** expect(received).toBeTruthy() Received: false
**Area:** Estimate
**Issue:** Estimate endpoint not returning success response

### 6. Upload → Takeoff → Estimate → Interactive (video)
**Error:** expect(locator).toBeVisible() failed - Upload PDF Blueprint for AI Analysis
**Area:** UI
**Issue:** UI upload interface not displaying correctly

## Skipped Tests (1)
- Estimator smoke (supervised scaffold) › loads UI frame

## Recommendations
1. Fix missing quantities.sample.json file
2. Debug 500 errors in assess and estimate endpoints
3. Fix QnA answer processing logic
4. Update UI upload interface for proper element visibility
5. Re-run tests after fixes to validate improvements
