"""
Cashflow utilities (v0)
- Load flat estimate lines CSV (aligned with benchmarking CSV shape)
- Generate quick cashflow from estimate (simple linear S-curve weekly)
- Generate cashflow from schedule (allocate totals across dated tasks; weekly series)
No external calls; read-only from local files.
"""
from __future__ import annotations

import csv
import os
import math
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional


ESTIMATE_COLS = [
    "project_id", "trade", "item", "quantity", "unit", "unit_cost", "line_total", "source"
]


def _to_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default


def _parse_date(s: str) -> Optional[date]:
    if not s or not isinstance(s, str):
        return None
    # Try ISO-like variants
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(s[:len(fmt)], fmt).date()
        except Exception:
            continue
    return None


def load_estimate_lines_csv(csv_path: str) -> List[Dict[str, Any]]:
    """
    CSV columns: project_id, trade, item, quantity, unit, unit_cost, line_total, source
    Returns normalized rows with numeric fields coerced and non-negative.
    """
    rows: List[Dict[str, Any]] = []
    if not os.path.exists(csv_path):
        return rows
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in (r or {}).items()}
            row.setdefault("project_id", "")
            row.setdefault("trade", "")
            row.setdefault("item", "")
            row.setdefault("unit", "")
            q = max(0.0, _to_float(row.get("quantity"), 0.0))
            uc = max(0.0, _to_float(row.get("unit_cost"), 0.0))
            lt = max(0.0, _to_float(row.get("line_total"), 0.0))
            if lt <= 0.0:
                lt = max(0.0, q * uc)
            row["quantity"] = q
            row["unit_cost"] = uc
            row["line_total"] = lt
            row.setdefault("source", "")
            rows.append(row)
    return rows


def _week_start(d: date) -> date:
    # ISO week start (Monday)
    return d - timedelta(days=d.weekday())


def _daterange_weeks(start: date, end: date) -> List[date]:
    """
    Inclusive weekly buckets by week start (Monday).
    """
    if end < start:
        start, end = end, start
    buckets: List[date] = []
    cur = _week_start(start)
    while cur <= end:
        buckets.append(cur)
        cur = cur + timedelta(days=7)
    return buckets


def _linear_weights(buckets: List[date]) -> List[float]:
    """
    Simple linear ramp weights across N buckets (sum to 1).
    """
    n = max(1, len(buckets))
    if n == 1:
        return [1.0]
    ws = [i + 1 for i in range(n)]  # 1..n
    s = float(sum(ws))
    return [w / s for w in ws]


def quick_cashflow_from_estimate(rows: List[Dict[str, Any]], weeks: int = 12, retainage_pct: float = 0.1) -> Dict[str, Any]:
    """
    Produce a naive weekly cashflow over a fixed number of weeks:
      - Linear ramp allocation across weeks.
      - Apply retainage at the end as a holdback (i.e., paid at the final week).
    Returns dict: {"series":[{"week_start":"YYYY-MM-DD","amount":float}], "total":float}
    """
    total = sum(_to_float(r.get("line_total"), 0.0) for r in rows)
    weeks = max(1, int(weeks))
    today = date.today()
    buckets = [_week_start(today + timedelta(days=7 * i)) for i in range(weeks)]
    weights = _linear_weights(buckets)
    alloc_total = total * (1.0 - max(0.0, min(retainage_pct, 1.0)))
    series = []
    for b, w in zip(buckets, weights):
        amt = alloc_total * w
        series.append({"week_start": b.isoformat(), "amount": round(amt, 2)})
    # Add retainage on final week
    if series:
        series[-1]["amount"] = round(series[-1]["amount"] + (total - alloc_total), 2)
    return {"series": series, "total": round(total, 2)}


def cashflow_from_schedule(
    rows: List[Dict[str, Any]],
    schedule: Dict[str, Any],
    retainage_pct: float = 0.1
) -> Dict[str, Any]:
    """
    Allocate estimate total across scheduled tasks with start/end dates.
    - schedule shape (v0 minimal):
      { "version":"v0",
        "tasks":[
           {"name":"Mobilize","start":"2025-01-01","end":"2025-01-07","weight":0.05},
           {"name":"Foundation","start":"2025-01-08","end":"2025-02-10","weight":0.25},
           ...
        ]
      }
      Notes:
        * weight is optional; if missing, equal weights are used.
        * Weeks are ISO-week-start Mondays.
        * Retainage is held and paid in final week.
    Returns dict: {"series":[{"week_start":"YYYY-MM-DD","amount":float}], "total":float}
    """
    tasks = (schedule or {}).get("tasks") or []
    if not tasks:
        # fallback to quick curve
        return quick_cashflow_from_estimate(rows, weeks=12, retainage_pct=retainage_pct)

    total = sum(_to_float(r.get("line_total"), 0.0) for r in rows)
    if total <= 0.0:
        total = sum(_to_float(r.get("quantity"), 0.0) * _to_float(r.get("unit_cost"), 0.0) for r in rows)

    # Weights
    wts = []
    for t in tasks:
        w = t.get("weight")
        wts.append(_to_float(w, math.nan))
    if any(math.isnan(x) for x in wts):
        # Equal weights
        wts = [1.0 for _ in tasks]
    s = float(sum(wts)) or 1.0
    wts = [w / s for w in wts]

    # Build weekly buckets across all tasks
    all_starts: List[date] = []
    all_ends: List[date] = []
    parsed: List[Dict[str, Any]] = []
    for t in tasks:
        ds = _parse_date(str(t.get("start")))
        de = _parse_date(str(t.get("end")))
        if not ds or not de:
            continue
        if de < ds:
            ds, de = de, ds
        parsed.append({"start": ds, "end": de})
        all_starts.append(ds)
        all_ends.append(de)
    if not parsed:
        return quick_cashflow_from_estimate(rows, weeks=12, retainage_pct=retainage_pct)

    start_all = min(all_starts)
    end_all = max(all_ends)
    buckets = _daterange_weeks(start_all, end_all)
    amounts = {b: 0.0 for b in buckets}

    # Allocate per task across its buckets
    for t, wt in zip(parsed, wts):
        task_total = total * wt * (1.0 - max(0.0, min(retainage_pct, 1.0)))
        task_buckets = [b for b in buckets if (b >= _week_start(t["start"]) and b <= _week_start(t["end"]))]
        if not task_buckets:
            continue
        tw = _linear_weights(task_buckets)
        for b, w in zip(task_buckets, tw):
            amounts[b] += task_total * w

    # Put retainage on final week
    retainage_amt = total * max(0.0, min(retainage_pct, 1.0))
    if buckets:
        amounts[buckets[-1]] += retainage_amt

    series = [{"week_start": b.isoformat(), "amount": round(amounts[b], 2)} for b in buckets]
    return {"series": series, "total": round(total, 2)}
