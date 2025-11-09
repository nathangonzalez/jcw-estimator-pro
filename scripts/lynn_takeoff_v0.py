#!/usr/bin/env python3
"""
Lynn v0 — Plan Features + Takeoff (DEV-FAST)
- Finds first PDF under data/lynn/raw/plans/
- Extracts plan features (read-only)
- Generates M01 v0 takeoff quantities (no server)
Outputs:
- data/lynn/working/plan_features.json
- data/lynn/working/takeoff_quantities.json
Guardrails:
- Only touches data/lynn paths. No deletion.
"""
from __future__ import annotations

import os
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LYNN = REPO / "data" / "lynn"
RAW_PLANS = LYNN / "raw" / "plans"
WORKING = LYNN / "working"

def find_first_pdf() -> Path | None:
    if not RAW_PLANS.exists():
        return None
    for root, _, files in os.walk(RAW_PLANS):
        for fn in files:
            if fn.lower().endswith(".pdf"):
                return Path(root) / fn
    return None

def main() -> int:
    WORKING.mkdir(parents=True, exist_ok=True)

    pdf = find_first_pdf()
    if pdf is None:
        # Emit placeholders with explanation
        with open(WORKING / "plan_features.json", "w", encoding="utf-8") as f:
            json.dump({"error": "no_plan_pdf_found", "expected_dir": str(RAW_PLANS)}, f, indent=2)
        with open(WORKING / "takeoff_quantities.json", "w", encoding="utf-8") as f:
            json.dump({"error": "no_plan_pdf_found", "expected_dir": str(RAW_PLANS)}, f, indent=2)
        print("No PDF found in data/lynn/raw/plans. Wrote placeholder JSONs.")
        return 0

    # Import read-only helpers
    from web.backend.plan_reader import extract_plan_features
    from web.backend.takeoff_engine import TakeoffEngine

    # Plan features (best-effort)
    features = extract_plan_features(str(pdf))
    # Normalize & add project defaults
    features_out = {
        "project_id": features.get("project_id") or "LYNN-001",
        "project_type": features.get("project_type") or "SOD",
        "area_sqft": features.get("area_sqft") or 0.0,
        "fixtures": features.get("fixtures") or {},
        "sheets": features.get("sheets"),
        "scales": features.get("scales"),
        "source": {"pdf": str(pdf)},
    }
    with open(WORKING / "plan_features.json", "w", encoding="utf-8") as f:
        json.dump(features_out, f, indent=2)

    # Quantities v0 via TakeoffEngine (best-effort)
    eng = TakeoffEngine(max_pages=3)
    meta, pages, pages_text = eng.load_pdf(pdf_path=str(pdf))
    meta.project_id = "LYNN-001"
    scale = eng.detect_scale(pages_text)
    geom = eng.extract_geometry(pages)
    fixtures = eng.detect_fixtures(pages_text)
    quantities_v0 = eng.to_quantities(meta.project_id, meta, geom, fixtures, scale)

    with open(WORKING / "takeoff_quantities.json", "w", encoding="utf-8") as f:
        json.dump(quantities_v0, f, indent=2)

    print("Wrote plan_features.json and takeoff_quantities.json in data/lynn/working")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
