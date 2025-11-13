#!/usr/bin/env python3
"""
R2.5 Demo Analytics - Dashboard Builder

Generates offline HTML dashboard with metrics visualization.
"""

import json
import os
import sys
from datetime import datetime

def load_data():
    """Load summary and latest run data."""
    summary_path = "output/metrics/summary.json"
    run_path = "output/metrics/run.json"

    if not os.path.exists(summary_path) or not os.path.exists(run_path):
        print("Required data files not found", file=sys.stderr)
        with open("output/METRICS_DASHBOARD_DIAGNOSE.md", 'w') as f:
            f.write("# Dashboard Build Failed\n\n- summary.json or run.json not found\n- Run collection and trend update first\n")
        return None, None

    try:
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        with open(run_path, 'r') as f:
            run = json.load(f)
        return summary, run
    except Exception as e:
        print(f"Failed to load data: {e}", file=sys.stderr)
        return None, None

def generate_chart_data(summary):
    """Generate JavaScript data for charts."""
    trends = summary.get('trends', {})

    # Pass rate trend (last 10 runs)
    pass_rates = trends.get('pass_rate_trend', [])
    pass_rate_data = ', '.join(f'{rate:.2f}' for rate in pass_rates)

    # Video clips trend
    video_trend = trends.get('video_coverage_trend', {})
    clips_data = ', '.join(str(x) for x in video_trend.get('clips_per_run', []))

    return f"""
const passRateData = [{pass_rate_data}];
const videoClipsData = [{clips_data}];
"""

