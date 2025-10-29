# Assistant Requests

This directory contains validation-only payloads for the file-based gateway.

## Approval

All request JSON/JSONL must include `"approved": true`. The gateway will reject anything without it.

## Types

- **ping** — tiny, trivial request to verify the path.
- **estimate-v1** — intended for /v1/estimate, but not executed by this plan.

## Batches

Keep batches conservative at first. The gateway caps:

- Max file size ~200 KB
- Max lines per JSONL: 200
