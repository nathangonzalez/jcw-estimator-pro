import pandas as pd
import argparse
import os
import glob
import re
from pdfminer.high_level import extract_text
from dateutil import parser as date_parser

def parse_csv_transactions(csv_path):
    df = pd.read_csv(csv_path)
    # Assume same format as before
    header_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'date' in col_lower:
            header_map['date'] = col
        elif 'description' in col_lower:
            header_map['description'] = col
        elif 'amount' in col_lower:
            header_map['amount'] = col

    transactions = []
    for idx, row in df.iterrows():
        date_str = str(row[header_map.get('date', df.columns[0])])
        desc = str(row[header_map.get('description', df.columns[1])])
        amount = float(row.get(header_map.get('amount', 0), 0))
        transactions.append({
            'txn_id': f"csv_{idx}",
            'date': date_str,
            'source': 'csv',
            'account': 'unknown',
            'description': desc,
            'category': 'unknown',
            'amount': amount,
            'sign': 1 if amount > 0 else -1
        })
    return transactions

def parse_pdf_transactions(pdf_path):
    try:
        text = extract_text(pdf_path)
        lines = text.split('\n')
        transactions = []
        seq = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            date_match = re.search(r'\b(\d{1,2}/\d{1,2}/(?:\d{2}|\d{4}))\b', line)
            amount_match = re.search(r'(\(?\-?\$?[\d,]+\.?\d*\)?)', line)
            if date_match and amount_match:
                date_str = date_match.group(1)
                amount_str = amount_match.group(1)
                amount_clean = re.sub(r'[^\d\-\.]', '', amount_str)
                try:
                    amount = float(amount_clean)
                    if '(' in amount_str and ')' in amount_str:
                        amount = -abs(amount)
                except:
                    continue
                desc = re.sub(r'\b' + re.escape(date_str) + r'\b', '', line)
                desc = re.sub(r'\(?\-?\$?[\d,]+\.?\d*\)?', '', desc).strip()
                transactions.append({
                    'txn_id': f"pdf_{seq}",
                    'date': date_str,
                    'source': 'pdf',
                    'account': 'unknown',
                    'description': desc,
                    'category': 'unknown',
                    'amount': amount,
                    'sign': 1 if amount > 0 else -1
                })
                seq += 1
        return transactions
    except Exception as e:
        return []

def main():
    inbox_dir = 'data/finance/inbox'
    os.makedirs('data/finance/working', exist_ok=True)

    all_transactions = []
    csv_files = glob.glob(os.path.join(inbox_dir, '*.csv'))
    pdf_files = glob.glob(os.path.join(inbox_dir, '*.pdf'))

    errors = []
    for csv_file in csv_files:
        try:
            all_transactions.extend(parse_csv_transactions(csv_file))
        except Exception as e:
            errors.append(f"CSV {csv_file}: {e}")

    for pdf_file in pdf_files:
        try:
            all_transactions.extend(parse_pdf_transactions(pdf_file))
        except Exception as e:
            errors.append(f"PDF {pdf_file}: {e}")

    df = pd.DataFrame(all_transactions)
    df.to_csv('data/finance/working/ledger.canonical.csv', index=False)

    # QA
    with open('output/FINANCE_INGEST_SUMMARY.md', 'w') as f:
        f.write('# Finance Ingest Summary\n\n')
        f.write(f'- CSV files: {len(csv_files)}\n')
        f.write(f'- PDF files: {len(pdf_files)}\n')
        f.write(f'- Total transactions: {len(all_transactions)}\n')

    with open('output/FINANCE_INGEST_ERRORS.md', 'w') as f:
        f.write('# Finance Ingest Errors\n\n')
        for error in errors:
            f.write(f'- {error}\n')

if __name__ == '__main__':
    main()
