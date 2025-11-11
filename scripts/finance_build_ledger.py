import pandas as pd
import argparse
import os

def normalize_desc(desc):
    return desc.lower().strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', required=True)
    parser.add_argument('--pdf', default=None)
    parser.add_argument('--out', required=True)
    parser.add_argument('--recon', required=True)
    args = parser.parse_args()

    # Load CSV
    csv_df = pd.read_csv(args.csv)
    csv_df['source_type'] = 'csv'

    all_dfs = [csv_df]

    # Load PDF if exists
    if args.pdf and os.path.exists(args.pdf):
        pdf_df = pd.read_csv(args.pdf)
        pdf_df['source_type'] = 'pdf'
        all_dfs.append(pdf_df)
    else:
        pdf_df = pd.DataFrame()

    combined_df = pd.concat(all_dfs, ignore_index=True)

    # De-dupe
    def make_key(row):
        return (
            str(row['date']),
            round(row['amount'], 2),
            normalize_desc(row['description']),
            str(row.get('check_no', '')),
            str(row.get('counterparty', ''))
        )

    combined_df['key'] = combined_df.apply(make_key, axis=1)

    # Keep first occurrence
    deduped_df = combined_df.drop_duplicates(subset='key', keep='first')

    # Recon
    recon_rows = []
    for key in combined_df['key'].unique():
        group = combined_df[combined_df['key'] == key]
        in_csv = 'csv' in group['source_type'].values
        in_pdf = 'pdf' in group['source_type'].values
        amount_csv = group[group['source_type'] == 'csv']['amount'].iloc[0] if in_csv else 0
        amount_pdf = group[group['source_type'] == 'pdf']['amount'].iloc[0] if in_pdf else 0
        delta = abs(amount_csv - amount_pdf) if in_csv and in_pdf else 0
        desc_sample = group['description'].iloc[0]
        recon_rows.append({
            'key': key,
            'in_pdf': in_pdf,
            'in_csv': in_csv,
            'amount_pdf': amount_pdf,
            'amount_csv': amount_csv,
            'delta': delta,
            'description_sample': desc_sample
        })

    recon_df = pd.DataFrame(recon_rows)
    recon_df.to_csv(args.recon, index=False)

    # Output canonical
    deduped_df.drop(columns=['key', 'source_type'], inplace=True)
    deduped_df.to_csv(args.out, index=False)

if __name__ == '__main__':
    main()
