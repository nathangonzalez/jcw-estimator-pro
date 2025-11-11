# MVP Run Checklist

1. Verify Python environment and dependencies are installed (requirements.txt).
2. Prepare Ueltchi estimate input data in data/ueltchi/.
3. Execute Ueltchi estimate exporter to generate collapsed totals.
4. Review output/ueltchi/ESTIMATE.xlsx and SCHEDULE.xlsx for accuracy.
5. Prepare bank CSV files (Jul–Oct 2025) in data/finance/ with ownership cutover data.
6. Run finance ledger accrual processing with add-back rules.
7. Generate monthly summaries, forecasts, and KPI calculations.
8. Verify all output artifacts in output/finance/ and output/ueltchi/.
9. Review output/RECEIPT.md for key totals and paths.
10. Commit changes with the specified message if all checks pass.
