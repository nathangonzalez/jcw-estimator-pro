from typing import List, Dict, Any, Optional

def make_questions(inferred: List[Dict[str, Any]], takeoff_quantities: Optional[Dict[str, Any]], thresholds: Dict[str, Any]) -> List[Dict[str, Any]]:
    questions = []
    confidence_min = thresholds.get('confidence_min', 0.55)
    missing_required = thresholds.get('missing_required_items', [])

    # Questions for low confidence
    for trade_data in inferred:
        trade = trade_data['trade']
        for item in trade_data['items']:
            if item['confidence'] < confidence_min:
                questions.append({
                    'id': f'{trade}_{item["item"]}_confidence',
                    'trade': trade,
                    'item': item['item'],
                    'severity': 'normal',
                    'rationale': f'Low confidence ({item["confidence"]:.2f}) in inferred item',
                    'prompt': f'What type of {item["item"]} for {trade}?',
                    'suggested_answers': [{'key': 'default', 'label': 'Use default'}, {'key': 'skip', 'label': 'Skip this item'}]
                })

    # Questions for missing required items
    inferred_items = {item['item'] for trade_data in inferred for item in trade_data['items']}
    for required in missing_required:
        if required not in inferred_items:
            questions.append({
                'id': f'missing_{required}',
                'severity': 'critical',
                'rationale': f'Required item {required} not inferred',
                'prompt': f'Is {required} included in the project?',
                'suggested_answers': [{'key': 'yes', 'label': 'Yes'}, {'key': 'no', 'label': 'No'}]
            })

    # Hardcoded critical questions
    critical_questions = [
        {
            'id': 'roofing_material',
            'trade': 'roofing',
            'severity': 'critical',
            'rationale': 'Roofing material significantly impacts cost',
            'prompt': 'What roofing material?',
            'suggested_answers': [{'key': 'shingle', 'label': 'Shingle'}, {'key': 'metal', 'label': 'Metal'}, {'key': 'tile', 'label': 'Tile'}]
        },
        {
            'id': 'foundation_type',
            'trade': 'concrete',
            'severity': 'critical',
            'rationale': 'Foundation type affects structural cost',
            'prompt': 'What foundation type?',
            'suggested_answers': [{'key': 'slab', 'label': 'Slab-on-grade'}, {'key': 'crawl', 'label': 'Crawl space'}, {'key': 'basement', 'label': 'Basement'}]
        },
        {
            'id': 'window_tier',
            'trade': 'windows',
            'severity': 'critical',
            'rationale': 'Window quality affects energy and cost',
            'prompt': 'What window tier?',
            'suggested_answers': [{'key': 'economy', 'label': 'Economy'}, {'key': 'standard', 'label': 'Standard'}, {'key': 'premium', 'label': 'Premium'}]
        }
    ]

    questions.extend(critical_questions[:5])  # limit to 5 total

    return questions
