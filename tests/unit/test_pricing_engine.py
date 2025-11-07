import json
from web.backend.pricing_engine import price_quantities

def test_price_quantities_basic():
    quantities = [
        {"trade":"concrete","code":"FOOTING","description":"Footings","uom":"CY","qty":10},
        {"trade":"plumbing","code":"ROUGH","description":"Rough-in","uom":"EA","qty":1},
    ]
    policy_yaml = """
policy_id: pricing_policy.v0
region: boston
markups: { overhead_pct: 0.1, profit_pct: 0.05 }
waste_defaults: { global_pct: 0.03, concrete: 0.05 }
tax_pct: 0.0625
escalation_pct: 0.02
resolution_order: [vendor_quotes, unit_costs, policy_defaults]
"""
    unit_costs_csv = "trade,code,unit_cost\nconcrete,FOOTING,180\nplumbing,ROUGH,2500\n"
    vendor_quotes_csv = "trade,code,unit_cost\nplumbing,ROUGH,2300\n"

    res = price_quantities(
        quantities=quantities,
        policy_yaml=policy_yaml,
        region="boston",
        unit_costs_csv=unit_costs_csv,
        vendor_quotes_csv=vendor_quotes_csv,
    )
    assert res["version"] == "v0"
    assert res["grand_total"] > 0
    # vendor override applied for plumbing/ROUGH
    li = { (x["trade"], x["code"]): x for x in res["line_items"] }
    assert li[("plumbing","ROUGH")]["unit_cost"] == 2300
