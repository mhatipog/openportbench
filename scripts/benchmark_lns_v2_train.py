"""Paired training-only comparison: verified source incumbent + exact/LNS refinement.

No test instances are loaded. Benchmarks are not OpenAI mathematical theorem
reproductions; each candidate is checked with the independent and original
LACE PSP evaluators. Individual solver budgets are advisory (model build time
excluded from CP-SAT max_time); actual wall time is always recorded.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import random
import resource
import subprocess
import sys
import time

from openportbench.neighborhood import improve_psp
from openportbench.psp import evaluate
from openportbench.runtime import run_hard_deadline
from openportbench.solvers import cp_sat

LACE_SHA = "d772b74690075f641be8077e69748ec482e9febf"
TRAIN_FILES = (
    "20_2_3_T12_002.txt",
    "40_3_4_T12_002.txt",
    "60_5_8_T12_002.txt",
)
SEEDS = (1, 2, 3)
HEURISTIC_WALL_LIMIT_S = 0.6
REFINEMENT_BUDGET_S = 2.5
LNS_SIZE = 14
LNS_ROUNDS = 10


def environment():
    import ortools
    import numpy
    import scipy
    cpu = "unknown"
    p = Path("/proc/cpuinfo")
    if p.exists():
        cpu = next((line.partition(":")[2].strip() for line in
                    p.read_text().splitlines() if line.startswith("model name")), cpu)
    return {"python": sys.version.split()[0], "platform": platform.platform(),
            "cpu": cpu, "ortools": ortools.__version__, "numpy": numpy.__version__,
            "scipy": scipy.__version__, "logical_cpus": os.cpu_count()}


def main():
    root = Path(os.environ.get("LACE_ROOT", "lace_source")).resolve()
    sha = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                  text=True).strip()
    if sha != LACE_SHA:
        raise RuntimeError(f"Incorrect LACE checkout: {sha}")
    sys.path.insert(0, str(root))
    from lace.framework import load_heuristic
    spec = importlib.import_module("problems.port_scheduling_problem.spec").SPEC
    heuristic = load_heuristic(
        root / "problems/port_scheduling_problem/portfolio/heuristic_01.py"
    )
    import numpy
    numpy.random.seed(1)  # initialize before Unix fork, not inside timed budget
    rows = []
    for filename in TRAIN_FILES:
        path = root / "problems/port_scheduling_problem/instances/train" / filename
        inst = spec.load_data(str(path))
        for seed in SEEDS:
            random.seed(seed)
            start = time.perf_counter()
            baseline = run_hard_deadline(spec, inst, heuristic, HEURISTIC_WALL_LIMIT_S, seed)
            heuristic_wall = time.perf_counter() - start
            record = {
                "filename": filename, "seed": seed, "split": "train",
                "n": inst["vessel_num"],
                "instance_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "heuristic": {
                    "name": "lace-01", "wall_s": heuristic_wall,
                    "hard_budget_s": HEURISTIC_WALL_LIMIT_S,
                    "status": baseline["status"],
                    "objective": baseline["objective"],
                    "error": baseline.get("error"),
                },
                "methods": {},
            }
            hint = baseline.get("solution")
            if hint is None:
                print("NO INCUMBENT", filename, seed, baseline["status"], flush=True)
                rows.append(record)
                continue
            source_score = evaluate(inst, hint)
            source_native = spec.tools(inst)["objective"](hint)
            if abs(source_score - source_native) > 1e-6:
                raise AssertionError("Source incumbent objective disagreement")
            record["heuristic"]["independently_verified"] = True

            # Reverse evaluation order by seed to reduce systematic ordering bias.
            methods = ["warm_full_cp_sat", "restricted_lns"]
            if seed % 2 == 0:
                methods.reverse()
            for name in methods:
                t0 = time.perf_counter()
                c0 = time.process_time()
                if name == "warm_full_cp_sat":
                    result = cp_sat(inst, seconds=REFINEMENT_BUDGET_S, seed=seed,
                                    hint_solution=hint)
                    sol = result["solution"]
                    row = {
                        "objective": result["objective"], "status": result["status"],
                        "incumbent_source": result["incumbent_source"],
                        "global_best_bound": result["best_bound"],
                        "model_search_s": result["runtime_s"],
                    }
                else:
                    result = improve_psp(inst, hint, seconds=REFINEMENT_BUDGET_S,
                                         seed=seed, neighborhood_size=LNS_SIZE,
                                         max_rounds=LNS_ROUNDS)
                    sol = result["solution"]
                    row = {
                        "objective": result["objective"], "status": result["status"],
                        "incumbent_source": "local_repair" if result["improved"] else "verified_hint",
                        "global_best_bound": None,
                        "rounds": result["rounds"],
                        "iterations": len(result["rounds"]),
                    }
                wall = time.perf_counter()-t0
                row["refinement_wall_s"] = wall
                row["total_wall_s"] = wall + heuristic_wall
                row["cpu_s"] = time.process_time()-c0
                row["peak_process_rss_kb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                row["overran_refinement_budget_10pct"] = wall > REFINEMENT_BUDGET_S * 1.1
                row["independent_objective"] = evaluate(inst, sol)
                upstream_score = spec.tools(inst)["objective"](sol)
                if abs(row["objective"] - row["independent_objective"]) > 1e-6 or abs(
                    row["objective"] - upstream_score) > 1e-6:
                    raise AssertionError(f"{name} validator disagreement for {filename} seed={seed}")
                if row["objective"] > source_score + 1e-6:
                    raise AssertionError(f"{name} unexpectedly worsened incumbent")
                row["upstream_verified"] = True
                row["improvement_over_incumbent_pct"] = round(
                    100*(source_score-row["objective"])/source_score, 6
                ) if source_score > 0 else 0.
                record["methods"][name] = row
                print(filename, seed, name, row["objective"], row["status"],
                      f"wall={wall:.3f}", flush=True)
            rows.append(record)
    report = {
        "experiment": "frozen_lns_train_v2_larger_neighborhood", "lace_sha": LACE_SHA,
        "openportbench_sha": os.environ.get("GITHUB_SHA", "local"),
        "environment": environment(),
        "settings": {
            "files": TRAIN_FILES, "seeds": SEEDS,
            "heuristic_hard_wall_s": HEURISTIC_WALL_LIMIT_S,
            "refinement_advisory_budget_s": REFINEMENT_BUDGET_S,
            "lns_neighborhood_size": LNS_SIZE, "lns_max_rounds": LNS_ROUNDS,
            "cp_sat_workers": 1,
            "caution": "CP-SAT solver timeout excludes Python model build; true method wall time recorded",
        }, "rows": rows,
    }
    path = Path("results/tmp/lns-train-v2.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print("RESULT_JSON", path, flush=True)
    print("SUMMARY",
          json.dumps({name: [
              (r["methods"].get(name) or {}).get("improvement_over_incumbent_pct")
              for r in rows
          ] for name in ("warm_full_cp_sat", "restricted_lns")}), flush=True)


if __name__ == "__main__":
    main()
