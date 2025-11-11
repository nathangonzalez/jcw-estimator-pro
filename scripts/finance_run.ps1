python scripts/finance_csv_normalize.py --input data/financial/raw/accountActivityExport.csv --out data/financial/working/transactions.csv.tmp_csv
python scripts/finance_pdf_extract.py --root data/financial/raw --out data/financial/working/pdf_rows.csv
python scripts/finance_build_ledger.py --csv data/financial/working/transactions.csv.tmp_csv --pdf data/financial/working/pdf_rows.csv --out data/financial/working/transactions.csv --recon data/financial/working/recon_pdf_vs_csv.csv
python scripts/finance_categorize.py --rules data/financial/categories.seed.yaml --inout data/financial/working/transactions.csv
python scripts/finance_cashflow.py
python scripts/finance_forecast.py --assumptions data/financial/working/forecast_assumptions.yaml --ledger data/financial/working/transactions.csv
python scripts/finance_burn.py --ledger data/financial/working/transactions.csv
