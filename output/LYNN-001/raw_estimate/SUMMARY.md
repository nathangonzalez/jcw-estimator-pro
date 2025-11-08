# LYNN-001 — Raw Estimate Summary (no re-run)

Generated from existing artifacts only:
- output/TAKEOFF_RESPONSE.json
- output/PIPELINE_ESTIMATE_RESPONSE.json

Header
- project_id: LYNN-001
- run_timestamp: 2025-11-08T14:16:30-05:00
- input_digests:
  - quantities_json_sha256: e634eae29fa001e6891ebf30001454aea8b6ce28211629fc2f79b5921d3f4b13
  - policy_yaml_sha256: 67cac549e56a3c850ed36aece17fd68f172d34058d69de8488e501d5a3c8d205
  - unit_costs_csv_sha256: f1c200dcf7f0b5616b3c1b0b16b8cb823708d309a19c2a734263ff7baf0957d9

Subtotals by trade (descending)
- concrete: 0.00
- framing: 0.00
- plumbing: 0.00

Top 10 line items by cost
1) trade=concrete code=slab_area desc="Slab area (heuristic)" qty=3600 unit=SF unit_cost=0.00 total=0.00 source=policy_defaults
2) trade=framing code=wall_linear desc="Wall linear (heuristic)" qty=900 unit=LF unit_cost=0.00 total=0.00 source=policy_defaults
3) trade=plumbing code=fixtures desc="Fixture count (keyword scan)" qty=17 unit=EA unit_cost=0.00 total=0.00 source=policy_defaults
4) trade=plumbing code=toilet desc="Fixture (rule match)" qty=1 unit=EA unit_cost=0.00 total=0.00 source=policy_defaults
5) trade=plumbing code=lavatory_sink desc="Fixture (rule match)" qty=1 unit=EA unit_cost=0.00 total=0.00 source=policy_defaults
6) trade=plumbing code=shower desc="Fixture (rule match)" qty=1 unit=EA unit_cost=0.00 total=0.00 source=policy_defaults
7) trade=plumbing code=bathtub desc="Fixture (rule match)" qty=1 unit=EA unit_cost=0.00 total=0.00 source=policy_defaults
8) trade=plumbing code=hose_bibb desc="Fixture (rule match)" qty=1 unit=EA unit_cost=0.00 total=0.00 source=policy_defaults
9) trade=plumbing code=floor_drain desc="Fixture (rule match)" qty=1 unit=EA unit_cost=0.00 total=0.00 source=policy_defaults

Notes (warnings)
- Missing cost for concrete/slab_area; defaulted to 0.0
- Missing cost for framing/wall_linear; defaulted to 0.0
- Missing cost for plumbing/fixtures; defaulted to 0.0
- Missing cost for plumbing/toilet; defaulted to 0.0
- Missing cost for plumbing/lavatory_sink; defaulted to 0.0
- Missing cost for plumbing/shower; defaulted to 0.0
- Missing cost for plumbing/bathtub; defaulted to 0.0
- Missing cost for plumbing/hose_bibb; defaulted to 0.0
- Missing cost for plumbing/floor_drain; defaulted to 0.0
- using_m01_request_shape

Provenance
- CSV exported: output/LYNN-001/raw_estimate/estimate_lines.csv
- Built without re-running the pipeline; no external calls or installs.
