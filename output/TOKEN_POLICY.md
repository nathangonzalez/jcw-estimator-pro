High-Token Session Policy (SYNC-ONLY)
======================================

Generated: 2025-11-05
Mode: SYNC_ONLY
Purpose: Document what was read, how it was summarized, and compression/trimming choices to avoid context overflow.

Read Targets (Prioritized)
1) Contracts/Schemas
   - schemas/trade_quantities.schema.json (authoritative v0 quantities schema)
   - schemas/estimate_response.schema.json (authoritative v0 response schema)
   - schemas/pricing_policy.v0.yaml (regional defaults and markups)
   - openapi/contracts/estimate.v1.contract.json (dual-shape request; v0 response ref)
2) Entrypoints
   - web/backend/app_comprehensive.py (/v1/estimate dual-shape stub and warning)
   - web/backend/schemas.py (Legacy+M01 request shims; v0 response models)
3) Data/Tests/Scripts/Docs/Status
   - data/quantities.sample.json (conformant v0 M01 sample)
   - tests/contract/test_estimate_v1_contract.py (no-run shapes placeholder)
   - scripts/audit_m01.ps1 (read-only audit generator; no execution performed)
   - docs/JCW_SUITE_BIGPICTURE.md (living big-picture)
   - output/* status files (AGENT_SYNC, CLINE_STATUS, M01_ENV, M01_STATUS)

Compression & Trimming Strategy
- Focused summarization (2–3 lines per file) captured in output/CTX_SUMMARY.md.
- Consolidated path/role index captured in output/CTX_INDEX.json; size/hash placeholders only (no execution).
- Avoided embedding large raw sources in chat; will store any future raw extracts in /output/_sources/** if required.
- Omitted heavy logs, binary assets, and external reports from chat context.
- Deferred any dynamic hashing or parsing to scripts/audit_m01.ps1 (to be executed only with explicit approval).

Token Budget Discipline
- Targets were summarized, not inlined, to keep within ≤ ~1.5k tokens chat guidance.
- Cross-file deltas captured as bullets in CTX_SUMMARY; deep details remain in repository files themselves.

Planned Artifacts (SYNC-ONLY)
- output/CTX_INDEX.json  — index of key files (size/hash placeholders)
- output/CTX_SUMMARY.md — structured session summary
- output/TOKEN_POLICY.md — this policy
- prompts/MAXI_SUPERPROMPT.md — operating constraints and steps for high-token sessions
- scripts/high_context_session.ply — session plan for collection, summary, and proposed commit

Execution Gates (Do Not Run)
- Do not execute servers, installs, network, or audit scripts unless explicitly approved (“Approved: Execute”).
- Do not push commits without “Approved: Push”.
- Proposed commit (pending approval):
  - message: chore(context): add high-token session index, summary, and plan (sync-only)
  - staged: prompts/MAXI_SUPERPROMPT.md, scripts/high_context_session.ply, output/CTX_INDEX.json, output/CTX_SUMMARY.md, output/TOKEN_POLICY.md

Next Steps (Pending Approval)
- Optionally run scripts/audit_m01.ps1 to compute actual SHA-256 and JSON/YAML validation and emit:
  - output/M01_AUDIT.md, output/M01_STATUS.json
- Add policy loader and response composition utilities behind execution gate in a future module step.
