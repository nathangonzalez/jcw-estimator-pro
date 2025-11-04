JCW Suite — Big Picture (Living Document)
==========================================

Vision
- Integrated Estimating ↔ Contracts ↔ Finance ↔ Plan Reading ↔ 3D ↔ PM.
- Single source of truth across project lifecycle, with audit trails and versioned APIs.
- AI-augmented workflows that remain supervisor-controlled, deterministic when needed.

Data Sources
- QuickBooks: chart of accounts, invoices, vendor bills, payments, GL.
- Bank statements: cash flow, reconciliations, spend categorization.
- Vendor quotes: scoped pricing, inclusions/exclusions, validity windows.
- Crawled catalogs: commodity prices (lumber, concrete, fixtures), region/time indexed.
- PDFs: plans, specs, submittals, RFIs, change orders.
- Google Workspace: docs, sheets, drive folders; collaboration artifacts and approvals.

Core Services
- Estimating: quantities → pricing → markups → totals, with regional/time adjustments.
- Plan Reading: AI takeoff, scale detection, geometry summaries, cross-sheet references.
- Finance: job cost tracking, WIP, billing schedules, cash flow projections.
- Admin Assistant: intake, scheduling, approvals, vendor onboarding, correspondence.
- 3D: model ingestion, quantity extraction, clash/tolerance awareness.
- Project Mgmt: tasks, RFIs, submittals, changes, document control, audit-ready exports.

Shared Contracts
- Global IDs: project_id, request_id, vendor_id, quote_id, policy_id, artifact_id.
- Project lifecycle states: intake → estimating → contracting → execution → closeout.
- Audit trails: every derived artifact includes inputs_digest (hash), timestamps, actor.
- Evidence retention: saved source references (plan sheets, quotes, CSVs), redaction lanes.

Versioning
- API v1 (stable): long-lived, additive-compatible changes only, deprecations with warnings.
- vNext staging: feature flags and beta endpoints; promotes to v1 when stabilized.
- Schema semver: v0 for internal trials, v1+ for external-facing contracts.

Security and PII Lanes
- PII lanes: strict separation of personal info from estimating artifacts.
- Data minimization: only retain required fields; redact on export when possible.
- Artifact retention: default 18 months for derived estimates; raw uploads per policy.
- Access controls: per-project, per-role; vendor-only views for quotes.
- Cryptographic digests: inputs_digest embedded for trace/trust; chain-of-custody logs.

Roadmap (M01–M06)
- M01 — Estimating Foundations (Quantities ↔ Pricing v0)
  - Authoritative schemas (v0), dual-shape /v1/estimate, pricing policy seed.
  - Status: In progress (sync-only; no execution).
- M02 — CSV/Vendor Ingestion + Policy Engine v1
  - Unit costs CSV, vendor quotes blending, soft/contingency rules hardened.
  - Status: Planned.
- M03 — Plan Reading v1
  - Scale parse, geometry summaries, AI-assisted takeoff deltas.
  - Status: Planned.
- M04 — Contracts & Finance v1
  - Contract templates, COs, QuickBooks sync, bank reconcile hooks.
  - Status: Planned.
- M05 — 3D & BIM Hooks
  - 3D model import, quantities cross-check, clash-driven estimates.
  - Status: Planned.
- M06 — PM Integration
  - Tasks, RFIs, submittals, approvals; audit-quality exports.
  - Status: Planned.

Notes
- This document is a living spec; keep aligned with schemas under /schemas and OpenAPI under /openapi.
- Security and governance reviews occur before promoting vNext features into API v1.
