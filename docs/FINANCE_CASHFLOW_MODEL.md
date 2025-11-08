# Finance Cashflow Model (v0)

Scope
- Read-only utilities that transform an estimate into a weekly cashflow time series.
- No servers, no external APIs; local inputs only.
- Two paths:
  1) Quick curve: naive linear S-curve over N weeks with retainage held and paid on the final week.
  2) Schedule-driven: allocate totals across tasks with start/end dates and optional weights; aggregated by ISO week start (Monday).

Inputs
- Estimate Lines CSV (aligned with benchmarking export):
  - Columns: project_id, trade, item, quantity, unit, unit_cost, line_total, source
  - If line_total is 0, it is recomputed as quantity*unit_cost (non-negative).
- Schedule JSON (schemas/schedule.schema.json, version "v0"):
  - tasks: [{ name, start, end, weight? }]
  - start/end: YYYY-MM-DD
  - weight: optional fractional share; if omitted, equal weights are assumed.

Outputs
- Weekly series (JSON):
  {
    "series": [
      {"week_start": "YYYY-MM-DD", "amount": 12345.67},
      ...
    ],
    "total": 123456.78
  }

Modules
- web/backend/cashflow.py
  - load_estimate_lines_csv(path) -> rows
  - quick_cashflow_from_estimate(rows, weeks=12, retainage_pct=0.1) -> series
    - Weights are a simple linear ramp across weeks (sum to 1).
    - Retainage holdback is added onto the final week.
  - cashflow_from_schedule(rows, schedule, retainage_pct=0.1) -> series
    - Build weekly buckets across all tasks (ISO-week start).
    - Task totals = total * (task weight) * (1 - retainage_pct).
    - Each task’s total is linearly distributed across its buckets.
    - Retainage is paid on the final week.

Assumptions & Notes
- Totals are computed as sum(line_total) across rows; fall back to quantity*unit_cost if needed.
- Weeks use ISO week start (Monday) for alignment across tasks.
- Weights are normalized (sum to 1). If any task weight is missing, equal weights are used.
- Retainage percent is clamped to [0,1] and applied as a final week payment.
- This is a v0 model for reporting and planning; it is not intended to handle change orders, progress billing, or advanced accruals.

Quick Start
- Generate a minimal schedule:
  pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/generate_schedule_from_estimate.ps1 -Out output/SCHEDULE_SAMPLE.json -Phases 2 -DurationDays 56

- Produce demo outputs (assemblies + cashflow):
  pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/demo_assemblies_and_cashflow.ps1

Artifacts
- output/ASSEMBLIES_SAMPLE.md    # line items derived from assemblies YAML + plan features
- output/CASHFLOW_SAMPLE.json     # weekly cashflow time series

Extensibility Ideas (Future)
- Non-linear S-curves (front/back-loaded), per-trade timing offsets.
- Milestone-based retainage release (partial releases prior to final).
- Integration with vendor quotes and committed costs.
- Phase-specific weights inferred from estimate composition or WBS mappings.
