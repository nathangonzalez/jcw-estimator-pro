import pandas as pd
import argparse
from datetime import datetime, timedelta

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ledger', required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.ledger)
    df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y', errors='coerce')
    df = df.dropna(subset=['date'])
    df = df.sort_values('date')

    # Current balance proxy
    df['cumsum'] = df['amount'].cumsum()
    current_balance = df['cumsum'].iloc[-1] if not df.empty else 0

    # Burn rates
    end_date = df['date'].max()
    burns = {}
    for days in [30, 60, 90]:
        start_date = end_date - timedelta(days=days)
        period_df = df[df['date'] >= start_date]
        total_net = period_df['amount'].sum()
        avg_monthly_burn = total_net / (days / 30)
        burns[days] = avg_monthly_burn

    # Runway
    avg_burn_90 = burns[90]
    runway_months = abs(current_balance / avg_burn_90) if avg_burn_90 < 0 else float('inf')

    # Top expense categories
    expenses = df[df['amount'] < 0].copy()
    expenses['amount'] = expenses['amount'].abs()
    top_categories = expenses.groupby('category')['amount'].sum().nlargest(10).reset_index()

    # Top vendors
    top_vendors = expenses.groupby('counterparty')['amount'].sum().nlargest(10).reset_index()

    # Emit MD
    with open('output/FINANCE_BURN.md', 'w') as f:
        f.write('# Burn & Runway Analysis\n\n')
        f.write(f'Current Balance Proxy: {current_balance:.2f}\n\n')
        f.write('## Burn Rates (Avg Monthly Net Outflow)\n\n')
        for days, burn in burns.items():
            f.write(f'{days}-day: {burn:.2f}\n')
        f.write(f'\nRunway Months: {runway_months:.1f}\n\n')
        f.write('## Top 10 Expense Categories\n\n')
        f.write(top_categories.to_markdown(index=False))
        f.write('\n\n## Top 10 Vendors\n\n')
        f.write(top_vendors.to_markdown(index=False))

    # Emit HTML
    html = '<html><body><h1>Burn & Runway Analysis</h1>'
    html += f'<p>Current Balance Proxy: {current_balance:.2f}</p>'
    html += '<h2>Burn Rates</h2><ul>'
    for days, burn in burns.items():
        html += f'<li>{days}-day: {burn:.2f}</li>'
    html += f'</ul><p>Runway Months: {runway_months:.1f}</p>'
    html += '<h2>Top 10 Expense Categories</h2>'
    html += top_categories.to_html(index=False)
    html += '<h2>Top 10 Vendors</h2>'
    html += top_vendors.to_html(index=False)
    html += '</body></html>'

    with open('output/FINANCE_BURN.html', 'w') as f:
        f.write(html)

if __name__ == '__main__':
    main()