def generate_html(summary, run):
    """Generate the complete HTML dashboard."""
    chart_data = generate_chart_data(summary)

    # Extract key metrics
    tests = run.get('tests', {})
    total_tests = tests.get('total', 0)
    passed_tests = tests.get('passed', 0)
    failed_tests = tests.get('failed', 0)

    durations = run.get('durations', {})
    p95_duration = durations.get('p95_ms', 0)

    video = run.get('video', {})
    video_clips = video.get('clips', 0)

    reel = run.get('reel', {})
    reel_exists = reel.get('exists', False)
    reel_duration = reel.get('duration_s', 0)
    reel_bytes = reel.get('bytes', 0)

    interactive = run.get('interactive', {})
    assess_ok = interactive.get('assess_ok', False)
    qna_ok = interactive.get('qna_ok', False)

    finance = run.get('finance', {})
    overlay_applied = finance.get('overlay_applied', False)

    # Status badges
    reel_status = "✅ OK" if (reel_duration >= 10 and reel_bytes >= 300000) else "⚠️ Needs Attention"
    interactive_status = "✅ OK" if (assess_ok and qna_ok) else "⚠️ Needs Attention"
    finance_status = "✅ Applied" if overlay_applied else "⏳ Not Available"

    # Pass rate percentage
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JCW Estimator - Demo Analytics Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2em; font-weight: bold; margin-bottom: 5px; }}
        .metric-label {{ color: #666; font-size: 0.9em; }}
        .status-good {{ color: #28a745; }}
        .status-warning {{ color: #ffc107; }}
        .status-bad {{ color: #dc3545; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .table-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }}
        .badge-good {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-bad {{ background: #f8d7da; color: #721c24; }}
        .links {{ margin-top: 20px; }}
        .links a {{ display: inline-block; margin-right: 15px; color: #007bff; text-decoration: none; }}
        .links a:hover {{ text-decoration: underline; }}
        canvas {{ max-width: 100%; height: 300px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 JCW Estimator - Demo Analytics Dashboard</h1>
            <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | SHA: {run.get('git', {}).get('sha', 'unknown')}</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value status-good">{pass_rate:.1f}%</div>
                <div class="metric-label">Pass Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{passed_tests}/{total_tests}</div>
                <div class="metric-label">Tests Passed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value status-bad">{failed_tests}</div>
                <div class="metric-label">Tests Failed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{p95_duration:.0f}ms</div>
                <div class="metric-label">P95 Duration</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{video_clips}</div>
                <div class="metric-label">Video Clips</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{reel_duration:.1f}s</div>
                <div class="metric-label">Reel Duration</div>
            </div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">
                    <span class="badge {'badge-good' if reel_exists and reel_duration >= 10 and reel_bytes >= 300000 else 'badge-warning'}">{reel_status}</span>
                </div>
                <div class="metric-label">Reel Status</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">
                    <span class="badge {'badge-good' if assess_ok and qna_ok else 'badge-warning'}">{interactive_status}</span>
                </div>
                <div class="metric-label">Interactive APIs</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">
                    <span class="badge {'badge-good' if overlay_applied else 'badge-warning'}">{finance_status}</span>
                </div>
                <div class="metric-label">Finance Overlay</div>
            </div>
        </div>

        <div class="chart-container">
            <h3>📈 Pass Rate Trend (Last 10 Runs)</h3>
            <canvas id="passRateChart"></canvas>
        </div>

        <div class="chart-container">
            <h3>🎥 Video Coverage Trend</h3>
            <canvas id="videoChart"></canvas>
        </div>

        <div class="table-container">
            <h3>🧪 Latest Test Results</h3>
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>File</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Add test results (simplified - would need to load from tests.csv)
    test_results = []
    tests_csv = "output/metrics/tests.csv"
    if os.path.exists(tests_csv):
        import csv
        with open(tests_csv, 'r') as f:
            reader = csv.DictReader(f)
            test_results = list(reader)[:10]  # Show first 10

    for test in test_results:
        status_emoji = {"passed": "✅", "failed": "❌", "skipped": "⏭️"}.get(test.get('status', 'unknown'), "❓")
        duration = f"{int(test.get('duration_ms', 0))}ms"
        html += f"""
                    <tr>
                        <td>{test.get('name', 'Unknown')}</td>
                        <td>{status_emoji} {test.get('status', 'unknown')}</td>
                        <td>{duration}</td>
                        <td>{test.get('file', 'unknown')}</td>
                    </tr>"""

    html += """
                </tbody>
            </table>
        </div>

        <div class="links">
            <h3>🔗 Related Links</h3>
            <a href="playwright-report/index.html">📊 Playwright Report</a>
            <a href="uat/UAT_REEL_V2.mp4">🎬 Demo Reel V2</a>
            <a href="uat/UAT_ANNOTATED.mp4">📹 Annotated Video</a>
            <a href="metrics/run.json">📄 Latest Run JSON</a>
            <a href="metrics/summary.json">📈 Trends Summary</a>
        </div>
    </div>

    <script src="data:text/javascript;base64,ZnVuY3Rpb24gZHJhd0NoYXJ0KGNhbnZhcywgZGF0YSwgbGFiZWwsIGNvbG9yKSB7CiAgICBjb25zdCBjdHggPSBjYW52YXMuZ2V0Q29udGV4dCgyZCk7CiAgICBjb25zdCB3aWR0aCA9IGNhbnZhcy53aWR0aDsKICAgIGNvbnN0IGhlaWdodCA9IGNhbnZhcy5oZWlnaHQ7CiAgICBjb25zdCBtYXhWYWx1ZSA9IE1hdGgubWF4KC4uLmRhdGEpOwogICAgY29uc3QgbWluVmFsdWUgPSBNYXRoLm1pbihNYXRoLm1pbihkYXRhLmZpbHRlcih4ID0+IHggIT09IG51bGwpKSwgMCk7CiAgICBjb25zdCByYW5nZSA9IG1heFZhbHVlIC0gbWluVmFsdWUgfHwgMTsKCiAgICAvLyBEcmF3IGJhY2tncm91bmQKICAgIGN0eC5maWxsU3R5bGUgPSAnI2Y4ZjlmYSc7CiAgICBjdHguZmlsbFJlY3QoMCwgMCwgd2lkdGgsIGhlaWdodCk7CgogICAgLy8gRHJhdyBsaW5lCiAgICBjdHguYmVnaW5QYXRoKCk7CiAgICBjdHguU3Ryb2tlU3R5bGUgPSBjb2xvcjsKICAgIGN0eC5saW5lV2lkdGggPSAyOwogICAgY29uc3Qgc3RlcCA9IHdpZHRoIC8gKGRhdGEubGVuZ3RoIC0gMSk7CiAgICBmb3IgKGxldCBpID0gMDsgaSA8IGRhdGEubGVuZ3RoOyBpKyspIHsKICAgICAgICBjb25zdCB4ID0gaSAqIHN0ZXA7CiAgICAgICAgY29uc3QgdmFsdWUgPSBkYXRhW2ldOwogICAgICAgIGNvbnN0IHkgPSBoZWlnaHQgLSAoKHZhbHVlIC0gbWluVmFsdWUpIC8gcmFuZ2UgKiBoZWlnaHQgKiAwLjgpOwogICAgICAgIGlmIChpID09IDApIHsKICAgICAgICAgICAgY3R4Lm1vdmVUbygxMCwgeSk7CiAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgY3R4LmxpbmVUbygxMCArIHgsIHkpOwogICAgICAgIH0KICAgIH0KICAgIGN0eC5zdHJva2UoKTsKCiAgICAvLyBEcmF3IHBvaW50cwogICAgZm9yIChsZXQgaSA9IDA7IGkgPCBkYXRhLmxlbmd0aDsgaSsrKSB7CiAgICAgICAgY29uc3QgeCA9IDEwICsgaSAqIHN0ZXA7CiAgICAgICAgY29uc3QgdmFsdWUgPSBkYXRhW2ldOwogICAgICAgIGNvbnN0IHkgPSBoZWlnaHQgLSAoKHZhbHVlIC0gbWluVmFsdWUpIC8gcmFuZ2UgKiBoZWlnaHQgKiAwLjgpOwogICAgICAgIGN0eC5iZWdpblBhdGgoKTsKICAgICAgICBjdHguYXJjKHgsIHksIDMsIDAsIDJfTWF0aC5QSSk7CiAgICAgICAgY3R4LmZpbGwoKTsKICAgIH0KfQoKLy8gUGFzcyByYXRlIGNoYXJ0CmNvbnN0IHBhc3NSYXRlQ2FudmFzID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoJ3Bhc3NSYXRlQ2hhcnQnKTsKaWYgKHBhc3NSYXRlQ2FudmFzKSB7CiAgICBkcmF3Q2hhcnQocGFzc1JhdGVDYW52YXMsIHBhc3NSYXRlRGF0YSwgJ1Bhc3MgUmF0ZScsICcjMjhhNzQ1Jyk7Cn0KCi8vIFZpZGVvIGNsaXBzIGNoYXJ0CmNvbnN0IHZpZGVvQ2FudmFzID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoJ3ZpZGVvQ2hhcnQnKTsKaWYgKHZpZGVvQ2FudmFzKSB7CiAgICBkcmF3Q2hhcnQodmlkZW9DYW52YXMsIHZpZGVvQ2xpcHNEYXRhLCAnVmlkZW8gQ2xpcHMnLCAnIzY2N0VFQScpOwp9"></script>

    <script>
        {chart_data}
    </script>
</body>
</html>"""

    return html

def main():
    """Main dashboard build function."""
    summary, run = load_data()
    if not summary or not run:
        return 1

    html = generate_html(summary, run)

    try:
        with open("output/metrics/dashboard.html", 'w', encoding='utf-8') as f:
            f.write(html)
    except Exception as e:
        print(f"Failed to write dashboard: {e}", file=sys.stderr)
        with open("output/METRICS_DASHBOARD_DIAGNOSE.md", 'w') as f:
            f.write("# Dashboard Build Failed\n\n- Could not write dashboard.html\n- Check file permissions\n")
        return 1

    print("Dashboard built successfully: output/metrics/dashboard.html")
    return 0

if __name__ == "__main__":
    sys.exit(main())
