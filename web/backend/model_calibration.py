from __future__ import annotations
import csv, json, math, hashlib
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

def _key(trade:str, item:str)->str:
    return f"{trade.strip().lower()}::{item.strip().lower()}"

def normalize_key(trade: str, item: str) -> str:
    return f"{(trade or '').strip().lower()}::{(item or '').strip().lower()}"

def load_raw_estimate_lines(csv_path: Path) -> Dict[str, float]:
    """
    Input: output/LYNN-001/raw_estimate/estimate_lines.csv OR data/lynn/working/estimate_lines.csv
    Returns summed extended total by (trade,item).
    - Accepts multiple header variants:
        * line_total
        * ext_cost
        * total
        * Or computes qty*unit_cost from (qty|quantity) and unit_cost
    - If 'source' column exists, prefers rows from engine:policy but does not strictly require it.
    """
    def _to_float(val) -> float:
        try:
            if val is None: 
                return 0.0
            s = str(val).strip().replace(",", "").replace("$", "")
            return float(s) if s not in ("", "nan", "None") else 0.0
        except Exception:
            return 0.0

    totals = defaultdict(float)
    if not csv_path.exists():
        return {}
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Normalize headers to handle BOM, case and whitespace per row
            rr = { (k or "").strip().lstrip("\ufeff").lower(): v for k, v in r.items() }

            trade = (rr.get("trade") or "").strip()
            item  = (rr.get("item") or "").strip()
            if not trade or not item:
                continue

            # Prefer engine:policy rows if a source column exists; otherwise include all
            src = (rr.get("source") or "").strip().lower()
            if src and ("engine" not in src):
                # skip non-engine rows if a source col is present and not engine-derived
                continue

            # Extended total: try several columns, then compute from qty*unit_cost
            lt = 0.0
            for k in ("line_total", "ext_cost", "total"):
                if k in rr:
                    lt = _to_float(rr.get(k))
                    if lt > 0:
                        break

            if lt <= 0:
                qty = 0.0
                for qk in ("qty", "quantity"):
                    if qk in rr:
                        qty = _to_float(rr.get(qk))
                        break
                uc = _to_float(rr.get("unit_cost")) if ("unit_cost" in rr) else 0.0
                lt = qty * uc

            if lt > 0.0:
                totals[normalize_key(trade, item)] += lt
    return totals

