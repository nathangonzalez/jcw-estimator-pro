import pandas as pd
import argparse
from dateutil import parser as date_parser
import re

def normalize_type(desc, amount):
    desc_lower = desc.lower()
    if 'check' in desc_lower:
        return 'check'
    elif 'ach' in desc_lower and amount > 0:
        return 'ach_in'
    elif 'ach' in desc_lower and amount < 0:
        return 'ach_out'
    elif 'deposit' in desc_lower:
        return 'deposit'
    elif 'withdrawal' in desc_lower or 'payment' in desc_lower:
        return 'ach_out'
    elif 'pos' in desc_lower or 'card' in desc_lower:
        return 'card'
    elif 'fee' in desc_lower:
        return 'fee'
    elif 'interest' in desc_lower:
        return 'interest'
    else:
        return 'other'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    # Tolerant header mapping
    header_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'date' in col_lower or 'transaction date' in col_lower:
            header_map['date'] = col
        elif 'description' in col_lower or 'details' in col_lower:
            header_map['description'] = col
        elif 'amount' in col_lower:
            header_map['amount'] = col
        elif 'credit' in col_lower:
            header_map['credit'] = col
        elif 'debit' in col_lower:
            header_map['debit'] = col

    canonical_rows = []
    for idx, row in df.iterrows():
        # Date
        date_str = str(row[header_map.get('date', df.columns[0])])
        try:
            date = date_parser.parse(date_str).date()
        except:
            date = None

        # Description
        description = str(row[header_map.get('description', df.columns[1])])

        # Signed amount
        if 'amount' in header_map:
            amount = float(row[header_map['amount']])
        else:
            credit = float(row.get(header_map.get('credit', 0), 0))
            debit = float(row.get(header_map.get('debit', 0), 0))
            amount = credit - debit

        # Type
        typ = normalize_type(description, amount)

        # Other fields
        check_no = None
        if typ == 'check':
            match = re.search(r'check\s*(\d+)', description, re.IGNORECASE)
            if match:
                check_no = match.group(1)

        counterparty = None
        # Simple extraction, e.g. after 'to' or 'from'
        match = re.search(r'(?:to|from)\s+([A-Za-z\s]+)', description, re.IGNORECASE)
        if match:
            counterparty = match.group(1).strip()

        canonical_rows.append({
            'date': date,
            'description': description,
            'type': typ,
            'amount': amount,
            'debit': amount if amount < 0 else 0,
            'credit': amount if amount > 0 else 0,
            'check_no': check_no,
            'counterparty': counterparty,
            'category': None,
            'account_last4': None,
            'source': 'csv',
            'source_pdf': None,
            'source_row': idx + 1
        })

    out_df = pd.DataFrame(canonical_rows)
    out_df.to_csv(args.out, index=False)

if __name__ == '__main__':
    main()
