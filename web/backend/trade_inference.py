import re
from typing import Dict, List, Any

def infer_trades(plan_features: Dict[str, Any], fixtures_rules_path: str = "data/fixtures.rules.yaml", vendor_map_path: str = "data/taxonomy/vendor_map.yaml") -> List[Dict[str, Any]]:
    # Simple heuristics based on text tokens
    text = plan_features.get('full_text', '').lower()
    sheet_titles = plan_features.get('sheet_titles', [])
    sheet_text = ' '.join(sheet_titles).lower()

    # Keywords for trades
    trade_keywords = {
        'concrete': ['concrete', 'foundation', 'slab', 'footing', 'stem wall'],
        'framing': ['framing', 'stud', 'wall', 'joist', 'rafter'],
        'roofing': ['roof', 'shingle', 'tile roof', 'underlayment'],
        'plumbing': ['plumbing', 'pipe', 'drain', 'fixture'],
        'electrical': ['electrical', 'wire', 'outlet', 'panel'],
        'hvac': ['hvac', 'air handler', 'duct', 'furnace'],
        'drywall': ['drywall', 'sheetrock', 'gypsum'],
        'paint': ['paint', 'primer', 'finish'],
        'flooring': ['flooring', 'tile', 'carpet', 'hardwood'],
        'windows': ['window', 'door', 'glazing'],
        'insulation': ['insulation', 'batt', 'blown'],
        'sitework': ['sitework', 'grading', 'driveway']
    }

    inferred = []
    for trade, keywords in trade_keywords.items():
        hits = sum(1 for kw in keywords if kw in text or kw in sheet_text)
        if hits > 0:
            confidence = min(1.0, hits / len(keywords) * 0.5 + 0.5)  # simple blend
            signals = [{'type': 'keyword_hit', 'value': kw} for kw in keywords if kw in text or kw in sheet_text]
            items = [{'item': f'{trade}_default', 'confidence': confidence, 'signals': signals}]
            inferred.append({'trade': trade, 'items': items})

    return inferred
