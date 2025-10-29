import json, os, datetime, sys
inp = "output/ESTIMATE_V1_SMOKE_RESULT.json"
out_json = "output/CLINE_RUNCHECK.json"
out_md = "output/CLINE_RUNCHECK.md"
now = datetime.datetime.utcnow().isoformat() + "Z"
ok = False
resp_obj = {}
if os.path.exists(inp):
    with open(inp, "r", encoding="utf-8") as f:
        try:
            resp_obj = json.load(f)
            # Heuristic: consider success if a numeric total or estimate-like field exists
            candidate_keys = ["total_cost", "estimate", "predicted_cost"]
            ok = any(k in resp_obj for k in candidate_keys)
        except Exception:
            pass
summ = {
    "timestamp": now,
    "endpoint": "/v1/estimate",
    "input_file": "scripts/smoke_estimate_v1.json",
    "output_file": "output/ESTIMATE_V1_SMOKE_RESULT.json",
    "keys_present": sorted(list(resp_obj.keys())) if isinstance(resp_obj, dict) else ["non-dict-response"],
    "status": "pass" if ok else "fail",
    "notes": "Heuristic status based on presence of estimate-like keys."
}
os.makedirs("output", exist_ok=True)
with open(out_json, "w", encoding="utf-8") as f: json.dump(summ, f, indent=2)
with open(out_md, "w", encoding="utf-8") as f:
    f.write("# CLINE Run Check — /v1/estimate\n\n")
    f.write(f"- Timestamp (UTC): {now}\n")
    f.write("- Endpoint: /v1/estimate (http://127.0.0.1:8000)\n")
    f.write("- Input: scripts/smoke_estimate_v1.json\n")
    f.write("- Output: output/ESTIMATE_V1_SMOKE_RESULT.json\n")
    f.write(f"- Status: {'PASS' if ok else 'FAIL'}\n")
    excerpt = json.dumps(resp_obj, indent=2)[:1200]
    f.write("\n## Response Excerpt\n\n```json\n" + excerpt + "\n```\n")
