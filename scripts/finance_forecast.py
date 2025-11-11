import pandas as pd
import yaml
import argparse
from dateutil import parser as date_parser
from datetime import datetime, timedelta
import calendar

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--assumptions', required=True)
    parser.add_argument('--ledger', required=True)
    args = parser.parse_args()

    # Load assumptions
    with open(args.assumptions, 'r') as f:
        assumptions = yaml.safe_load(f)

    # Load ledger
    df = pd.read_csv(args.ledger)
    df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y', errors='coerce')
    df = df.dropna(subset=['date'])

    # Categorize inflows/outflows
    expense_categories = ["payroll", "materials", "insurance", "fuel"]
    df['is_inflow'] = (df['amount'] > 0) & (~df['category'].isin(expense_categories))
    df['is_outflow'] = (df['amount'] < 0) | (df['category'].isin(expense_categories) & (df['amount'] > 0))

    # Daily aggregates
    daily = df.groupby('date').agg(
        inflow=('amount', lambda x: x[x > 0].sum()),
        outflow=('amount', lambda x: abs(x[x < 0].sum())),
        net=('amount', 'sum')
    ).reset_index()

    # Rolling SMA
    window = assumptions['smoothing_window_days']
    daily['net_sma'] = daily['net'].rolling(window=window, min_periods=1).mean()

    # Baseline: recent 90 days avg monthly net
    recent_90 = daily[daily['date'] >= (daily['date'].max() - timedelta(days=90))]
    monthly_avg_net = recent_90['net'].sum() / 3  # approx monthly

    # Starting balance proxy: cumulative sum last
    df_sorted = df.sort_values('date')
    df_sorted['cumsum'] = df_sorted['amount'].cumsum()
    starting_balance = df_sorted['cumsum'].iloc[-1] if not df_sorted.empty else 0
    starting_balance += assumptions['working_capital_buffer']

    # Project forward
    start_month = date_parser.parse(assumptions['start_month'])
    horizon = assumptions['horizon_months']
    seasonality = assumptions.get('seasonality', {})

    forecast = []
    current_balance = starting_balance
    for i in range(horizon):
        month_date = start_month + timedelta(days=30 * i)
        month_str = month_date.strftime('%Y-%m')
        multiplier = seasonality.get(month_date.strftime('%m'), 1.0)
        projected_net = monthly_avg_net * multiplier
        projected_inflow = max(0, projected_net)  # assume positive is inflow
        projected_outflow = max(0, -projected_net)
        current_balance += projected_net
        forecast.append({
            'month': month_str,
            'projected_inflow': projected_inflow,
            'projected_outflow': projected_outflow,
            'projected_net': projected_net,
            'ending_cash': current_balance
        })

    forecast_df = pd.DataFrame(forecast)

    # Emit MD
    with open('output/FINANCE_FORECAST.md', 'w') as f:
        f.write('# Cash Forecast\n\n')
        f.write(f'Starting Balance: {starting_balance:.2f}\n\n')
        f.write(forecast_df.to_markdown(index=False))

    # Emit HTML with sparkline
    html = '<html><body><h1>Cash Forecast</h1>'
    html += f'<p>Starting Balance: {starting_balance:.2f}</p>'
    html += forecast_df.to_html(index=False)
    # Simple sparkline (placeholder)
    html += '<svg width="200" height="50"><polyline points="'
    points = []
    for i, row in forecast_df.iterrows():
        x = i * 20
        y = 25 - (row['ending_cash'] / 1000)  # scale
        points.append(f'{x},{y}')
    html += ' '.join(points) + '" stroke="blue" fill="none"/></svg>'
    html += '</body></html>'

    with open('output/FINANCE_FORECAST.html', 'w') as f:
        f.write(html)

if __name__ == '__main__':
    main()
