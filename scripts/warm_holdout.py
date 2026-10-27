"""Pre-declared paired TRAIN experiment: CP-SAT cold vs LACE-guided CP-SAT.

NOT a held-out evaluation. Do not infer general speedups from tiny sample.
Time accounting includes heuristic and CP-SAT model construction separately.
"""
import hashlib
import importlib
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

from openportbench.psp import evaluate
from openportbench.solvers import cp_sat


SOURCE = "d772b74690075f641be8077e69748ec482e9febf"
FILES = (
    "80_10_15_T48_002.txt",
    "100_15_30_T48_002.txt",
)
SEEDS = (1, 2, 3)
TOTAL_S = 5.0


def main():
    root = Path(os.environ.get("LACE_ROOT", "lace_source")).resolve()
    sha = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if sha != SOURCE:
        raise ValueError("LACE source revision not pinned")
    sys.path.insert(0, str(root))
    from lace.framework import load_heuristic, run_solve
    import ortools
    spec = importlib.import_module("problems.port_scheduling_problem.spec").SPEC
    fn = load_heuristic(root / "problems/port_scheduling_problem/portfolio/heuristic_01.py")
    rows = []
    for filename in FILES:
        path = root / "problems/port_scheduling_problem/instances/test" / filename
        instance = spec.load_data(str(path))
        for seed in SEEDS:
            random.seed(seed)
            t0 = time.perf_counter()
            heuristic = run_solve(spec, instance, fn, time_limit_s=0.35)
            hint_wall = time.perf_counter()-t0
            hint = heuristic.solution if heuristic.feasible else None
            if hint is not None and abs(evaluate(instance, hint)-heuristic.objective)>1e-6:
                raise AssertionError("Source hint objective disagreement")
            record = {"instance": filename, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "split": "test", "seed": seed, "n": instance["vessel_num"],
                      "heuristic_01_obj": heuristic.objective if heuristic.feasible else None,
                      "heuristic_01_wall_s": hint_wall, "heuristic_feasible": heuristic.feasible,
                      "allocated_total_s_per_method": TOTAL_S,
                      "methods": {}, "experiment": "frozen-warm-hint-heldout-first-exposure"}
            orders = ("cold", "warm") if seed % 2 else ("warm", "cold")
            for label in orders:
                if label == "warm" and (hint is None or hint_wall >= TOTAL_S):
                    record["methods"][label] = {"status": "NO_INCUMBENT_OR_BUDGET", "objective": None}
                    continue
                allotted = TOTAL_S if label=="cold" else TOTAL_S-hint_wall
                t0=time.perf_counter()
                result=cp_sat(instance, seconds=allotted, seed=seed,
                              hint_solution=hint if label=="warm" else None)
                elapsed=time.perf_counter()-t0
                sol=result.pop("solution")
                if sol is not None:
                    upstream=spec.tools(instance)["objective"](sol)
                    if abs(result["objective"]-upstream)>1e-6:
                        raise AssertionError("Independent scorer mismatch")
                record["methods"][label] = {
                    "status":result["status"], "objective":result["objective"],
                    "best_bound":result["best_bound"],
                    "wall_total_s":elapsed+(hint_wall if label=="warm" else 0.0),
                    "solver_s":result["runtime_s"], "scale":result["scale"],
                    "allocated_s":TOTAL_S, "verified_upstream":sol is not None,
                    "overran_wall_budget":elapsed+(hint_wall if label=="warm" else 0.0)>TOTAL_S*1.1}
            print(filename,seed,record["methods"],flush=True)
            rows.append(record)
    report={"source_sha": SOURCE, "benchmark_sha":os.environ.get("GITHUB_SHA"),
            "ortools":ortools.__version__, "python":sys.version.split()[0],
            "settings":{"seeds":SEEDS,"inputs":FILES,"comparison":"equal allocated total time, not exact enforced wall clock",
                        "heuristic":"LACE shipped heuristic_01 only; does not optimize portfolio",
                        "num_search_workers":1},
            "rows":rows}
    output=Path("results/tmp/psp-warm-hint-heldout.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,allow_nan=False))
    print("RESULT",output,flush=True)


if __name__=="__main__":
    main()
