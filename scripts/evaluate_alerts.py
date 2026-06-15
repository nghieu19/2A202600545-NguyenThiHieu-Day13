from __future__ import annotations

import json
import re
from pathlib import Path

import yaml


def load_metrics() -> dict:
    p = Path("data/metrics_snapshot.json")
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    # fallback: try to read live metrics
    try:
        import httpx

        r = httpx.get("http://127.0.0.1:8000/metrics", timeout=5.0)
        return r.json()
    except Exception:
        return {}


def eval_condition(cond: str, metrics: dict) -> tuple[bool, str]:
    # simple parser for conditions like 'latency_p95_ms > 5000 for 30m' or 'error_rate_pct > 5 for 5m'
    m = re.search(r"([a-zA-Z0-9_]+)\s*(>=|<=|==|>|<)\s*([0-9\.]+)", cond)
    if not m:
        return False, "unsupported condition"
    metric_name, op, value_s = m.groups()
    value = float(value_s)

    # map metric_name to metrics dict keys
    if metric_name == "latency_p95_ms":
        actual = float(metrics.get("latency_p95", 0.0))
    elif metric_name == "latency_p50_ms":
        actual = float(metrics.get("latency_p50", 0.0))
    elif metric_name == "latency_p99_ms":
        actual = float(metrics.get("latency_p99", 0.0))
    elif metric_name == "error_rate_pct":
        errs = sum(metrics.get("error_breakdown", {}).values()) if metrics.get("error_breakdown") else 0
        traffic = metrics.get("traffic", 0) or 0
        actual = (errs / traffic * 100.0) if traffic > 0 else 0.0
    elif metric_name == "hourly_cost_usd":
        # can't reliably compute hourly cost from in-memory snapshot
        return False, "cannot_evaluate_hourly_cost"
    else:
        return False, f"unknown_metric:{metric_name}"

    ops = {
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
    }

    result = ops[op](actual, value)
    return result, f"actual={actual} {op} threshold={value}"


def main() -> None:
    cfg_path = Path("config/alert_rules.yaml")
    if not cfg_path.exists():
        print("No alert config found at config/alert_rules.yaml")
        return

    metrics = load_metrics()
    rules = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    alerts = rules.get("alerts", [])

    fired = []
    ignored = []

    for a in alerts:
        name = a.get("name")
        cond = a.get("condition", "")
        ok, note = eval_condition(cond, metrics)
        if ok:
            fired.append((name, cond, note))
        else:
            # note may indicate unsupported
            ignored.append((name, cond, note))

    print("Alert evaluation report")
    print("-----------------------")
    print(f"Metrics snapshot: {json.dumps(metrics, indent=2)}\n")
    if fired:
        print("Fired alerts:")
        for f in fired:
            print(f"- {f[0]} | {f[1]} | {f[2]}")
    else:
        print("No alerts fired.")

    if ignored:
        print("\nIgnored or non-evaluable rules:")
        for ig in ignored:
            print(f"- {ig[0]} | {ig[1]} | {ig[2]}")


if __name__ == '__main__':
    main()
