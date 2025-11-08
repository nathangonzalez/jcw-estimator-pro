# Scheduling Templates (v0)

This note describes the minimal schedule format used for read-only cashflow allocation.

Schema
- File: schemas/schedule.schema.json
- Version: v0
- Shape:
  - version: "v0"
  - tasks: array of tasks
    - name: string
    - start: date YYYY-MM-DD
    - end: date YYYY-MM-DD
    - weight: number (optional), relative fraction. If omitted, equal weights are assumed across tasks.

Example (2-phase, equal weights)
{
  "version": "v0",
  "tasks": [
    { "name": "Phase A", "start": "2025-01-01", "end": "2025-01-21" },
    { "name": "Phase B", "start": "2025-01-22", "end": "2025-02-25" }
  ]
}

Example (3-phase, explicit weights)
{
  "version": "v0",
  "tasks": [
    { "name": "Foundation", "start": "2025-01-01", "end": "2025-01-14", "weight": 0.25 },
    { "name": "Structure",  "start": "2025-01-15", "end": "2025-02-20", "weight": 0.50 },
    { "name": "Finish",     "start": "2025-02-21", "end": "2025-03-10", "weight": 0.25 }
  ]
}

Notes
- Weeks are aggregated by ISO week start (Monday). Each task’s allocation is spread linearly across its weekly buckets.
- Retainage is handled at the final week (held back and paid at the end) by the cashflow generator.
- If a schedule file is missing, scripts may fall back to a small generated schedule or a simple S-curve approximation.
