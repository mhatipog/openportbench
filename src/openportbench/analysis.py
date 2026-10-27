"""Paired, instance-clustered summaries for PSP JSON benchmark output.

Replicate seeds only estimate algorithm noise on a fixed instance; never
bootstrap all (instance, seed) pairs as though they were independent cases.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import math
import random
import statistics
from pathlib import Path


def summarize_pairs(document: dict, *, repeats: int = 2000, bootstrap_seed: int = 2026) -> dict:
    if repeats < 100:
        raise ValueError("Bootstrap repeats must be at least 100")
    buckets = defaultdict(list)
    valid_pairs = 0
    failures = []
    for record in document.get("rows", []):
        file = record["filename"]
        methods = record.get("methods", {})
        a = methods.get("restricted_lns")
        b = methods.get("warm_full_cp_sat")
        if a is None or b is None:
            failures.append({"file": file, "seed": record.get("seed"), "reason": "missing method"})
            continue
        if not a.get("upstream_verified") or not b.get("upstream_verified"):
            failures.append({"file": file, "seed": record.get("seed"), "reason": "unverified result"})
            continue
        x, y = a.get("objective"), b.get("objective")
        if any(v is None or not isinstance(v, (int, float)) or not math.isfinite(v)
               for v in (x, y)) or y <= 0:
            failures.append({"file": file, "seed": record.get("seed"), "reason": "invalid objective"})
            continue
        gain = 100.0 * (y - x) / y
        buckets[file].append({
            "seed": record["seed"], "lns": x, "full": y,
            "gain_pct": gain, "lns_wall_s": a["refinement_wall_s"],
            "full_wall_s": b["refinement_wall_s"],
            "lns_overrun": bool(a.get("overran_refinement_budget_10pct")),
            "full_overrun": bool(b.get("overran_refinement_budget_10pct")),
        })
        valid_pairs += 1
    cases = []
    for name, pairs in sorted(buckets.items()):
        cases.append({
            "file": name, "seeds": sorted(p["seed"] for p in pairs),
            "size": int(name.split("_")[0]),
            "mean_gain_pct": statistics.mean(p["gain_pct"] for p in pairs),
            "paired_wins": sum(p["gain_pct"] > 1e-8 for p in pairs),
            "paired_ties": sum(abs(p["gain_pct"]) <= 1e-8 for p in pairs),
            "paired_losses": sum(p["gain_pct"] < -1e-8 for p in pairs),
            "mean_lns_wall_s": statistics.mean(p["lns_wall_s"] for p in pairs),
            "mean_full_wall_s": statistics.mean(p["full_wall_s"] for p in pairs),
            "lns_10pct_budget_overruns": sum(p["lns_overrun"] for p in pairs),
            "full_10pct_budget_overruns": sum(p["full_overrun"] for p in pairs),
        })
    gains = [c["mean_gain_pct"] for c in cases]
    interval = None
    if len(gains) >= 2:
        rng = random.Random(bootstrap_seed)
        values = sorted(
            statistics.mean(rng.choice(gains) for _ in gains)
            for _ in range(repeats)
        )
        interval = [values[int(0.025 * repeats)],
                    values[min(repeats - 1, int(0.975 * repeats))]]
    return {
        "experiment": document.get("experiment"),
        "reported_instance_count": len({r["filename"] for r in document.get("rows", [])}),
        "fully_compared_instance_count": len(cases),
        "verified_pairs": valid_pairs,
        "excluded_pairs": failures,
        "cases": cases, "mean_gain_pct_equal_weight_per_instance": (
            statistics.mean(gains) if gains else None),
        "instance_cluster_bootstrap_95pct": interval,
        "bootstrap_repeats": repeats, "bootstrap_seed": bootstrap_seed,
        "interpretation": "Descriptive paired bootstrap over original instances; "
                          "not evidence of performance on an operational port",
    }


def summarize_file(source: str | Path, output: str | Path | None = None) -> dict:
    source = Path(source)
    content = source.read_bytes()
    doc = json.loads(content)
    result = summarize_pairs(doc)
    result["source_sha256"] = hashlib.sha256(content).hexdigest()
    if output is not None:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result
