#!/usr/bin/env python3
"""
R2.5 Demo Analytics - Trend Update

Appends run metrics to history and rebuilds trend aggregates.
"""

import json
import os
import sys
from collections import defaultdict, Counter
from pathlib import Path

def load_history():
    """Load existing history.jsonl file."""
    history_path = "output/metrics/history.jsonl"
    if not os.path.exists(history_path):
        return []

    history = []
    try:
        with open(history_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    history.append(json.loads(line))
    except Exception as e:
        print(f"Failed to load history: {e}", file=sys.stderr)
        return []

    return history

def append_to_history(run_metrics):
    """Append current run to history."""
    history_path = "output/metrics/history.jsonl"
    try:
        with open(history_path, 'a') as f:
            f.write(json.dumps(run_metrics) + '\n')
    except Exception as e:
        print(f"Failed to append to history: {e}", file=sys.stderr)
        with open("output/METRICS_TREND_DIAGNOSE.md", 'w') as f:
            f.write("# Trend Update Failed\n\n- Could not append to history.jsonl\n- Check file permissions\n")
        return False
    return True

def calculate_trends(history):
    """Calculate trend metrics from last 10 runs."""
    if not history:
        return {}

    # Get last 10 runs
    recent = history[-10:]

    # Pass rate trend
    pass_rates = []
    for run in recent:
        tests = run.get('tests', {})
        total = tests.get('total', 0)
        passed = tests.get('passed', 0)
        if total > 0:
            pass_rates.append(passed / total)

    # Average duration
    avg_durations = [run.get('durations', {}).get('p95_ms', 0) for run in recent]
    avg_duration = sum(avg_durations) / len(avg_durations) if avg_durations else 0

    # Flakiness: tests that changed status 2+ times
    test_statuses = defaultdict(list)
    for run in recent:
        for test in run.get('tests', {}).get('byFile', []):
            # Simplified: just track pass/fail counts
            pass

    flaky_tests = []
    # Would need more complex logic to track individual test status changes

    # Video coverage trend
    video_clips = [run.get('video', {}).get('clips', 0) for run in recent]
    video_bytes = [run.get('video', {}).get('total_bytes', 0) for run in recent]

    # Reel completeness
    reel_completes = []
    for run in recent:
        reel = run.get('reel', {})
        duration_ok = reel.get('duration_s', 0) >= 10
        size_ok = reel.get('bytes', 0) >= 300000
        reel_completes.append(duration_ok and size_ok)

    return {
        'pass_rate_trend': pass_rates,
        'avg_duration_ms': avg_duration,
        'flaky_tests': flaky_tests,
        'video_coverage_trend': {
            'clips_per_run': video_clips,
            'bytes_per_run': video_bytes
        },
        'reel_completeness_rate': sum(reel_completes) / len(reel_completes) if reel_completes else 0
    }

def find_top_slow_tests(history, n=5):
    """Find top N slowest tests by average duration."""
    test_durations = defaultdict(list)

    for run in history[-5:]:  # Last 5 runs
        # This is simplified - would need to match tests by name
        pass

    # Would aggregate by test name and calculate averages
    return []

def build_summary(history):
    """Build summary.json with trends and top items."""
    trends = calculate_trends(history)
    top_slow = find_top_slow_tests(history)

    summary = {
        'total_runs': len(history),
        'last_run': history[-1] if history else None,
        'trends': trends,
        'top_slow_tests': top_slow
    }

    try:
        with open("output/metrics/summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
    except Exception as e:
        print(f"Failed to write summary: {e}", file=sys.stderr)
        with open("output/METRICS_TREND_DIAGNOSE.md", 'w') as f:
            f.write("# Trend Update Failed\n\n- Could not write summary.json\n- Check file permissions\n")
        return False

    return True

def main():
    """Main trend update function."""
    # Load current run metrics
    run_path = "output/metrics/run.json"
    if not os.path.exists(run_path):
        print("Run metrics not found", file=sys.stderr)
        with open("output/METRICS_TREND_DIAGNOSE.md", 'w') as f:
            f.write("# Trend Update Failed\n\n- run.json not found\n- Run metrics_collect.py first\n")
        return 1

    try:
        with open(run_path, 'r') as f:
            run_metrics = json.load(f)
    except Exception as e:
        print(f"Failed to load run metrics: {e}", file=sys.stderr)
        return 1

    # Load and update history
    history = load_history()
    if not append_to_history(run_metrics):
        return 1

    # Rebuild summary
    if not build_summary(history + [run_metrics]):
        return 1

    print("Trend update completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
