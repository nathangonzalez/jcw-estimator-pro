SINGLE CONTEXT WINDOW — R2 "Polymath Estimator" (DEV-FAST; supervised; no force push)

Repo: jcw-estimator-pro (master)
Goal: From a blueprint PDF, infer likely trades/items and rough quantities, estimate costs with quality/complexity/region, and auto-ask clarifying questions when confidence is low or scope is ambiguous. Return BOTH a collapsed (template) total and an exploded detail. Keep existing paths working (M01, legacy), but add a new "interactive" flow.

Guardrails:
- Only edit inside repo. Don't remove existing features. If a step fails, write an *_ERROR.md and continue safely.
- No force push.

# STEP 0 — Session receipt
- Append timestamp, branch, HEAD short SHA to output/R2_INTERACTIVE_RUN.md

# STEP 1 — Contracts (schemas)
- Add schemas/questions.schema.json
  - shape:
    version: "v0"
    project_id: string
    questions: [
      { id, trade?, item?, severity: "critical"|"normal"|"nice_to_have",
        rationale, prompt, suggested_answers?: [ {key,label} ] }
    ]
- Add schemas/assess_response.schema.json
  - { project_id, trades_inferred: [{trade, items:[{item, signals:[…], confidence:0..1}]}],
      questions_ref: "output/<…>/QUESTIONS.json", coverage_score:0..1, notes:[] }
- (Update schemas/estimate_response.schema.json only if needed: allow metadata.interactive with {coverage_score, questions_count, unresolved_count})

# STEP 2 — Engines (backend)
- Create web/backend/trade_inference.py
  - infer_trades(plan_features, rules_yaml=data/taxonomy/vendor_map.yaml, fixtures_rules=data/fixtures.rules.yaml?) →
    list of {trade, item, signals:[{type,value}], confidence}
  - Use: keywords in plan text (title block, sheets list), symbols/fixtures, room tags, typical residential defaults (concrete, framing, roofing, plumbing, electrical, HVAC, insulation, drywall, paint, flooring, millwork, windows/doors, landscaping, sitework).
  - Confidence blends: (#signals hit, sheet coverage, presence of quantities) normalized.
- Create web/backend/clarifier.py
  - make_questions(inferred, takeoff_quantities?, thresholds={confidence_min:0.55, missing_required_items:[…]}) →
    array of question objects (schema-conformant).
  - Examples:
    - "Roofing: shingle or metal?" with choices
    - "Foundation: slab-on-grade vs stem wall?"
    - "Window spec: vinyl vs aluminum?" etc.
  - Route critical where cost swing is high (roofing, windows/doors, slab type, exterior finish, cabinetry grade).
- Extend web/backend/features_builder.py (if needed) to include "complexity" and "quality" scalars per trade (simple mapping tables in code for now).
- Reuse pricing_engine.price_quantities; add hooks for "complexity/quality multipliers by trade", applied before markups/tax/escalation.

# STEP 3 — API wiring (new endpoints)
- web/backend/app_comprehensive.py:
  - POST /v1/plan/assess
    body: { project_id, pdf_path? or pdf_base64?, region?, quality?, complexity? }
    flow:
      a) load + plan_reader.extract_plan_features (existing)
      b) takeoff_engine.TakeoffEngine minimal pass for hints (counts may be partial)
      c) trade_inference.infer_trades → inferred list
      d) clarifier.make_questions → QUESTIONS (write to output/<project>/QUESTIONS.json)
      e) build assess_response (validate with jsonschema), write output/<project>/ASSESS_RESPONSE.json
  - POST /v1/estimate (interactive mode)
    - accept new shape: { mode:"interactive", project_id, region, quality?, complexity?, pdf_path? pdf_base64?, answers?:[{id, key|text}] }
    flow:
      a) If pdf present, run assess pipeline (or reuse cached ASSESS/TEMP) to gather inferred + quantities
      b) apply answers → resolve assumptions (e.g., roofing=metal toggles unit costs/assemblies)
      c) assemble quantities_v0 (fill missing items with heuristic quantities where possible; else zero with warning)
      d) price via pricing_engine with quality/complexity multipliers
      e) response metadata.interactive = {coverage_score, questions_count, unresolved_count, used_defaults:[…]}
      f) ALSO emit collapsed "template rollup" CSV for business templates:
         output/<project>/TEMPLATE_ROLLUP.csv with columns {trade, rolled_total}
      g) full exploded detail to output/<project>/ESTIMATE_LINES.csv

# STEP 4 — Data & defaults
- Add data/interactive/default_mappings.yaml
  - quality_map per trade: {economy:0.9, standard:1.0, premium:1.2}
  - complexity_map per trade: {simple:0.95, normal:1.0, complex:1.15}
  - default_missing_items: list of "must-ask" items if missing
  - roofing/materials, windows/door tiers, foundation types with cost deltas (percent multipliers)
- Ensure schemas/pricing_policy.v0.yaml remains source for markups/tax/escalation.

# STEP 5 — Scripts (operator UX)
- scripts/run_assess.ps1
  - params: -ProjectId, -PdfPath
  - calls /v1/plan/assess
  - writes summary to output/<project>/ASSESS_SUMMARY.md (trades inferred, coverage, question count)
- scripts/run_interactive_estimate.ps1
  - params: -ProjectId, -PdfPath, -Region, -Quality, -Complexity, -AnswersJsonPath?
  - calls /v1/estimate with mode=interactive
  - emits:
    - output/<project>/ESTIMATE_LINES.csv
    - output/<project>/TEMPLATE_ROLLUP.csv
    - output/<project>/INTERACTIVE_RECEIPT.md (coverage, unresolved, warnings)

# STEP 6 — UAT (Playwright)
- tests/e2e/uat.r2interactive.spec.ts
  - /health 200
  - POST /v1/plan/assess with sample plan → object with trades_inferred and questions
  - POST /v1/estimate (interactive with answers from QUESTIONS.json) → v0-shaped response; totals.grand_total > 0; metadata.interactive present
  - Verify TEMPLATE_ROLLUP.csv exists

# STEP 7 — Reporting
- docs/INTERACTIVE_ESTIMATOR.md
  - How questions are generated, how answers influence pricing, where artifacts live
- output/R2_INTERACTIVE_RECEIPT.md
  - record commit SHA, endpoints added, smoke summary, artifact paths

# STEP 8 — Commit & push
- Stage: new/changed schemas, backend modules, scripts, tests, docs, outputs touched
- Commit message:
  feat(r2-interactive): plan assessment, trade inference, questions, and interactive estimate (collapsed+exploded)
- Push HEAD (no tag for now)

ACCEPTANCE (write in R2_INTERACTIVE_RECEIPT.md):
- New endpoints: /v1/plan/assess (JSON validates), /v1/estimate interactive mode returns v0 + metadata.interactive
- Questions emitted: output/<project>/QUESTIONS.json; contains ≥3 critical questions on a house plan
- Rolled CSV: TEMPLATE_ROLLUP.csv exists and sums ≈ totals.grand_total (± rounding)
- Exploded CSV: ESTIMATE_LINES.csv present (≥ 10 lines)
- UAT spec passes (skip if sample PDF limited; then log PASS-SKIP with reason)
