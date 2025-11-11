import argparse
import os
import glob
import re
from pdfminer.high_level import extract_text
import pandas as pd
from dateutil import parser as date_parser

def extract_transactions_from_text(text, filename):
    lines = text.split('\n')
    transactions = []
    seq = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Regex for date: MM/DD/YYYY or MM/DD/YY
        date_match = re.search(r'\b(\d{1,2}/\d{1,2}/(?:\d{2}|\d{4}))\b', line)
        # Regex for amount: supports $, commas, negatives in parens
        amount_match = re.search(r'(\(?\-?\$?[\d,]+\.?\d*\)?)', line)
        if date_match and amount_match:
            date_str = date_match.group(1)
            amount_str = amount_match.group(1)
            # Parse amount
            amount_clean = re.sub(r'[^\d\-\.]', '', amount_str)
            try:
                amount = float(amount_clean)
                if '(' in amount_str and ')' in amount_str:
                    amount = -abs(amount)
            except:
                continue
            # Description: line without date and amount
            desc = re.sub(r'\b' + re.escape(date_str) + r'\b', '', line)
            desc = re.sub(r'\(?\-?\$?[\d,]+\.?\d*\)?', '', desc).strip()
            # Type: guess
            typ = 'other'
            if 'check' in desc.lower():
                typ = 'check'
            elif amount > 0:
                typ = 'deposit'
            else:
                typ = 'card'
            transactions.append({
                'date': date_str,
                'description': desc,
                'type': typ,
                'amount': amount,
                'debit': amount if amount < 0 else 0,
                'credit': amount if amount > 0 else 0,
                'check_no': None,
                'counterparty': None,
                'category': None,
                'account_last4': None,
                'source': 'pdf',
                'source_pdf': filename,
                'source_row': seq
            })
            seq += 1
    return transactions

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()

    all_transactions = []
    pdf_files = glob.glob(os.path.join(args.root, '**', '*.pdf'), recursive=True)
    qa_notes = []
    for pdf_path in pdf_files:
        try:
            text = extract_text(pdf_path)
            if not text.strip():
                qa_notes.append(f"{pdf_path}: empty text, ocr_needed")
                continue
            transactions = extract_transactions_from_text(text, os.path.basename(pdf_path))
            all_transactions.extend(transactions)
        except Exception as e:
            qa_notes.append(f"{pdf_path}: error {e}, ocr_needed")

    df = pd.DataFrame(all_transactions)
    df.to_csv(args.out, index=False)

    # Write QA
    with open('output/FINANCE_QA.md', 'w') as f:
        f.write('# Finance QA Notes\n\n')
        for note in qa_notes:
            f.write(f'- {note}\n')

if __name__ == '__main__':
    main()
