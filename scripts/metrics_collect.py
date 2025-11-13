#!/usr/bin/env python3
"""
R2.5 Demo Analytics - Metrics Collection

Parses UAT report JSON and extracts comprehensive metrics for dashboard.
"""

import json
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
import subprocess

def get_git_info():
    """Get current git SHA and branch."""
    try:
        sha = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
        branch = subprocess.check_output(['git', 'branch', '--show-current']).decode().strip()
        return sha, branch
    except:
        return "unknown", "unknown"

def parse_uat_report(report_path):
    """Parse Playwright JSON report and extract test metrics."""
    if not os.path.exists(report_path):
        return None

    try:
        with open(report_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to parse {report_path}: {e}", file=sys.stderr)
        return None

    tests = []
    suites = {}

    for suite in data.get('suites', []):
        suite_file = suite.get('file', 'unknown')
        suite_passed = 0
        suite_failed = 0
        suite_duration = 0

        for spec in suite.get('specs', []):
            spec_title = spec.get('title', 'unknown')

            for test in spec.get('tests', []):
                result = test.get('results', [{}])[0]
                status = result.get('status', 'unknown')
                duration = result.get('duration', 0)

                tests.append({
                    'name': spec_title,
                    'status': status,
                    'duration_ms': duration,
                    'file': suite_file
                })

                suite_duration += duration
                if status == 'passed':
                    suite_passed += 1
                elif status == 'failed':
                    suite_failed += 1

        suites[suite_file] = {
            'passed': suite_passed,
            'failed': suite_failed,
            'duration_ms': suite_duration
        }

    # Calculate summary stats
    total = len(tests)
    passed = sum(1 for t in tests if t['status'] == 'passed')
    failed = sum(1 for t in tests if t['status'] == 'failed')
    skipped = sum(1 for t in tests if t['status'] == 'skipped')

    # Duration percentiles
    durations = sorted([t['duration_ms'] for t in tests if t['duration_ms'] > 0])
    if durations:
        p50 = durations[len(durations) // 2]
        p95 = durations[int(len(durations) * 0.95)]
        max_dur = max(durations)
    else:
        p50 = p95 = max_dur = 0

    return {
        'total': total,
        'passed': passed,
        'failed': failed,
        'skipped': skipped,
        'byFile': list(suites.values()),
        'durations': {
            'p50_ms': p50,
            'p95_ms': p95,
            'max_ms': max_dur
        }
    }, tests, list(suites.items())

def collect_video_metrics(uat_dir):
    """Count video files and estimate total duration/size."""
    video_dir = Path(uat_dir) / ".." / "playwright-artifacts"
    clips = 0
    total_bytes = 0
    total_duration = 0

    if video_dir.exists():
        for webm in video_dir.rglob("video.webm"):
            clips += 1
            try:
                stat = webm.stat()
                total_bytes += stat.st_size
                # Rough estimate: assume 25fps, but we don't probe each file
            except:
                pass

    return {
        'clips': clips,
        'total_duration_s': total_duration,
        'total_bytes': total_bytes
    }

def collect_reel_metrics(reel_path):
    """Get reel file stats."""
    if not os.path.exists(reel_path):
        return {'exists': False, 'path': reel_path, 'duration_s': 0, 'bytes': 0}

    try:
        stat = os.stat(reel_path)
        # Try to get duration from ffprobe if available
        duration = 0
        try:
            result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                                   'format=duration', '-of', 'default=nw=1:nk=1', reel_path],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
        except:
            pass

        return {
            'exists': True,
            'path': reel_path,
            'duration_s': duration,
            'bytes': stat.st_size
        }
    except:
        return {'exists': False, 'path': reel_path, 'duration_s': 0, 'bytes': 0}

def collect_interactive_metrics():
    """Check interactive endpoints status."""
    log_path = "output/INTERACTIVE/INTERACTIVE_RUN.log"
    assess_ok = False
    qna_ok = False

    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                content = f.read().lower()
                assess_ok = '200' in content and 'assess' in content
                qna_ok = ('200' in content or '422' in content) and 'qna' in content
        except:
            pass

    return {'assess_ok': assess_ok, 'qna_ok': qna_ok}

def collect_finance_metrics():
    """Get finance overlay status."""
    forecast_path = "output/finance/forecast.json"
    overlay_applied = False
    runway_days = None

    if os.path.exists(forecast_path):
        try:
            with open(forecast_path, 'r') as f:
                data = json.load(f)
                runway_days = data.get('runway_months')
                if runway_days:
                    runway_days = runway_days * 30  # Convert months to days
        except:
            pass

    return {'overlay_applied': overlay_applied, 'runway_days': runway_days}

def main():
    """Main collection function."""
    output_dir = Path("output/metrics")
    output_dir.mkdir(exist_ok=True)

    # Collect all metrics
    timestamp = datetime.now().isoformat()
    sha, branch = get_git_info()

    # Test metrics
    test_metrics, tests, suites = parse_uat_report("output/uat-report.json")
    if not test_metrics:
        print("Failed to parse UAT report", file=sys.stderr)
        with open("output/METRICS_COLLECT_DIAGNOSE.md", 'w') as f:
            f.write("# Metrics Collection Failed\n\n- UAT report not found or invalid\n- Check output/uat-report.json\n")
        return 1

    # Video metrics
    video_metrics = collect_video_metrics("output/uat")

    # Reel metrics (try V3 first, then V2)
    reel_path = "output/uat/UAT_REEL_V3.mp4"
    if not os.path.exists(reel_path):
        reel_path = "output/uat/UAT_REEL_V2.mp4"
    reel_metrics = collect_reel_metrics(reel_path)

    # Interactive and finance
    interactive_metrics = collect_interactive_metrics()
    finance_metrics = collect_finance_metrics()

    # Build run metrics
    run_metrics = {
        'timestamp': timestamp,
        'git': {'sha': sha, 'branch': branch},
        'tests': test_metrics,
        'durations': test_metrics['durations'],
        'video': video_metrics,
        'reel': reel_metrics,
        'interactive': interactive_metrics,
        'finance': finance_metrics
    }

    # Write run.json
    with open("output/metrics/run.json", 'w') as f:
        json.dump(run_metrics, f, indent=2)

    # Write tests.csv
    with open("output/metrics/tests.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'status', 'duration_ms', 'file'])
        writer.writeheader()
        for test in tests:
            writer.writerow(test)

    # Write suites.csv
    with open("output/metrics/suites.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['file', 'passed', 'failed', 'duration_ms'])
        writer.writeheader()
        for file_name, metrics in suites:
            row = {'file': file_name, **metrics}
            writer.writerow(row)

    # Write artifacts info
    artifacts = {
        'reel_bytes': reel_metrics['bytes'],
        'reel_duration_s': reel_metrics['duration_s'],
        'video_clips': video_metrics['clips'],
        'video_bytes': video_metrics['total_bytes']
    }
    with open("output/metrics/run_artifacts.json", 'w') as f:
        json.dump(artifacts, f, indent=2)

    print("Metrics collected successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
