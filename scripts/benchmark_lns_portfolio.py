"""Independent PSP comparison against all ten shipped LACE heuristics.

Previously unused LACE _006/_007 test files. Strict per-heuristic LACE wall
deadlines. Equal *allocated* seven-second budget per portfolio/hybrid,
not guaranteed equal consumed wall time. All candidate results independently
validated; raw failures, timeouts, CPU and wall times are retained.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time

from openportbench.neighborhood import improve_psp
from openportbench.psp import evaluate
from openportbench.runtime import run_hard_deadline

LACE_SHA = "d772b74690075f641be8077e69748ec482e9febf"
FILES = (
    "80_10_15_T48_006.txt", "80_10_15_T48_007.txt",
    "100_15_30_T48_006.txt", "100_15_30_T48_007.txt",
    "150_20_40_T48_006.txt", "150_20_40_T48_007.txt",
)
SEEDS = (1, 2)
PORTFOLIO_PER_HEURISTIC_WALL_S = 0.7   # 10 x 0.7 = 7 s
HYBRID_SOURCE_WALL_S = 2.0             # 2 + 5 = 7 s
HYBRID_REFINEMENT_ADVISORY_S = 5.0
LNS_SIZE = 14
LNS_MAX_ROUNDS = 10


def cpu():
    """CPU of finished child heuristic processes; includes subprocess startup."""
    value = resource.getrusage(resource.RUSAGE_CHILDREN)
    return value.ru_utime + value.ru_stime


def check(spec, instance, solution, expected=None):
    independent = evaluate(instance, solution)
    original = spec.tools(instance)["objective"](solution)
    if abs(original-independent) > 1e-6 or (expected is not None and
                                             abs(expected-independent) > 1e-6):
        raise AssertionError(f"Independent scoring mismatch: {independent}, {original}, {expected}")
    return independent


def main():
    root = Path(os.environ.get("LACE_ROOT", "lace_source")).resolve()
    sha = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if sha != LACE_SHA:
        raise ValueError(f"Wrong LACE source {sha}")
    sys.path.insert(0, str(root))
    import numpy as np
    import ortools
    from lace.framework import load_heuristic
    spec = importlib.import_module("problems.port_scheduling_problem.spec").SPEC
    functions = [load_heuristic(
        root / "problems/port_scheduling_problem/portfolio" / f"heuristic_{j:02d}.py"
    ) for j in range(1, 11)]
    np.random.seed(1)  # warm import, not hidden inside a per-method time limit

    observations = []
    for filename in FILES:
        path = root / "problems/port_scheduling_problem/instances/test" / filename
        inst = spec.load_data(str(path))
        for seed in SEEDS:
            row = {
                "file": filename, "seed": seed, "n": inst["vessel_num"],
                "split": "test", "instance_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "portfolio": [], "hybrid": {},
            }
            portfolio_start = time.perf_counter()
            portfolio_cpu_start = cpu()
            for j, fn in enumerate(functions, start=1):
                output = run_hard_deadline(
                    spec, inst, fn, PORTFOLIO_PER_HEURISTIC_WALL_S, seed)
                result = {
                    "heuristic": f"lace_{j:02d}", "status": output["status"],
                    "wall_s": output["wall_s"], "error": output.get("error"),
                    "objective": output.get("objective"),
                }
                if output.get("solution") is not None:
                    result["objective"] = check(spec, inst, output["solution"], output["objective"])
                    result["independently_verified"] = True
                row["portfolio"].append(result)
            port_total = time.perf_counter() - portfolio_start
            row["portfolio_wall_s"] = port_total
            row["portfolio_child_cpu_s"] = cpu() - portfolio_cpu_start
            scores = [x["objective"] for x in row["portfolio"] if x.get("independently_verified")]
            row["portfolio_best_objective"] = min(scores) if scores else None
            row["portfolio_feasible_count"] = len(scores)
            row["portfolio_timeout_count"] = sum(x["status"] == "TIMEOUT" for x in row["portfolio"])

            hybrid_start = time.perf_counter()
            source = run_hard_deadline(
                spec, inst, functions[0], HYBRID_SOURCE_WALL_S, seed)
            source_info = {
                "status": source["status"], "wall_s": source["wall_s"],
                "objective": source.get("objective"), "error": source.get("error"),
            }
            hint = source.get("solution")
            if hint is not None:
                check(spec, inst, hint, source["objective"])
                source_info["independently_verified"] = True
                refine_start = time.perf_counter()
                refine_cpu_start = time.process_time()
                repaired = improve_psp(
                    inst, hint, seconds=HYBRID_REFINEMENT_ADVISORY_S, seed=seed,
                    neighborhood_size=LNS_SIZE, max_rounds=LNS_MAX_ROUNDS)
                source_info["refinement_wall_s"] = time.perf_counter() - refine_start
                source_info["refinement_cpu_s"] = time.process_time() - refine_cpu_start
                source_info["refinement_status"] = repaired["status"]
                source_info["rounds_completed"] = len(repaired["rounds"])
                source_info["round_results"] = repaired["rounds"]
                source_info["final_objective"] = check(spec, inst, repaired["solution"], repaired["objective"])
                source_info["improved_over_initial"] = repaired["improved"]
            else:
                source_info["final_objective"] = None
            row["hybrid"] = source_info
            row["hybrid_total_wall_s"] = time.perf_counter() - hybrid_start
            row["hybrid_wall_overrun_10pct"] = row["hybrid_total_wall_s"] > 7.7
            row["portfolio_wall_overrun_10pct"] = port_total > 7.7
            row["peak_process_rss_kb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            row["portfolio_vs_hybrid_gain_pct"] = (
                100.0 * (row["portfolio_best_objective"] - source_info["final_objective"])
                / row["portfolio_best_objective"]
                if row["portfolio_best_objective"] and source_info["final_objective"] is not None
                else None
            )
            observations.append(row)
            print(
                f"{filename} seed={seed}: strict_portfolio={row['portfolio_best_objective']} "
                f"({len(scores)}/10 feasible) hybrid={source_info['final_objective']} "
                f"improvement_pct={row['portfolio_vs_hybrid_gain_pct']} "
                f"portfolio_wall={port_total:.3f} hybrid_wall={row['hybrid_total_wall_s']:.3f}",
                flush=True,
            )
    report = {
        "experiment": "frozen_lns_v2_vs_strict_lace_portfolio",
        "benchmark_commit": os.environ.get("GITHUB_SHA"),
        "upstream_lace_sha": sha, "rows": observations,
        "protocol": {
            "files": FILES, "seeds": SEEDS,
            "portfolio_10x_wall_limit_s": PORTFOLIO_PER_HEURISTIC_WALL_S,
            "hybrid_source_hard_wall_s": HYBRID_SOURCE_WALL_S,
            "hybrid_refinement_advisory_s": HYBRID_REFINEMENT_ADVISORY_S,
            "lns_neighborhood_size": LNS_SIZE, "lns_max_rounds": LNS_MAX_ROUNDS,
            "nominal_total_budget_per_competitor_s": 7.0,
            "comparability": "same problem/objective; equal nominal wall budget, "
                             "different allocations and actual runtime; strict only for "
                             "individual source heuristic calls",
        },
        "environment": {
            "python": sys.version.split()[0], "ortools": ortools.__version__,
            "numpy": np.__version__, "platform": platform.platform(),
            "cpus": os.cpu_count(), "machine": platform.machine(),
        },
    }
    output = Path("results/tmp/lns-vs-lace-portfolio.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print("RESULT_JSON", output, flush=True)


if __name__ == "__main__":
    main()
