#!/usr/bin/env python3
"""
Finance Export v0 - Convert estimate JSON to finance-ready CSVs
Reads latest estimate JSON and emits SOV seed and forecast seed CSVs
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, Optional

def find_estimate_json() -> Optional[str]:
    """Find the most recent estimate JSON file in priority order"""
    candidates = [
        "data/lynn/working/PIPELINE_ESTIMATE_RESPONSE_CALIBRATED.json",
        "data/lynn/working/PIPELINE_ESTIMATE_RESPONSE.json",
        "output/PIPELINE_ESTIMATE_RESPONSE.json"
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            print(f"Found estimate JSON: {candidate}")
            return candidate

    print("No estimate JSON found in expected locations")
    return None

def load_estimate_data(json_path: str) -> Optional[Dict[str, Any]]:
    """Load and validate estimate JSON data"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Basic validation - should have trades and some total
        if not isinstance(data, dict):
            print(f"Invalid JSON structure in {json_path}")
            return None

        if 'trades' not in data:
            print(f"No trades found in {json_path}")
            return None

        # Extract project_id from meta or use default
        project_id = "unknown"
        if 'meta' in data and isinstance(data['meta'], dict):
            project_id = data['meta'].get('project_id', 'unknown')

        return data

    except Exception as e:
        print(f"Error loading {json_path}: {e}")
        return None

def extract_project_id(data: Dict[str, Any]) -> str:
    """Extract project ID from estimate data"""
    if 'meta' in data and isinstance(data['meta'], dict):
        return data['meta'].get('project_id', 'unknown')
    return 'unknown'

def calculate_grand_total(data: Dict[str, Any]) -> float:
    """Calculate grand total from estimate data"""
    # Try different total fields
    for field in ['grand_total', 'total_cost', 'totals.grand_total']:
        keys = field.split('.')
        value = data
        try:
            for key in keys:
                value = value[key]
            if isinstance(value, (int, float)):
                return float(value)
        except (KeyError, TypeError):
            continue

    # Fallback: sum all trade subtotals
    total = 0.0
    if 'trades' in data:
        trades = data['trades']
        if isinstance(trades, list):
            for trade in trades:
                if isinstance(trade, dict) and 'subtotal' in trade:
                    total += float(trade.get('subtotal', 0))
        elif isinstance(trades, dict):
            for trade_name, trade_data in trades.items():
                if isinstance(trade_data, dict):
                    # Sum items in this trade
                    if 'items' in trade_data:
                        for item in trade_data['items']:
                            if isinstance(item, dict) and 'total' in item:
                                total += float(item.get('total', 0))

    return total

