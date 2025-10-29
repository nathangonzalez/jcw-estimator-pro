# Cline Load-Test Plan (SYNC-ONLY)

## Purpose: Safely increase token usage to exercise long-context reasoning without executing code.

## What’s included

- Large, realistic request corpora for /v1/estimate under .assistant/requests/.
- Gateway guardrails to require explicit approval flags and enforce token caps.
- Validation scripts (not executed) and documentation.

## What’s not included

- No service execution, no network calls, no Playwright runs, no installs.

## Next (manual/maintainer) steps

- Review the guardrails in .assistant/gateway.py.
- Approve a tiny “ping” request first (.assistant/requests/ping.json), then (optionally) approve a small batch file.
- Keep batch files small at first; scale gradually.
- Monitor GitHub Action runs and captured artifacts before expanding scope.
