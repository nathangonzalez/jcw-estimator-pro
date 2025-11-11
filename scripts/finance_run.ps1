python scripts/finance_csv_normalize.py --input data/financial/raw/accountActivityExport.csv --out data/financial/working/transactions.csv.tmp_csv

python scripts/finance_build_ledger.py --csv data/financial/working/transactions.csv.tmp_csv --pdf data/financial/working/transactions.csv.tmp_pdf --out data/financial/working/transactions.csv --recon data/financial/working/recon_pdf_vs_csv.csv

python scripts/finance_cashflow.py
