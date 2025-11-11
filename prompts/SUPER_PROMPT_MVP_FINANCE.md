SYSTEM: DEV-FAST, supervised. No force-push. Repo-local only.

TASK 0 — Persist the Super Prompt
- Create output/READ_ME_FIRST.md with a 10-line checklist on how to run Estimating/PM (Ueltchi) and Finance MVP.

TASK 1 — Estimating/PM (Ueltchi-first)
- Exporters collapse exploded estimate lines to template-level totals while keeping detailed traceability.
- Emit:
  - output/ueltchi/ESTIMATE.xlsx
  - output/ueltchi/SCHEDULE.xlsx
  - output/ueltchi/ESTIMATE_SUMMARY.md (totals + traceability notes)

TASK 2 — Finance MVP (company-wide)
- Load bank CSVs (Jul–Oct 2025), ownership cutover (7/1), accrual mapping (1–10 receipts → prior month revenue; 10–EOM vendor costs → prior month COGS).
- Apply add-backs (personal utilities, Town of Jupiter, personal CCs except Sapphire & Southwest business, auto loans, landscaping, Ferrellgas, etc.).
- Exclude LOC/Equity/SBA flows from income; include only in cashflow.
- Emit:
  - output/finance/LEDGER_ACCRUAL.csv
  - output/finance/MONTHLY_SUMMARY.csv
  - output/finance/ADD_BACK_SCHEDULE.csv
  - output/finance/FORECAST_12M.xlsx (flat run-rate baseline)
  - output/finance/KPIS.json (GM%, Adjusted EBITDA, Overhead vs Add-back split, Debt Service coverage)

TASK 3 — Receipts
- Write output/RECEIPT.md summarizing key totals and artifact paths.

COMMIT (single commit)
- Message:
  chore(mvp): persist super-prompt; emit Ueltchi estimate/schedule; finance ledger+summary+forecast+KPIs (DEV-FAST)

RULES
- Do NOT run Playwright or vendor parsing in this pass.
- If any required input is missing, emit a stub and note it in output/RECEIPT.md, then continue.
