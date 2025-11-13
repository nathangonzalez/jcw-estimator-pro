# Lynn Full-Test Requirements - R2

Auto-generated from UAT test failures.

**Total Requirements:** 6

## Estimate

### RQ-LYNN-002: Missing quantities.sample.json file

**Priority:** HIGH

**Given / When / Then:**
- **Given:** UAT test attempts to load quantities data
- **When:** Estimate API is called with sample data
- **Then:** quantities.sample.json file should exist and be loadable

**Acceptance Test:** UAT R2 - Estimate API (UAT R2 - Estimate API)

**Suggested Fix:** Create data/quantities.sample.json with valid takeoff quantities structure

---

### RQ-LYNN-004: Interactive estimate mode returns 500 error

**Priority:** HIGH

**Given / When / Then:**
- **Given:** Valid project parameters and mode=interactive
- **When:** POST /v1/estimate is called with interactive mode
- **Then:** Should return 200 with version and total_cost fields

**Acceptance Test:** UAT R2 Interactive - Estimate interactive mode (UAT R2 Interactive - Estimate interactive mode)

**Suggested Fix:** Implement interactive mode logic in estimate endpoint

---

### RQ-LYNN-005: Estimate endpoint not returning success response

**Priority:** HIGH

**Given / When / Then:**
- **Given:** Valid M01 quantities body is provided
- **When:** POST /v1/estimate is called
- **Then:** Should return successful response with v0-shaped cost data

**Acceptance Test:** POST /v1/estimate (M01 body) returns v0-shaped response (POST /v1/estimate (M01 body) returns v0-shaped response)

**Suggested Fix:** Fix estimate endpoint to handle M01 body format and return proper response

---


## Interactive

### RQ-LYNN-001: QnA endpoint not processing answers correctly

**Priority:** HIGH

**Given / When / Then:**
- **Given:** Valid answers array is provided to QnA endpoint
- **When:** POST /v1/interactive/qna is called with answers
- **Then:** Should process answers and return answered array with correct length

**Acceptance Test:** UAT Interactive - QnA endpoint processes answers (UAT Interactive - QnA endpoint processes answers)

**Suggested Fix:** Fix answer processing logic in QnA endpoint, ensure answered field is populated

---

### RQ-LYNN-003: Assess endpoint returns 500 error

**Priority:** HIGH

**Given / When / Then:**
- **Given:** Valid PDF path and project_id are provided
- **When:** POST /v1/interactive/assess is called
- **Then:** Should return 200 with trades_inferred and questions_ref

**Acceptance Test:** UAT R2 Interactive - Assess endpoint (UAT R2 Interactive - Assess endpoint)

**Suggested Fix:** Debug assess endpoint logic, check PDF processing and trade inference

---


## UI

### RQ-LYNN-006: UI upload interface not displaying correctly

**Priority:** MEDIUM

**Given / When / Then:**
- **Given:** User navigates to upload page
- **When:** Upload PDF Blueprint interface loads
- **Then:** Upload PDF Blueprint text should be visible

**Acceptance Test:** Upload to Takeoff to Estimate to Interactive (video) (Upload → Takeoff → Estimate → Interactive (video))

**Suggested Fix:** Fix UI upload interface, ensure proper element visibility and text content

---

