"""Frozen LACE PSP portfolio and independent held-out comparison."""
import argparse
import hashlib
import importlib
import json
import os
import platform
import random
import resource
import subprocess
import sys
import time
from pathlib import Path

from openportbench.psp import evaluate
from openportbench.solvers import cp_sat

LACE_SHA = "d772b74690075f641be8077e69748ec482e9febf"


def environment():
    import ortools
    import numpy
    import scipy
    model = "unknown"
    p = Path("/proc/cpuinfo")
    if p.exists():
        model = next((line.partition(":")[2].strip() for line in
                      p.read_text().splitlines() if line.startswith("model name")), "unknown")
    return {"python": sys.version.split()[0], "platform": platform.platform(),
            "cpu_model": model, "logical_cpu_count": os.cpu_count(),
            "ortools": ortools.__version__, "numpy": numpy.__version__,
            "scipy": scipy.__version__}


def run(args):
    root = Path(os.environ.get("LACE_ROOT", "lace_source")).resolve()
    sha = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                  text=True).strip()
    if sha != LACE_SHA:
        raise ValueError(f"Wrong LACE revision: {sha}")
    sys.path.insert(0, str(root))
    import numpy as np
    from lace.framework import load_heuristic, run_solve
    spec = importlib.import_module("problems.port_scheduling_problem.spec").SPEC
    inputs = sorted((root / "problems/port_scheduling_problem/instances" / args.split).glob("*.txt"))
    grouped = {}
    for path in inputs:
        group = "_".join(path.stem.split("_")[:4])
        grouped.setdefault(group, []).append(path)
    selected = inputs if args.all else [path for group in sorted(grouped)
                                         for path in grouped[group][:args.per_group]]
    if not selected:
        raise ValueError("No PSP cases selected")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    finished = set()
    if args.output.exists():
        for line in args.output.read_text().splitlines():
            r = json.loads(line)
            if r["lace_sha"] != LACE_SHA or r["seconds_per_heuristic"] != args.seconds:
                raise ValueError("Incompatible checkpoint")
            finished.add((r["file"], r["seed"]))
    print("SELECTED", [p.name for p in selected], flush=True)
    for path in selected:
        for seed in args.seeds:
            if (path.name, seed) in finished:
                continue
            inst = spec.load_data(str(path))
            report = {"split": args.split, "file": path.name, "seed": seed,
                      "lace_sha": LACE_SHA, "openportbench_sha": os.environ.get("GITHUB_SHA"),
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "n": inst["vessel_num"], "seconds_per_heuristic": args.seconds,
                      "cp_sat_budget_s": args.seconds * 10,
                      "environment": environment(), "methods": []}
            try:
                for i in range(1, 11):
                    random.seed(seed)
                    np.random.seed(seed)
                    fn = load_heuristic(root / "problems/port_scheduling_problem/portfolio"
                                        / f"heuristic_{i:02d}.py")
                    t = time.perf_counter()
                    c = time.process_time()
                    result = run_solve(spec, inst, fn, time_limit_s=args.seconds)
                    wall = time.perf_counter() - t
                    row = {"name": f"lace-{i:02d}", "status": "FEASIBLE" if result.feasible else "INVALID",
                           "objective": result.objective if result.feasible else None,
                           "wall_s": wall, "cpu_s": time.process_time()-c,
                           "peak_process_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                           "exceeded_advisory_budget": wall > args.seconds * 1.1,
                           "error": result.error_msg}
                    if result.feasible:
                        independent = evaluate(inst, result.solution)
                        if abs(independent - result.objective) > 1e-6:
                            raise AssertionError(f"Independent objective mismatch: {path.name} {i}")
                        row["independently_verified"] = True
                    report["methods"].append(row)
                    print(f"{path.name} seed={seed} {row['name']} {row['objective']}", flush=True)
                if inst["vessel_num"] <= args.cp_max_vessels:
                    t = time.perf_counter()
                    c = time.process_time()
                    exact = cp_sat(inst, seconds=args.seconds * 10, seed=seed)
                    wall = time.perf_counter() - t
                    sol = exact.pop("solution")
                    if sol is not None:
                        score = spec.tools(inst)["objective"](sol)
                        if abs(score - exact["objective"]) > 1e-6:
                            raise AssertionError("Original and independent CP-SAT evaluators disagree")
                    report["methods"].append({"name": "cp-sat", "status": exact["status"],
                        "objective": exact["objective"], "best_bound": exact["best_bound"],
                        "model_and_solve_wall_s": wall, "solver_s": exact["runtime_s"],
                        "cpu_s": time.process_time()-c, "scale": exact["scale"],
                        "peak_process_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                        "checked_by_upstream": sol is not None,
                        "exceeded_allocated_budget": wall > args.seconds * 10 * 1.1})
                else:
                    report["methods"].append({"name": "cp-sat", "status": "SKIPPED_SIZE_CAP",
                                              "objective": None, "best_bound": None})
            except Exception as ex:
                report["error"] = type(ex).__name__ + ": " + str(ex)
                print("ERROR", path.name, str(ex), flush=True)
            with args.output.open("a", encoding="utf-8") as f:
                f.write(json.dumps(report, sort_keys=True, allow_nan=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
    print("FINISHED", args.output, flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--split", choices=["train", "test"], default="test")
    p.add_argument("--seconds", type=float, default=0.15)
    p.add_argument("--per-group", type=int, default=1)
    p.add_argument("--all", action="store_true")
    p.add_argument("--cp-max-vessels", type=int, default=80)
    p.add_argument("--seeds", type=int, nargs="+", default=[1])
    p.add_argument("--output", type=Path, default=Path("results/tmp/psp-heldout.jsonl"))
    a = p.parse_args()
    if a.seconds <= 0 or a.per_group <= 0:
        p.error("Time budget and per-group sample count must be positive")
    run(a)
