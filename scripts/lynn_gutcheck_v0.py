#!/usr/bin/env python3
"""
Lynn v0 — Gut-Check (read-only)
- Reads RAW estimate outputs under data/lynn/working
- Uses benchmarking module to generate reports
Emits:
- data/lynn/working/gutcheck.json
- output/BENCH/LYNN_GUTCHECK.md (via benchmarking.generate_reports)
Guardrails:
- Only touches data/lynn paths and output/BENCH artifacts. No deletion.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LYNN = REPO / "data" / "lynn"
WORKING = LYNN / "working"
BENCH_DIR = REPO / "output" / "BENCH"

def main() -> int:
    from web.backend import benchmarking

    WORKING.mkdir(parents=True, exist_ok=True)
    BENCH_DIR.mkdir(parents=True, exist_ok=True)

    estimate_csv = WORKING / "estimate_lines.csv"
    takeoff_json = WORKING / "takeoff_quantities.json"  # M01 v0, has version/meta/trades
    vendor_csv = None  # RAW quote-free baseline

    # Run generator (read-only)
    benchmarking.generate_reports(
        estimate_csv=str(estimate_csv),
        plan_json=str(takeoff_json),
        vendor_csv=str(vendor_csv) if vendor_csv else None,
        out_dir=str(BENCH_DIR),
        project_id_fallback="LYNN-001",
    )

    # Copy bench JSON into working/gutcheck.json for Lynn package
    bench_json = BENCH_DIR / "LYNN_GUTCHECK.json"
    gutcheck_json = WORKING / "gutcheck.json"
    if bench_json.exists():
        shutil.copyfile(bench_json, gutcheck_json)

    print("Gut-check complete: wrote data/lynn/working/gutcheck.json and output/BENCH/LYNN_GUTCHECK.{json,md}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
