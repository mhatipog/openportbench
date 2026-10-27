"""Render benchmark protocol JSON as an honest, shareable Markdown scorecard."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics


def render_matrix(doc: dict, *, source_hash: str | None = None) -> str:
    if doc.get("protocol") != "PSP-strict-common-incumbent-v1":
        raise ValueError("Expected PSP common-incumbent, strict-wall protocol")
    methods=doc["methods"]
    rows=doc["rows"]
    out=[
        "# PSP solver tournament — reproducible comparison",
        "",
        "> Research benchmark, **not a claim of maritime state of the art**. "
        "These rankings apply only to the specified generated LACE PSP inputs, "
        "hardware, warm-start convention and strict wall budget.",
        "",
        f"- Dataset split: **{doc['split']}**; LACE source: `{doc['source_sha']}`",
        f"- OpenPortBench runner: `{doc['benchmark_commit']}`",
        f"- Unique input files: **{len({r['input_sha256'] for r in rows})}**; "
        f"paired source observations: **{len(rows)}**",
        f"- Common initial incumbent source wall budget: **{doc['source_hard_wall_s']} s**; "
        f"each independent refinement hard budget: **{doc['refinement_hard_wall_s']} s**",
    ]
    if source_hash:
        out.append(f"- Exact primary JSON SHA256: `{source_hash}`")
    out.extend([
        "",
        "## Summary (per-instance normalized improvements)",
        "",
        "| Method | Mean improvement vs common source | Mean actual wall | Full timed-out / total | "
        "Invalid | Method wins (ties included) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    metrics=doc["summary"]["metrics"]
    wins=doc["summary"]["winner_counts_including_ties"]
    for method in methods:
        stats=metrics.get(method)
        if not stats:
            out.append(f"| `{method}` | — | — | — | — | — |")
            continue
        val=stats["mean_improvement_pct_instance_weighted"]
        out.append(
            f"| `{method}` | {val:.2f}% | {stats['mean_observed_wall_s']:.2f} s | "
            f"{stats['hard_timeout_count']}/{stats['observations']} | "
            f"{stats['invalid_count']} | {wins.get(method,0)} |")
    out.extend([
        "",
        "A hard timeout returns a valid *preserved incumbent*, **not** a new "
        "solver success. HiGHS `MASTER_OPTIMAL` is optimal only within the "
        "restricted generated candidate set; it is not a full PSP bound. "
        "Likewise, a CP-SAT neighborhood optimum does not prove global PSP "
        "optimality. Scores from different problem sizes must never be compared "
        "directly without within-instance normalization.",
        "",
        "## Instance-level paired outcomes",
        "",
        "| Input | Seeds | " + " | ".join(f"`{m}` mean improvement" for m in methods)+" |",
        "| --- | ---: | " + " | ".join("---:" for _ in methods) +" |",
    ])
    byfile=defaultdict(list)
    for row in rows:
        byfile[row["file"]].append(row)
    for name,group in sorted(byfile.items(),key=lambda x:(int(x[0].split("_")[0]),x[0])):
        cells=[]
        for method in methods:
            deltas=[
                100*(r["source_objective"]-r["methods"][method]["objective"])/r["source_objective"]
                for r in group if r["source_objective"] is not None
            ]
            cells.append(f"{statistics.mean(deltas):.2f}%" if deltas else "—")
        out.append(f"| `{name}` | {len(group)} | " +" | ".join(cells)+" |")
    out.extend([
        "",
        "## Reproduce",
        "",
        "Install `pip install -e '.[dev]'` plus `mip networkx`. "
        "Checkout LACE at the source revision above, then run "
        "`scripts/solver_matrix.py` with the exact sizes, indices, split, "
        "seeds and budgets recorded in the JSON. The original LACE scorer "
        "and an independent PSP checker validate every final solution.",
        "",
        "All measurements were obtained without paid solver licenses. These "
        "comparisons do not constitute a reproduction of a published ALNS "
        "algorithm, a commercial system, or an OpenAI mathematical theorem.",
        "",
    ])
    return "\n".join(out)


def render_file(source: str | Path, output: str | Path) -> None:
    payload=Path(source).read_bytes()
    doc=json.loads(payload)
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(
        render_matrix(doc,source_hash=hashlib.sha256(payload).hexdigest()),
        encoding="utf-8",
    )
