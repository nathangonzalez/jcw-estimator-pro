# UAT Training Notes — Vendor Quotes (LYNN)

**Goal:** Use real vendor quotes as ground truth to calibrate pricing.

## Workflow (LYNN)
1. Generate Best Guess with `/v1/estimate` using M01 body.
2. Extract vendor quote line items from PDFs → normalized JSON rows.
3. Run variance report to compare Best Guess vs Vendor by trade/item.
4. Record deltas & rationales; update pricing policy or unit costs as needed.
5. Append findings here (human notes) + store machine-readable artifacts.

## Data conventions
- Raw vendor PDFs: `data/vendor_quotes/LYNN-001/<vendor>/raw/<filename>.pdf`
- Parsed JSON: `data/vendor_quotes/LYNN-001/<vendor>/parsed/<filename>.json`
- Normalized CSV (canonical columns): `data/vendor_quotes/LYNN-001/<vendor>/normalized/<filename>.csv`
- Aggregated canonical quotes: `data/vendor_quotes/LYNN-001/quotes.canonical.csv`
- Comparison outputs: `output/LYNN-001/compare/`

## Canonical columns
- `vendor, trade, item, description, unit, qty, unit_cost, line_total, notes`

## Open questions to track
- How each vendor groups scopes (e.g., “rough + finish” vs. split).
- Tax, mobilization, alternates & exclusions representation.
- Units consistency (LF, SF, EA) and conversion assumptions.
- Title/section signal patterns we can auto-detect.