def load_vendor_canonical(csv_path: Path) -> Dict[str, float]:
    """
    Input: data/lynn/working/vendor_quotes.canonical.csv (trade,item,quoted_total)
    Returns summed quoted_total by (trade,item).
    - If trade/item missing, attempts to infer from description using data/taxonomy/vendor_map.yaml
    - Accumulates vendor totals to a global bucket when trade/item cannot be inferred
    - Note: No cap applied in v0; extreme values are tolerated because multipliers are clamped downstream.
    """
    totals = defaultdict(float)
    if not csv_path.exists():
        return {}

    # Lazy vendor_map loader (normalizers + rules)
    def _load_vendor_map_cfg() -> dict:
        try:
            from pathlib import Path as _P
            import yaml as _yaml  # type: ignore
            repo_root = Path(__file__).resolve().parents[2]
            vm = repo_root / "data" / "taxonomy" / "vendor_map.yaml"
            if vm.exists():
                return _yaml.safe_load(vm.read_text(encoding="utf-8")) or {}
        except Exception:
            return {}
        return {}

    def _apply_norm(text: str, cfg: dict) -> str:
        s = text or ""
        norms = (cfg or {}).get("normalizers") or []
        for n in norms:
            pat = str(n.get("pattern") or "").strip()
            repl = str(n.get("replace") or "")
            if not pat:
                continue
            try:
                import re as _re
                s = _re.sub(pat, repl, s, flags=_re.IGNORECASE)
            except Exception:
                s = s.replace(pat, repl)
        return s.strip()

    def _map_trade_item(desc: str, cfg: dict) -> Tuple[str, str]:
        if not desc:
            return ("","")
        rules = (cfg or {}).get("rules") or []
        import re as _re
        for r in rules:
            cond = str(r.get("if") or "").strip()
            to = r.get("to") or {}
            if not cond:
                continue
            try:
                if _re.search(cond, desc, flags=_re.IGNORECASE):
                    t = (to.get("trade") or "").strip()
                    i = (to.get("item") or "").strip()
                    if t and i:
                        return (t, i)
            except Exception:
                if cond.lower() in desc.lower():
                    t = (to.get("trade") or "").strip()
                    i = (to.get("item") or "").strip()
                    if t and i:
                        return (t, i)
        return ("","")

    # money parser: handles "", "$1,234.56", None, etc.
    def _parse_money(val) -> float:
        if val is None:
            return 0.0
        s = str(val).strip()
        if not s:
            return 0.0
        try:
            return float(s)
        except Exception:
            try:
                return float(s.replace(",", "").replace("$", ""))
            except Exception:
                return 0.0

    vm_cfg = _load_vendor_map_cfg()
    global_total = 0.0  # accumulate small totals when we cannot infer trade/item

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            trade = (r.get("trade") or "").strip()
            item  = (r.get("item") or "").strip()
            desc  = (r.get("description") or "").strip()

            # Prefer quoted_total; if not positive, fallback to line_total
            qt_q = _parse_money(r.get("quoted_total"))
            qt_l = _parse_money(r.get("line_total"))
            qt = qt_q if qt_q > 0.0 else qt_l

            # Determine max line amount from env or vendor_map parsing config (default 10M)
            def _max_line_from_env_or_cfg() -> float:
                try:
                    import os as _os
                    val = (_os.environ.get("VENDOR_MAX_LINE") or "").strip()
                    if val:
                        return float(str(val).replace(",", "").replace("$", ""))
                except Exception:
                    pass
                try:
                    cfg = _load_vendor_map_cfg() or {}
                    parsing = cfg.get("parsing") or {}
                    return float(parsing.get("max_line_amount", 10_000_000))
                except Exception:
                    return 10_000_000.0

            max_line = _max_line_from_env_or_cfg()

            # Attempt to infer trade/item when missing
            if (not trade or not item) and desc:
                norm_desc = _apply_norm(desc, vm_cfg)
                mt, mi = _map_trade_item(norm_desc, vm_cfg)
                if mt and mi:
                    trade, item = mt, mi

            # Aggregate only positive totals within max_line; exclude zeros and outliers
            if qt > 0.0 and qt <= max_line:
                if trade and item:
                    totals[normalize_key(trade, item)] += qt
                else:
                    # No inference possible; keep signal for global fallback
                    global_total += qt

    # If we saw any usable totals without a mapping, expose them via a global bucket
    if global_total > 0.0:
        totals[normalize_key("global", "__all__")] += global_total

    return totals

def compute_multipliers(estimate: Dict[str,float], vendor: Dict[str,float],
                        min_estimate: float = 1.0, clamp: Tuple[float,float]=(0.4, 2.5)) -> Dict[str,float]:
    """
    Compute per-(trade,item) multipliers with fallbacks:
      1) Exact key match: (trade::item)
      2) Trade-level fallback: use (sum vendor trade)/(sum estimate trade) when no item match
      3) Global fallback: use (sum vendor totals)/(sum estimate totals) when trade also lacks match
    Notes:
      - Skips estimate entries where estimate_total < min_estimate
      - Clamps multipliers to [lo, hi]
    """
    lo, hi = clamp
    factors: Dict[str, float] = {}

    # Precompute totals
    total_est = sum(float(v) for v in estimate.values())
    total_ven = sum(float(v) for v in vendor.values())

    # Totals by trade
    est_by_trade = defaultdict(float)
    ven_by_trade = defaultdict(float)
    for k, val in estimate.items():
        parts = k.split("::", 1)
        t = parts[0] if parts else ""
        est_by_trade[t] += float(val)
    for k, val in vendor.items():
        parts = k.split("::", 1)
        t = parts[0] if parts else ""
        ven_by_trade[t] += float(val)

    # Build factors with progressive fallback
    for k, est in estimate.items():
        est_val = float(est)
        if est_val < min_estimate:
            continue

        vend_val = float(vendor.get(k, 0.0))
        if vend_val > 0.0:
            m = vend_val / est_val
        else:
            t = k.split("::", 1)[0] if "::" in k else k
            t_est = est_by_trade.get(t, 0.0)
            t_ven = ven_by_trade.get(t, 0.0)
            if t_est >= min_estimate and t_ven > 0.0:
                m = t_ven / t_est
            elif total_est >= min_estimate and total_ven > 0.0:
                m = total_ven / total_est
            else:
                # no usable vendor signal
                continue

        m = max(lo, min(hi, m))
        factors[k] = round(m, 3)

    return factors

def digest_file(p: Path) -> str:
    if not p.exists(): return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def save_calibration_json(out_path: Path, factors: Dict[str,float], meta: Dict[str, str]):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"type":"per_trade_item_multiplier","factors":factors,"meta":meta}
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
