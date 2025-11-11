import pandas as pd
import argparse
from collections import defaultdict

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ledger', default='data/financial/working/transactions.csv')
    parser.add_argument('--recon', default='data/financial/working/recon_pdf_vs_csv.csv')
    args = parser.parse_args()

    ledger_df = pd.read_csv(args.ledger)
    recon_df = pd.read_csv(args.recon) if args.recon and pd.io.common.file_exists(args.recon) else pd.DataFrame()

    # Row counts
    csv_count = ledger_df[ledger_df['source'] == 'csv'].shape[0]
    pdf_count = ledger_df[ledger_df['source'] == 'pdf'].shape[0] if 'source' in ledger_df.columns else 0
    merged_count = ledger_df.shape[0]
    dedup_count = csv_count + pdf_count - merged_count

    # Recon stats
    recon_stats = {}
    if not recon_df.empty:
        recon_stats = {
            'total_keys': recon_df.shape[0],
            'in_both': recon_df[(recon_df['in_pdf']) & (recon_df['in_csv'])].shape[0],
            'deltas': recon_df[recon_df['delta'] > 0].shape[0]
        }

    # Cashflow
    ledger_df['date'] = pd.to_datetime(ledger_df['date'], format='%m/%d/%Y', errors='coerce')
    ledger_df['month'] = ledger_df['date'].dt.to_period('M')
    ledger_df['year'] = ledger_df['date'].dt.year

    # YTD
    current_year = ledger_df['year'].max()
    ytd_df = ledger_df[ledger_df['year'] == current_year]
    ytd_inflow = ytd_df[ytd_df['amount'] > 0]['amount'].sum()
    ytd_outflow = abs(ytd_df[ytd_df['amount'] < 0]['amount'].sum())
    ytd_net = ytd_inflow - ytd_outflow

    # Monthly
    monthly = ledger_df.groupby('month').agg(
        inflow=('amount', lambda x: x[x > 0].sum()),
        outflow=('amount', lambda x: abs(x[x < 0].sum())),
        net=('amount', 'sum')
    ).reset_index()

    # Top 10 outflow counterparties
    outflow_df = ledger_df[ledger_df['amount'] < 0].copy()
    outflow_df['amount'] = outflow_df['amount'].abs()
    top_outflow = outflow_df.groupby('counterparty')['amount'].sum().nlargest(10).reset_index()

    # By-category monthly rollup
    category_monthly = ledger_df.groupby(['month', 'category']).agg(
        inflow=('amount', lambda x: x[x > 0].sum()),
        outflow=('amount', lambda x: abs(x[x < 0].sum())),
        net=('amount', 'sum')
    ).reset_index()

    # Uncategorize count
    uncategorized = ledger_df[ledger_df['category'].isnull() | (ledger_df['category'] == '')].shape[0]

    # Append to FINANCE_RUN.md
    with open('output/FINANCE_RUN.md', 'a') as f:
        f.write('\n## QA Section\n\n')
        f.write(f'- Uncategorize rows: {uncategorized}\n')
        f.write(f'- Months covered: {ledger_df["month"].nunique()}\n')
        f.write(f'- Cash-flow outputs: output/FINANCE_CASHFLOW.md, output/FINANCE_CASHFLOW.html\n')

    # Emit FINANCE_CASHFLOW.md
    with open('output/FINANCE_CASHFLOW.md', 'w') as f:
        f.write('# Cash-Flow Summary\n\n')
        f.write('## YTD\n\n')
        f.write(f'- Inflow: {ytd_inflow:.2f}\n')
        f.write(f'- Outflow: {ytd_outflow:.2f}\n')
        f.write(f'- Net: {ytd_net:.2f}\n\n')
        f.write('## Monthly\n\n')
        f.write(monthly.to_markdown(index=False))
        f.write('\n\n## By-Category Monthly\n\n')
        f.write(category_monthly.to_markdown(index=False))
        f.write('\n\n## Top 10 Outflow Counterparties\n\n')
        f.write(top_outflow.to_markdown(index=False))

    # Emit FINANCE_CASHFLOW.html
    html = '<html><body><h1>Cash-Flow Summary</h1>'
    html += '<h2>YTD</h2>'
    html += f'<p>Inflow: {ytd_inflow:.2f}</p>'
    html += f'<p>Outflow: {ytd_outflow:.2f}</p>'
    html += f'<p>Net: {ytd_net:.2f}</p>'
    html += '<h2>Monthly</h2>'
    html += monthly.to_html(index=False)
    html += '<h2>By-Category Monthly</h2>'
    html += category_monthly.to_html(index=False)
    html += '<h2>Top 10 Outflow Counterparties</h2>'
    html += top_outflow.to_html(index=False)
    html += '</body></html>'

    with open('output/FINANCE_CASHFLOW.html', 'w') as f:
        f.write(html)

if __name__ == '__main__':
    main()
