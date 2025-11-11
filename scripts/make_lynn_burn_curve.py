import pandas as pd
import argparse
from dateutil import parser as date_parser
from datetime import datetime, timedelta
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='data/lynn/working/estimate_lines_calibrated.csv')
    parser.add_argument('--start_date', default='2025-12-01')
    parser.add_argument('--duration_months', type=int, default=10)
    parser.add_argument('--front_load', type=float, default=0.25)
    args = parser.parse_args()

    # Try calibrated first, else raw
    input_file = args.input
    if not pd.io.common.file_exists(input_file):
        input_file = 'output/LYNN-001/raw_estimate/estimate_lines.csv'

    df = pd.read_csv(input_file)
    if 'line_total' in df.columns:
        total = df['line_total'].sum()
    elif 'ext_cost' in df.columns:
        total = df['ext_cost'].sum()
    else:
        total = 0

    start = date_parser.parse(args.start_date)
    months = []
    spends = []

    # Front load
    first_spend = args.front_load * total
    remaining = total - first_spend
    remaining_months = args.duration_months - 1
    monthly_spend = remaining / remaining_months if remaining_months > 0 else 0

    current = start
    spends.append(first_spend)
    months.append(current.strftime('%Y-%m'))

    for i in range(1, args.duration_months):
        current = start + timedelta(days=30 * i)
        spends.append(monthly_spend)
        months.append(current.strftime('%Y-%m'))

    # CSV
    burn_df = pd.DataFrame({'month': months, 'planned_spend': spends})
    burn_df.to_csv('output/LYNN_BURN_CURVE.csv', index=False)

    # MD
    with open('output/LYNN_BURN_CURVE.md', 'w') as f:
        f.write('# Lynn Burn Curve\n\n')
        f.write(f'Total Estimate: {total:.2f}\n\n')
        f.write(f'Start Date: {args.start_date}\n\n')
        f.write(f'Duration: {args.duration_months} months\n\n')
        f.write(f'Front Load: {args.front_load}\n\n')
        f.write('## Monthly Spend\n\n')
        f.write(burn_df.to_markdown(index=False))

    # JSON
    cashflow = {
        'assumptions': {
            'start_date': args.start_date,
            'duration_months': args.duration_months,
            'front_load': args.front_load,
            'total_estimate': total
        },
        'monthly_cash_need': dict(zip(months, spends))
    }
    with open('output/LYNN_JOB_CASHFLOW.json', 'w') as f:
        json.dump(cashflow, f, indent=2)

if __name__ == '__main__':
    main()
