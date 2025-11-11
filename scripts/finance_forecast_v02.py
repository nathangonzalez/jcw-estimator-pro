import pandas as pd
import yaml
import argparse
from datetime import datetime, timedelta

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ledger', default='data/finance/working/ledger.canonical.csv')
    parser.add_argument('--assumptions', default='data/finance/assumptions.yaml')
    args = parser.parse_args()

    df = pd.read_csv(args.ledger)
    df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y', errors='coerce')
    df = df.dropna(subset=['date'])
    df = df.sort_values('date')

    # Starting balance
    df['cumsum'] = df['amount'].cumsum()
    starting_balance = df['cumsum'].iloc[-1] if not df.empty else 0

    # Recent net average (last 90 days)
    end_date = df['date'].max()
    start_date = end_date - timedelta(days=90)
    recent = df[df['date'] >= start_date]
    avg_weekly_net = recent['amount'].sum() / 12  # approx weekly

    # Assumptions
    assumptions = {'recurring_outflows': [], 'recurring_inflows': [], 'starting_balance': starting_balance}
    if pd.io.common.file_exists(args.assumptions):
        with open(args.assumptions, 'r') as f:
            assumptions.update(yaml.safe_load(f))

    starting_balance = assumptions.get('starting_balance', starting_balance)

    # Forecast 13 weeks
    forecast = []
    current_balance = starting_balance
    current_date = datetime.now()
    for week in range(13):
        week_start = current_date + timedelta(weeks=week)
        projected_net = avg_weekly_net
        current_balance += projected_net
        forecast.append({
            'week': f'Week {week+1}',
            'start_date': week_start.strftime('%Y-%m-%d'),
            'projected_inflow': max(0, projected_net),
            'projected_outflow': max(0, -projected_net),
            'projected_net': projected_net,
            'ending_balance': current_balance
        })

    forecast_df = pd.DataFrame(forecast)
    forecast_df.to_csv('output/FINANCE_13W_FORECAST.csv', index=False)

    # Runway
    min_balance = min(forecast_df['ending_balance'])
    weeks_to_negative = None
    for i, row in forecast_df.iterrows():
        if row['ending_balance'] < 0:
            weeks_to_negative = i + 1
            break

    with open('output/FINANCE_RUNWAY.md', 'w') as f:
        f.write('# Cash Runway Analysis\n\n')
        f.write(f'Starting Balance: {starting_balance:.2f}\n\n')
        f.write(f'Min Balance in 13 weeks: {min_balance:.2f}\n\n')
        if weeks_to_negative:
            f.write(f'Weeks to negative balance: {weeks_to_negative}\n\n')
        else:
            f.write('No negative balance in 13 weeks\n\n')

    # Project overlay if LYNN_BURN exists
    if pd.io.common.file_exists('output/LYNN_BURN_CURVE.csv'):
        burn_df = pd.read_csv('output/LYNN_BURN_CURVE.csv')
        with open('output/FINANCE_RUNWAY.md', 'a') as f:
            f.write('## Project Overlay\n\n')
            f.write('Burn curve integrated (placeholder)\n\n')

if __name__ == '__main__':
    main()
