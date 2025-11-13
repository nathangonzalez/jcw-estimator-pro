# JCW Estimator - Demo Analytics Dashboard

This directory contains analytics and metrics for demo runs, providing insights into test performance, trends, and system health.

## Files Overview

### Data Files
- **`run.json`** - Latest run metrics (test results, durations, video stats, etc.)
- **`summary.json`** - Aggregated trends from last 10 runs
- **`history.jsonl`** - Complete history of all runs (one JSON per line)
- **`tests.csv`** - Individual test results with status and duration
- **`suites.csv`** - Test suite summaries by file

### Generated Assets
- **`dashboard.html`** - Interactive analytics dashboard (open in browser)
- **`run_artifacts.json`** - Reel and video file statistics

## Dashboard Features

### 📊 Key Metrics
- **Pass Rate**: Overall test success percentage
- **Test Counts**: Passed/failed/total breakdown
- **Performance**: P95 duration percentiles
- **Video Coverage**: Number of recorded test clips
- **Reel Status**: Duration and file size validation

### 📈 Trend Charts
- **Pass Rate Trend**: Last 10 runs success rate over time
- **Video Coverage**: Clips recorded per run trend

### 📋 Test Results Table
- Latest run individual test results
- Status indicators (✅ passed, ❌ failed, ⏭️ skipped)
- Duration and file information

### 🔗 Quick Links
- Playwright HTML report
- Demo reel videos
- Raw JSON data files

## Usage

### View Dashboard
```bash
# When serving output
open http://127.0.0.1:8000/output/metrics/dashboard.html

# Or open directly in browser
start output/metrics/dashboard.html
```

### Manual Generation
```bash
# Full pipeline
pwsh -File scripts/demo_metrics.ps1

# Individual steps
python scripts/metrics_collect.py
python scripts/metrics_trend_update.py
python scripts/metrics_dashboard_build.py
```

## Metrics Schema

### Run Metrics (run.json)
```json
{
  "timestamp": "ISO-8601",
  "git": {"sha": "short", "branch": "master"},
  "tests": {
    "total": 21, "passed": 13, "failed": 7, "skipped": 1,
    "durations": {"p50_ms": 100, "p95_ms": 500, "max_ms": 2000}
  },
  "video": {"clips": 2, "total_bytes": 150000},
  "reel": {"exists": true, "duration_s": 10.5, "bytes": 16928},
  "interactive": {"assess_ok": false, "qna_ok": false},
  "finance": {"overlay_applied": false}
}
```

### Trend Summary (summary.json)
```json
{
  "total_runs": 5,
  "trends": {
    "pass_rate_trend": [0.62, 0.71, 0.65, 0.81, 0.76],
    "avg_duration_ms": 450,
    "video_coverage_trend": {"clips_per_run": [2, 3, 1, 2, 2]}
  }
}
```

## Status Badges

- **✅ OK**: Meets all requirements (duration ≥10s, size ≥300KB)
- **⚠️ Needs Attention**: Below thresholds or has issues
- **⏳ Not Available**: Feature not configured or data missing

## Automation

The dashboard is automatically generated as part of the demo pipeline:

1. **Demo Run** → UAT tests execute
2. **Video Generation** → Reel created
3. **Metrics Collection** → Parse results and stats
4. **Trend Update** → Append to history, rebuild aggregates
5. **Dashboard Build** → Generate HTML with charts and tables
6. **HTTP Serve** → Dashboard available at `/output/metrics/dashboard.html`

## Troubleshooting

### Dashboard Not Loading
- Check `output/metrics/dashboard.html` exists
- Ensure HTTP server is running (`scripts/serve_output.ps1`)
- Verify browser supports inline JavaScript

### Missing Data
- Run `python scripts/metrics_collect.py` to regenerate
- Check `output/uat-report.json` exists from UAT run
- Verify `output/uat/UAT_REEL_V2.mp4` was created

### Charts Not Showing
- Dashboard uses inline JavaScript (no external dependencies)
- Check browser console for JavaScript errors
- Data arrays should be populated in the HTML source

## Data Retention

- **`history.jsonl`**: Complete run history (grows over time)
- **`summary.json`**: Rolling aggregates (last 10 runs)
- **CSV files**: Latest run test data
- **HTML dashboard**: Regenerated on each run

Clean up old data by truncating `history.jsonl` if needed.
