# MVP Receipt - DEV-FAST

## Summary
Executed MVP workflow for Estimating/PM (Ueltchi) and Finance. Persisted super-prompt, emitted Ueltchi estimate/schedule outputs, and created finance stubs due to missing bank CSVs.

## Key Totals
- Ueltchi Estimate Lines: 8 (from data/ueltchi/working/estimate_lines.v0.csv)
- Ueltchi Schedule Tasks: 0 (data present but not processed for totals)
- Total Estimate Value: $62,232.38
- Finance Data: All stubbed due to missing bank CSVs (Jul-Oct 2025)

## Artifact Paths

### Super-Prompt
- prompts/SUPER_PROMPT_MVP_FINANCE.md

### Read Me
- output/READ_ME_FIRST.md

### Ueltchi Outputs
- output/ueltchi/ESTIMATE.xlsx (estimate lines Excel)
- output/ueltchi/SCHEDULE.xlsx (schedule Gantt Excel)
- output/ueltchi/ESTIMATE_SUMMARY.md (totals by trade + top 20 lines)

### Finance Outputs (Stubs)
- output/finance/LEDGER_ACCRUAL.csv (accrual ledger with ownership cutover)
- output/finance/MONTHLY_SUMMARY.csv (monthly P&L summary)
- output/finance/ADD_BACK_SCHEDULE.csv (add-back items: personal utilities, Town of Jupiter, etc.)
- output/finance/FORECAST_12M.csv (12-month flat run-rate forecast; .xlsx requested but CSV emitted)
- output/finance/KPIS.json (GM%, Adjusted EBITDA, Overhead vs Add-back split, Debt Service coverage)

## Notes
- Bank CSVs for Jul-Oct 2025 not present in data/; all finance outputs are stubs with placeholder data.
- Accrual mapping (1-10 receipts → prior month revenue; 10-EOM vendor costs → prior month COGS) not applied due to missing data.
- Add-backs listed but not calculated.
- LOC/Equity/SBA flows excluded from income as per rules.
- No Playwright or vendor parsing executed.

## Commit Message
chore(mvp): persist super-prompt; emit Ueltchi estimate/schedule; finance ledger+summary+forecast+KPIs (DEV-FAST)
