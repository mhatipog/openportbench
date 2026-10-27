"""Reproducible fair PSP solver tournament on original, pinned LACE inputs.

One verified common initial incumbent per (instance, seed). Every independent
refinement method gets an identical *externally enforced* wall deadline.
This is a benchmark protocol, not an accuracy claim about any participant.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys

from openportbench.benchkit import METHODS, strict_refine, sanitize
from openportbench.matrix_summary import summary
from openportbench.psp import empty_solution, evaluate
from openportbench.runtime import run_hard_deadline

LACE_SHA="d772b74690075f641be8077e69748ec482e9febf"
TRACK="port_scheduling_problem"
PATTERNS={20:"20_2_3_T12",40:"40_3_4_T12",60:"60_5_8_T12",
          80:"80_10_15_T48",100:"100_15_30_T48",150:"150_20_40_T48",
          250:"250_20_50_T48",300:"300_25_60_T48",500:"500_40_100_T48"}


def build_parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--split",choices=["train","test"],default="train")
    p.add_argument("--sizes",default="20,40,60")
    p.add_argument("--indices",default="004,005")
    p.add_argument("--seeds",default="1,2")
    p.add_argument("--methods",default="warm-cp-sat,fix-optimize-cp-sat,restricted-highs-milp")
    p.add_argument("--refine-seconds",type=float,default=3.)
    p.add_argument("--refine-budgets",default=None,
                   help="Comma-separated hard deadlines; same baseline for every budget")
    p.add_argument("--source-seconds",type=float,default=.8)
    p.add_argument("--output",default="results/tmp/solver-matrix.json")
    return p


def main():
    a=build_parser().parse_args()
    sizes=[int(s) for s in a.sizes.split(",")]
    idx=a.indices.split(",")
    seeds=[int(s) for s in a.seeds.split(",")]
    methods=a.methods.split(",")
    if not sizes or not idx or not seeds or any(i not in PATTERNS for i in sizes):
        raise ValueError("Invalid dimensions")
    if len(set(methods))!=len(methods) or any(m not in METHODS or m=="identity" for m in methods):
        raise ValueError("Unknown or duplicate method")
    budgets = ([float(t) for t in a.refine_budgets.split(",")] if a.refine_budgets
               else [a.refine_seconds])
    if (not budgets or len(set(budgets)) != len(budgets)
            or any(not math.isfinite(t) or t <= 0 for t in budgets)
            or a.source_seconds <= 0):
        raise ValueError("Time limits must be finite and positive; budgets unique")
    root=Path(os.environ.get("LACE_ROOT","lace_source")).resolve()
    sha=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    if sha!=LACE_SHA:
        raise RuntimeError("LACE source SHA mismatch")
    sys.path.insert(0,str(root))
    import numpy as np
    import scipy
    import ortools
    from lace.framework import load_heuristic
    spec=importlib.import_module(f"problems.{TRACK}.spec").SPEC
    fn=load_heuristic(root/f"problems/{TRACK}/portfolio/heuristic_01.py")
    np.random.seed(1)
    doc={
        "protocol":("PSP-strict-common-incumbent-sweep-v1" if len(budgets) > 1
                    else "PSP-strict-common-incumbent-v1"),
        "benchmark_commit":os.environ.get("GITHUB_SHA") or "local",
        "source_sha":sha,
        "split":a.split,
        "methods":methods,
        "sizes":sizes,
        "instance_indices":idx,
        "seeds":seeds,
        "source_hard_wall_s":a.source_seconds,
        "refinement_hard_wall_s":budgets[0],
        "refinement_hard_budgets_s":budgets,
        "environment":{
            "python":sys.version.split()[0],"numpy":np.__version__,
            "scipy":scipy.__version__,"ortools":ortools.__version__,
            "platform":platform.platform(),
            "processors":os.cpu_count(),
            "github_runner":os.environ.get("RUNNER_NAME"),
        },
        "rows":[],
    }
    for size in sizes:
        for suffix in idx:
            filename=f"{PATTERNS[size]}_{suffix}.txt"
            p=root/f"problems/{TRACK}/instances/{a.split}/{filename}"
            if not p.is_file():
                raise FileNotFoundError(f"No silent skipping of missing instance: {p}")
            instance=spec.load_data(str(p))
            for seed in seeds:
                random.seed(seed)
                source=run_hard_deadline(spec,instance,fn,a.source_seconds,seed)
                hint=source.get("solution")
                source_score=None
                if hint is not None:
                    source_score=evaluate(instance,hint)
                    upstream=spec.tools(instance)["objective"](hint)
                    if not math.isclose(source_score,upstream,rel_tol=0,abs_tol=1e-6):
                        raise AssertionError("Baseline checker mismatch")
                else:
                    hint=empty_solution(instance)
                row={
                    "file":filename,"n":size,"seed":seed,"split":a.split,
                    "input_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                    "source_status":source["status"],"source_error":source.get("error"),
                    "source_wall_s":source["wall_s"],
                    "source_objective":source_score,
                    "methods":{},
                }
                budget_records = {}
                for budget in budgets:
                    budget_records[f"{budget:g}"] = {}
                    for name in methods:
                        r=strict_refine(instance,hint,name,budget,seed)
                        score=evaluate(instance,r["solution"])
                        upstream=spec.tools(instance)["objective"](r["solution"])
                        if not math.isclose(score,upstream,rel_tol=0,abs_tol=1e-6):
                            raise AssertionError(f"Validation failure {name} {filename}")
                        rec=sanitize(r)
                        rec["upstream_verified"]=True
                    # If source construction failed, results must not enter
                    # common-incumbent win-rate and improvement summaries.
                        rec["valid_comparison"]=source_score is not None
                        budget_records[f"{budget:g}"][name]=rec
                if len(budgets) == 1:
                    row["methods"] = budget_records[f"{budgets[0]:g}"]
                else:
                    row["methods_by_budget"] = budget_records
                doc["rows"].append(row)
                for budget in budgets:
                    outcomes = budget_records[f"{budget:g}"]
                    print(filename,seed,source["status"],f"budget={budget:g}",
                          " ".join(f"{name}={outcomes[name]['objective']:.3f}"
                                   f"/{outcomes[name]['status']}"
                                   for name in methods),flush=True)
    if len(budgets) == 1:
        doc["summary"] = summary(doc)
    else:
        from openportbench.matrix_profile import summarize_sweep
        doc["summary_by_budget"] = summarize_sweep(doc)
    output=Path(a.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(doc,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("SUMMARY",json.dumps(doc.get("summary",doc.get("summary_by_budget")),sort_keys=True),flush=True)
    print("RESULT_JSON",output,flush=True)


if __name__=="__main__":
    main()
