"""Re-run LACE's shipped 10-heuristic portfolio on fixed training instances.

No LLM calls. For PSP, independently verify LACE candidates and verify our
CP-SAT and greedy solutions against the original evaluator as well.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

from openportbench.psp import evaluate
from openportbench.solvers import greedy, cp_sat

LACE_SHA = "d772b74690075f641be8077e69748ec482e9febf"
CASES = {
    "port_scheduling_problem": "20_2_3_T12_001.txt",
    "multi_tugboat_routing_and_scheduling_problem": "n10_K5_T24_00001.txt",
    "multi_base_tugboat_routing_and_scheduling_problem": "12_6_3_001.txt",
    "multi_tugboat_routing_problem_with_variable_speed": "n10_m3_a30_001.txt",
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seconds-per-heuristic", type=float, default=0.35)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--output", type=Path, default=Path("results/smoke.json"))
    args = p.parse_args()
    if args.seconds_per_heuristic <= 0:
        p.error("Budget must be positive")
    root = Path(os.environ.get("LACE_ROOT", "lace_source")).resolve()
    actual = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if actual != LACE_SHA:
        raise RuntimeError(f"Unexpected LACE revision {actual}; expected {LACE_SHA}")
    sys.path.insert(0, str(root))
    from lace.framework import load_heuristic, run_solve
    import ortools
    try:
        import numpy as np
    except ImportError:
        np = None
    try:
        import scipy
        scipy_version = scipy.__version__
    except ImportError:
        scipy_version = None
    results = {
        "status": "SMOKE_NOT_PAPER_REPRODUCTION",
        "source": {"lace_git_sha": actual, "openportbench_git_sha": os.environ.get("GITHUB_SHA")},
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "cpu": platform.processor() or platform.machine(),
                        "ortools": ortools.__version__, "numpy": getattr(np, "__version__", None),
                        "scipy": scipy_version, "cpu_count": os.cpu_count()},
        "budget": {"lace_per_heuristic_s": args.seconds_per_heuristic,
                   "cp_sat_total_s": args.seconds_per_heuristic * 10},
        "seed": args.seed, "problems": {},
    }
    for slug, filename in CASES.items():
        print(f"START {slug}", flush=True)
        spec = importlib.import_module(f"problems.{slug}.spec").SPEC
        path = root / "problems" / slug / "instances" / "train" / filename
        inst = spec.load_data(str(path))
        record = {"instance": str(path.relative_to(root)), "split": "train",
                  "instance_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                  "validation": "independent+upstream" if slug == "port_scheduling_problem" else "upstream_only",
                  "heuristics": []}
        for j in range(1, 11):
            name = f"heuristic_{j:02d}"
            random.seed(args.seed)
            if np is not None:
                np.random.seed(args.seed)
            fn = load_heuristic(root / "problems" / slug / "portfolio" / f"{name}.py")
            rr = run_solve(spec, inst, fn, time_limit_s=args.seconds_per_heuristic)
            h = {"name": name, "feasible_upstream": rr.feasible, "objective": rr.objective,
                 "runtime_s": rr.elapsed_s, "overran_advisory_budget": rr.elapsed_s > args.seconds_per_heuristic * 1.1,
                 "error": rr.error_msg}
            if rr.feasible and slug == "port_scheduling_problem":
                independent = evaluate(inst, rr.solution)
                if abs(independent - rr.objective) > 1e-6:
                    raise AssertionError(f"Objective/checker mismatch on {name}: {independent} vs {rr.objective}")
                h["independent_objective"] = independent
            record["heuristics"].append(h)
            print(f"  {name}: {h['objective']} / {h['runtime_s']:.3f}s / {h['error']}", flush=True)
        valid = [h for h in record["heuristics"] if h["feasible_upstream"]]
        record["portfolio_best"] = min((h["objective"] for h in valid), default=None)
        record["portfolio_total_actual_s"] = sum(h["runtime_s"] for h in record["heuristics"])
        if slug == "port_scheduling_problem":
            record["baselines"] = {}
            for order in ("fcfs", "priority"):
                t0 = time.perf_counter()
                sol = greedy(inst, order=order)
                seconds = time.perf_counter() - t0
                own_score = evaluate(inst, sol)
                upstream_score = spec.tools(inst)["objective"](sol)
                if abs(own_score - upstream_score) > 1e-6:
                    raise AssertionError(f"Checker mismatch: {order}")
                record["baselines"][order] = {"objective": own_score, "runtime_s": seconds,
                                              "feasible_independent": True}
            cp = cp_sat(inst, seconds=args.seconds_per_heuristic * 10, seed=args.seed)
            if cp["solution"] is not None:
                upstream_score = spec.tools(inst)["objective"](cp["solution"])
                if abs(cp["objective"] - upstream_score) > 1e-6:
                    raise AssertionError("CP-SAT and LACE objective mismatch")
            cp.pop("solution")
            record["baselines"]["cp-sat"] = cp
            print(f"  CP-SAT: {cp['objective']} bound={cp['best_bound']} status={cp['status']}", flush=True)
        results["problems"][slug] = record
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT_JSON {args.output} ({args.output.stat().st_size} bytes)", flush=True)
    print("SUMMARY_JSON " + json.dumps(
        {slug: {"portfolio_best": r["portfolio_best"],
                "portfolio_actual_s": r["portfolio_total_actual_s"],
                "cp_sat": r.get("baselines", {}).get("cp-sat", {}).get("objective")}
         for slug, r in results["problems"].items()}), flush=True)


if __name__ == "__main__":
    main()
