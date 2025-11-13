# R2.5 Lynn Full-Test Inputs Check

## Missing Files

### Lynn Plan PDF
**Expected:** `data/lynn/raw/plans/LYNN.pdf`
**Status:** MISSING
**Action Required:** Place the Lynn construction plan PDF at the expected location.

## Available Files

### Schemas
- ✅ `schemas/trade_quantities.schema.json` - Present
- ✅ `schemas/questions.schema.json` - Present
- ✅ `schemas/assess_response.schema.json` - Present
- ✅ `schemas/estimate_response.schema.json` - Present

### Environment Setup
- API_URL: http://127.0.0.1:8001
- UI_URL: http://127.0.0.1:8001
- TAKEOFF_ENABLE_LAYOUT: true

## Next Steps
1. Obtain Lynn construction plan PDF
2. Place at `data/lynn/raw/plans/LYNN.pdf`
3. Re-run this check
