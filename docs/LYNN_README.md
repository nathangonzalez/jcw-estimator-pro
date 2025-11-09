# Lynn v0 — Ingest & Baseline (DEV-FAST)

RAW first rule
- Always stage original files under data/lynn/raw first. Never modify or overwrite raw files.
- Derived artifacts are written under data/lynn/working.
- If an item becomes obsolete, move it into data/lynn/_archive (do not delete).

Directory layout
- data/lynn/
  - raw/
    - plans/                  # Uploaded plan PDFs (source of truth for plan features/takeoff)
    - vendor/                 # Any vendor files (quotes, emails, catalogs) placed here
    - other/                  # Any other raw material for the Lynn job
  - working/
    - registry.json           # Ingestion registry created by scripts/ingest_lynn.py
    - plan_features.json      # Extracted plan features (v0)
    - takeoff_quantities.json # M01 v0 quantities JSON (schema: schemas/trade_quantities.schema.json)
    - PIPELINE_ESTIMATE_RESPONSE.json # raw estimate response (policy + unit costs only)
    - estimate_lines.csv      # flattened line items for benchmarking and finance
    - gutcheck.json           # metrics() from benchmarking module (read-only)
  - _archive/                 # Obsolete or superseded files moved here (never delete)
  - vendor_rules.yaml         # Simple rules for classifying vendor/trade from filenames

Workflow (v0)
1) Ingestion
   - Place files under data/lynn/raw/*.
   - Run scripts/ingest_lynn.py to compute sha256 and classify (doc_type, vendor, trade).
   - Output: data/lynn/working/registry.json

2) Plan features + Takeoff
   - Place plan PDF(s) under data/lynn/raw/plans/.
   - Run scripts/lynn_takeoff_v0.py to produce plan features and M01 takeoff quantities.
   - Outputs:
     - data/lynn/working/plan_features.json
     - data/lynn/working/takeoff_quantities.json

3) RAW estimate (quote-free)
   - Run scripts/lynn_estimate_v0.py to price quantities (policy + unit costs only; ignore vendor CSVs).
   - Outputs:
     - data/lynn/working/PIPELINE_ESTIMATE_RESPONSE.json
     - data/lynn/working/estimate_lines.csv

4) Gut-check
   - Run scripts/lynn_gutcheck_v0.py to compute read-only metrics using the benchmarking module.
   - Outputs:
     - data/lynn/working/gutcheck.json
     - output/BENCH/LYNN_GUTCHECK.md (summary also uploaded by CI)

Guardrails
- Work only under data/lynn for all Lynn-related file operations.
- Do not delete; move non-used artifacts into data/lynn/_archive.
- Commit normally (no force-push). Suggested message for a complete pass:
  feat(lynn-v0): ingest registry + plan features + RAW estimate + gutcheck

Notes
- The read-only CI (Gut-Check) does not start servers or run the pipeline; it only reads existing artifacts.
- The pricing engine and takeoff modules are called locally; ensure any paths provided to scripts are valid on this machine.
