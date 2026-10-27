"""Rigorous within-instance matched multi-budget tournament profiles.

Excludes unverified initial schedules from success and win-rate metrics.
Bootstrap resamples independently generated *instances*, never repeated seeds.
"""
from __future__ import annotations

from collections import defaultdict
import json
import random
import statistics

from .matrix_summary import summary


def summarize_sweep(doc: dict) -> dict:
    if doc.get("protocol") != "PSP-strict-common-incumbent-sweep-v1":
        raise ValueError("Wrong benchmark protocol")
    output = {}
    for budget in doc["refinement_hard_budgets_s"]:
        key = f"{budget:g}"
        block = {
            "rows": [
                {**row, "methods": row["methods_by_budget"][key]}
                for row in doc["rows"]
            ]
        }
        output[key] = summary(block)
    return output


def _clustered_values(doc, budget, method):
    """One paired, seed-averaged % improvement per independent input."""
    groups = defaultdict(list)
    key = f"{budget:g}"
    for row in doc["rows"]:
        if row.get("source_status") != "FEASIBLE" or row.get("source_objective") is None:
            continue
        base = row["source_objective"]
        if base <= 0:
            raise ValueError("Expected positive reference objective")
        candidate = row["methods_by_budget"][key][method]["objective"]
        groups[(row["file"], row["input_sha256"])].append(
            100.0 * (base - candidate) / base)
    return [statistics.mean(group) for _,group in sorted(groups.items())]


def confidence_interval(values, *, confidence=.95, reps=3000, seed=2026):
    """Percentile instance-cluster bootstrap; descriptive, not proof of SOTA."""
    if not values:
        return None
    rng = random.Random(seed)
    n = len(values)
    mean = statistics.mean(values)
    if n == 1:
        return {"mean":mean, "lower":None, "upper":None, "n_instances":1}
    resampled = sorted(statistics.mean(rng.choices(values,k=n)) for _ in range(reps))
    alpha = (1-confidence)/2
    return {
        "mean":mean,
        "lower":resampled[int(alpha*reps)],
        "upper":resampled[min(reps-1,int((1-alpha)*reps))],
        "n_instances":n,
    }


def render_sweep(doc: dict, source_hash: str) -> str:
    """Markdown provenance, distinct-size results and fair runtime profile."""
    if doc.get("protocol")!="PSP-strict-common-incumbent-sweep-v1":
        raise ValueError("Wrong benchmark protocol")
    if "summary_by_budget" not in doc:
        doc = {**doc, "summary_by_budget":summarize_sweep(doc)}
    budgets=doc["refinement_hard_budgets_s"]
    methods=doc["methods"]
    rows=doc["rows"]
    out=[
        "# Strict end-to-end wall-time PSP algorithm performance profiles",
        "",
        "> Exploratory synthetic benchmark. There is no commercial or published "
        "SOTA equivalence implied by these rankings.",
        "",
        f"- Source: **LACE** commit \`{doc['source_sha']}\`, **{doc['split']}** split",
        f"- Runner: \`{doc['benchmark_commit']}\`",
        f"- Unmodified input instances: **{len({r['input_sha256'] for r in rows})}**; "
        f"observations with different random seeds: **{len(rows)}**",
        f"- Source heuristic strict construction budget: **{doc['source_hard_wall_s']} s** "
        "(common to every method AND all refinement budgets within a trial)",
        f"- Method refinement deadlines (strict worker-launch-to-response): "
        + ", ".join(f"**{b:g} s**" for b in budgets),
        f"- Raw primary JSON SHA256: \`{source_hash}\`",
        "",
        "## Equal-budget comparisons",
        "",
        "| Budget | Method | Mean per-instance gain | 95% cluster bootstrap CI* | "
        "Mean observed wall | Hard timeouts | Successful outputs |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for budget in budgets:
        key=f"{budget:g}"
        summaries=doc["summary_by_budget"][key]["metrics"]
        for method in methods:
            record=summaries.get(method)
            if record is None:
                out.append(f"| {key} s | \`{method}\` | — | — | — | — | — |")
                continue
            ci=confidence_interval(_clustered_values(doc,budget,method))
            bounds=(f"[{ci['lower']:.2f}%, {ci['upper']:.2f}%]"
                    if ci and ci["lower"] is not None else "—")
            total=record["observations"]
            valid=sum(1 for row in rows
                      if row["source_status"]=="FEASIBLE" and
                      row["methods_by_budget"][key][method]["status"]=="FEASIBLE")
            out.append(
                f"| {key} s | \`{method}\` | "
                f"{record['mean_improvement_pct_instance_weighted']:.2f}% | "
                f"{bounds} | {record['mean_observed_wall_s']:.2f} s | "
                f"{record['hard_timeout_count']}/{total} | {valid}/{total} |")
    out.extend([
        "",
        "*95% confidence intervals are **descriptive percentile bootstrap intervals "
        "over distinct instance files** (3,000 resamples, seed 2026). With few "
        "instances they can be unreliable; seeds of a single instance are NOT "
        "independent research replications. These intervals do not account for "
        "benchmark/dataset selection bias.",
        "",
        "## Per-instance improvement curves",
        "",
        "| Input | Seeds | Budget | "+ " | ".join(f"\`{m}\`" for m in methods)+" |",
        "| --- | ---: | ---: | "+" | ".join("---:" for _ in methods)+" |",
    ])
    grouped=defaultdict(list)
    for row in rows:
        grouped[(row["file"],row["input_sha256"])].append(row)
    for (name, _), items in sorted(grouped.items(),key=lambda x: (
        int(x[0][0].split("_")[0]),x[0][0])):
        for b in budgets:
            key=f"{b:g}"
            measures=[]
            for method in methods:
                values=[
                    100*(row["source_objective"]-
                         row["methods_by_budget"][key][method]["objective"])/row["source_objective"]
                    for row in items if row["source_status"]=="FEASIBLE"
                ]
                measures.append(f"{statistics.mean(values):.2f}%" if values else "—")
            out.append(f"| \`{name}\` | {len(items)} | {key} s | "
                       + " | ".join(measures)+" |")
    out.extend([
        "",
        "## Interpretation",
        "",
        "Improvements are percentage reductions of the independently verified "
        "complete four-term PSP objective versus the **same source schedule** "
        "across all budgets in a paired trial. A timeout preserves that source "
        "score as an explicit fallback, never counts as a feasible solver output, "
        "and must not be labelled optimal. Fully timed CP-SAT is the only complete "
        "PSP model; HiGHS is optimal only over candidate columns and ALNS/LNS "
        "give no global certificates. A wall-time deadline is not equal CPU "
        "consumption. No single approach is declared universal SOTA.",
        "",
    ])
    return "\n".join(out)
