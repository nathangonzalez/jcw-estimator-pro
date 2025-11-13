#!/usr/bin/env python3
"""
R2.5 Requirements Generation - Auto-generate requirements from UAT failures
"""

import json
import os
import sys
from pathlib import Path

def load_uat_status():
    """Load UAT status from JSON file."""
    status_file = "output/R25_UAT_STATUS.json"
    if not os.path.exists(status_file):
        print(f"UAT status file not found: {status_file}", file=sys.stderr)
        return None

    try:
        with open(status_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load UAT status: {e}", file=sys.stderr)
        return None

def generate_requirements(uat_status):
    """Generate requirements from UAT failures."""
    failures = uat_status.get('failures', [])
    requirements = []
    req_counter = 1

    # Priority mapping based on area
    priority_map = {
        'Estimate': 'HIGH',
        'Interactive': 'HIGH',
        'Takeoff': 'MEDIUM',
        'UI': 'MEDIUM',
        'Calibration': 'LOW'
    }

    for failure in failures:
        test_name = failure.get('test', 'Unknown')
        error = failure.get('error', 'Unknown error')
        area = failure.get('area', 'Unknown')

        # Map test to requirement based on error patterns
        if 'Cannot find module' in error and 'quantities.sample.json' in error:
            req_id = f"RQ-LYNN-{req_counter:03d}"
            req = {
                'id': req_id,
                'area': 'Estimate',
                'priority': 'HIGH',
                'title': 'Missing quantities.sample.json file',
                'given': 'UAT test attempts to load quantities data',
                'when': 'Estimate API is called with sample data',
                'then': 'quantities.sample.json file should exist and be loadable',
                'acceptance_test': f'UAT R2 - Estimate API ({test_name})',
                'failing_test': test_name,
                'suggested_fix': 'Create data/quantities.sample.json with valid takeoff quantities structure'
            }

        elif 'Expected: 200 Received: 500' in error and 'Assess endpoint' in test_name:
            req_id = f"RQ-LYNN-{req_counter:03d}"
            req = {
                'id': req_id,
                'area': 'Interactive',
                'priority': 'HIGH',
                'title': 'Assess endpoint returns 500 error',
                'given': 'Valid PDF path and project_id are provided',
                'when': 'POST /v1/interactive/assess is called',
                'then': 'Should return 200 with trades_inferred and questions_ref',
                'acceptance_test': f'UAT R2 Interactive - Assess endpoint ({test_name})',
                'failing_test': test_name,
                'suggested_fix': 'Debug assess endpoint logic, check PDF processing and trade inference'
            }

        elif 'Expected: 200 Received: 500' in error and 'Estimate interactive mode' in test_name:
            req_id = f"RQ-LYNN-{req_counter:03d}"
            req = {
                'id': req_id,
                'area': 'Estimate',
                'priority': 'HIGH',
                'title': 'Interactive estimate mode returns 500 error',
                'given': 'Valid project parameters and mode=interactive',
                'when': 'POST /v1/estimate is called with interactive mode',
                'then': 'Should return 200 with version and total_cost fields',
                'acceptance_test': f'UAT R2 Interactive - Estimate interactive mode ({test_name})',
                'failing_test': test_name,
                'suggested_fix': 'Implement interactive mode logic in estimate endpoint'
            }

        elif 'toHaveLength(expected)' in error and 'QnA endpoint processes answers' in test_name:
            req_id = f"RQ-LYNN-{req_counter:03d}"
            req = {
                'id': req_id,
                'area': 'Interactive',
                'priority': 'HIGH',
                'title': 'QnA endpoint not processing answers correctly',
                'given': 'Valid answers array is provided to QnA endpoint',
                'when': 'POST /v1/interactive/qna is called with answers',
                'then': 'Should process answers and return answered array with correct length',
                'acceptance_test': f'UAT Interactive - QnA endpoint processes answers ({test_name})',
                'failing_test': test_name,
                'suggested_fix': 'Fix answer processing logic in QnA endpoint, ensure answered field is populated'
            }

        elif 'toBeTruthy()' in error and 'estimate' in test_name.lower():
            req_id = f"RQ-LYNN-{req_counter:03d}"
            req = {
                'id': req_id,
                'area': 'Estimate',
                'priority': 'HIGH',
                'title': 'Estimate endpoint not returning success response',
                'given': 'Valid M01 quantities body is provided',
                'when': 'POST /v1/estimate is called',
                'then': 'Should return successful response with v0-shaped cost data',
                'acceptance_test': f'POST /v1/estimate (M01 body) returns v0-shaped response ({test_name})',
                'failing_test': test_name,
                'suggested_fix': 'Fix estimate endpoint to handle M01 body format and return proper response'
            }

        elif 'toBeVisible()' in error and 'Upload PDF Blueprint' in error:
            req_id = f"RQ-LYNN-{req_counter:03d}"
            req = {
                'id': req_id,
                'area': 'UI',
                'priority': 'MEDIUM',
                'title': 'UI upload interface not displaying correctly',
                'given': 'User navigates to upload page',
                'when': 'Upload PDF Blueprint interface loads',
                'then': 'Upload PDF Blueprint text should be visible',
                'acceptance_test': f'Upload to Takeoff to Estimate to Interactive (video) ({test_name})',
                'failing_test': test_name,
                'suggested_fix': 'Fix UI upload interface, ensure proper element visibility and text content'
            }

        else:
            # Generic requirement for unhandled failures
            req_id = f"RQ-LYNN-{req_counter:03d}"
            req = {
                'id': req_id,
                'area': area,
                'priority': priority_map.get(area, 'MEDIUM'),
                'title': f'Fix {test_name} test failure',
                'given': 'Test conditions are met',
                'when': f'{test_name} executes',
                'then': 'Test should pass without errors',
                'acceptance_test': test_name,
                'failing_test': test_name,
                'suggested_fix': f'Investigate and fix: {error}'
            }

        requirements.append(req)
        req_counter += 1

    return requirements

def write_requirements_markdown(requirements):
    """Write requirements to markdown file."""
    output_file = "output/LYNN_REQUIREMENTS_R2.md"

    # Group by area and sort by priority
    priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    area_order = {'Estimate': 0, 'Interactive': 1, 'Takeoff': 2, 'UI': 3, 'Calibration': 4}

    sorted_reqs = sorted(requirements,
                        key=lambda x: (area_order.get(x['area'], 99),
                                      priority_order.get(x['priority'], 99),
                                      x['id']))

    with open(output_file, 'w') as f:
        f.write("# Lynn Full-Test Requirements - R2\n\n")
        f.write("Auto-generated from UAT test failures.\n\n")
        f.write(f"**Total Requirements:** {len(requirements)}\n\n")

        current_area = None
        for req in sorted_reqs:
            area = req['area']
            if area != current_area:
                if current_area is not None:
                    f.write("\n")
                f.write(f"## {area}\n\n")
                current_area = area

            f.write(f"### {req['id']}: {req['title']}\n\n")
            f.write(f"**Priority:** {req['priority']}\n\n")
            f.write("**Given / When / Then:**\n")
            f.write(f"- **Given:** {req['given']}\n")
            f.write(f"- **When:** {req['when']}\n")
            f.write(f"- **Then:** {req['then']}\n\n")
            f.write(f"**Acceptance Test:** {req['acceptance_test']}\n\n")
            f.write(f"**Suggested Fix:** {req['suggested_fix']}\n\n")
            f.write("---\n\n")

    print(f"Requirements written to {output_file}")

def write_requirements_json(requirements):
    """Write requirements to JSON file."""
    output_file = "output/LYNN_REQUIREMENTS_R2.json"

    with open(output_file, 'w') as f:
        json.dump(requirements, f, indent=2)

    print(f"Requirements JSON written to {output_file}")

def main():
    """Main requirements generation function."""
    uat_status = load_uat_status()
    if not uat_status:
        return 1

    requirements = generate_requirements(uat_status)

    write_requirements_markdown(requirements)
    write_requirements_json(requirements)

    print(f"Generated {len(requirements)} requirements from {len(uat_status.get('failures', []))} failures")
    return 0

if __name__ == "__main__":
    sys.exit(main())