def export_estimate_csv(data: Dict[str, Any], output_path: str):
    """Export detailed estimate lines to CSV"""
    project_id = extract_project_id(data)

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['project_id', 'trade', 'item', 'quantity', 'unit', 'unit_cost', 'line_total', 'source', 'room', 'notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        trades = data.get('trades', {})
        if isinstance(trades, list):
            # Convert list format to dict for processing
            trades_dict = {}
            for trade in trades:
                if isinstance(trade, dict) and 'trade' in trade:
                    trade_name = trade['trade']
                    trades_dict[trade_name] = trade
            trades = trades_dict

        for trade_name, trade_data in trades.items():
            if not isinstance(trade_data, dict):
                continue

            items = trade_data.get('items', [])
            if not isinstance(items, list):
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue

                row = {
                    'project_id': project_id,
                    'trade': trade_name,
                    'item': item.get('code', item.get('item', 'unknown')),
                    'quantity': item.get('quantity', item.get('qty', 0)),
                    'unit': item.get('unit', item.get('uom', 'ea')),
                    'unit_cost': item.get('unit_cost', 0),
                    'line_total': item.get('total', item.get('line_total', 0)),
                    'source': item.get('source', 'engine:policy'),
                    'room': '',  # Not available in current schema
                    'notes': item.get('notes', '')
                }
                writer.writerow(row)

def export_sov_seed_csv(data: Dict[str, Any], output_path: str):
    """Export Schedule of Values seed data"""
    project_id = extract_project_id(data)

    # Calculate totals by trade
    trade_totals = {}
    trades = data.get('trades', {})

    if isinstance(trades, list):
        # Convert list format to dict for processing
        trades_dict = {}
        for trade in trades:
            if isinstance(trade, dict) and 'trade' in trade:
                trade_name = trade['trade']
                trades_dict[trade_name] = trade
        trades = trades_dict

    for trade_name, trade_data in trades.items():
        if not isinstance(trade_data, dict):
            continue

        total = 0.0
        items = trade_data.get('items', [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    total += float(item.get('total', item.get('line_total', 0)))

        if total > 0:
            trade_totals[trade_name] = total

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['sov_code', 'description', 'trade', 'amount', 'retainage_pct']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for trade_name, amount in trade_totals.items():
            row = {
                'sov_code': f"TRD-{trade_name.upper()}",
                'description': f"Schedule of Values — {trade_name.title()}",
                'trade': trade_name,
                'amount': round(amount, 2),
                'retainage_pct': 0.10  # 10% default retainage
            }
            writer.writerow(row)

def export_forecast_seed_csv(data: Dict[str, Any], output_path: str):
    """Export cashflow forecast seed data"""
    project_id = extract_project_id(data)
    grand_total = calculate_grand_total(data)

    # Divide total evenly across 3 periods
    period_amount = grand_total / 3

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['period', 'inflow_type', 'inflow_amount', 'outflow_type', 'outflow_amount', 'notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Create 3 periods with inflows and outflows
        for period in ['P1', 'P2', 'P3']:
            # Inflows: SOV draws
            inflow_row = {
                'period': period,
                'inflow_type': 'SOV draw',
                'inflow_amount': round(period_amount, 2),
                'outflow_type': '',
                'outflow_amount': '',
                'notes': f'Project {project_id} - auto-seed v0'
            }
            writer.writerow(inflow_row)

            # Outflows: Vendor payments (30/40/30 split)
            outflow_splits = {'P1': 0.30, 'P2': 0.40, 'P3': 0.30}
            outflow_amount = grand_total * outflow_splits[period]

            outflow_row = {
                'period': period,
                'inflow_type': '',
                'inflow_amount': '',
                'outflow_type': 'vendor payout',
                'outflow_amount': round(outflow_amount, 2),
                'notes': f'Project {project_id} - auto-seed v0'
            }
            writer.writerow(outflow_row)

def main():
    """Main export function"""
    print("Finance Export v0 - Starting...")

    # Find estimate JSON
    json_path = find_estimate_json()
    if not json_path:
        # Write diagnostic file
        with open("output/FINANCE_DIAGNOSE.md", 'w') as f:
            f.write("# Finance Export Diagnosis\n\nNo estimate JSON found in expected locations:\n")
            f.write("- data/lynn/working/PIPELINE_ESTIMATE_RESPONSE_CALIBRATED.json\n")
            f.write("- data/lynn/working/PIPELINE_ESTIMATE_RESPONSE.json\n")
            f.write("- output/PIPELINE_ESTIMATE_RESPONSE.json\n")
        print("Exiting - no estimate data found")
        return

    # Load estimate data
    data = load_estimate_data(json_path)
    if not data:
        print("Failed to load estimate data")
        return

    # Ensure finance output directory
    os.makedirs("output/finance", exist_ok=True)

    # Export CSVs
    export_estimate_csv(data, "output/finance/estimate_export.csv")
    export_sov_seed_csv(data, "output/finance/sov_seed.csv")
    export_forecast_seed_csv(data, "output/finance/forecast_seed.csv")

    # Write receipt
    with open("output/FINANCE_RECEIPT.md", 'w') as f:
        f.write("# Finance Export Receipt\n\n")
        f.write(f"- Source: {json_path}\n")
        f.write(f"- Project ID: {extract_project_id(data)}\n")
        f.write(f"- Grand Total: ${calculate_grand_total(data):,.2f}\n")
        f.write("- Exports:\n")
        f.write("  - output/finance/estimate_export.csv (detailed line items)\n")
        f.write("  - output/finance/sov_seed.csv (SOV schedule)\n")
        f.write("  - output/finance/forecast_seed.csv (cashflow forecast)\n")

    print("Finance export complete!")

if __name__ == "__main__":
    main()
