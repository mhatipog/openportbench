"""Diagnostic repeat: LACE with true hard wall limits, not advisory limits.

Already-exposed test inputs are used deliberately ONLY for benchmark-audit,
not as unseen validation for a tuned solver.
"""
import hashlib
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

from openportbench.psp import evaluate
from openportbench.runtime import run_hard_deadline

SHA = "d772b74690075f641be8077e69748ec482e9febf"
CASES = [
    ("train", "20_2_3_T12_001.txt"),
    ("test", "80_10_15_T48_001.txt"),
    ("test", "500_40_100_T48_001.txt"),
]
HARD_BUDGET_SECONDS = 0.5


def main():
    root = Path(os.environ.get("LACE_ROOT", "lace_source")).resolve()
    assert subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                   text=True).strip() == SHA
    sys.path.insert(0, str(root))
    from lace.framework import load_heuristic
    spec = importlib.import_module("problems.port_scheduling_problem.spec").SPEC
    records = []
    for split, filename in CASES:
        p = root / "problems/port_scheduling_problem/instances" / split / filename
        instance = spec.load_data(str(p))
        out = {"input": filename, "split": split, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
               "n": instance["vessel_num"], "hard_budget_per_heuristic_s": HARD_BUDGET_SECONDS,
               "methods": []}
        for idx in range(1, 11):
            solver = load_heuristic(root / "problems/port_scheduling_problem/portfolio" /
                                    f"heuristic_{idx:02d}.py")
            r = run_hard_deadline(spec, instance, solver, HARD_BUDGET_SECONDS, seed=1)
            if r["status"]=="FEASIBLE":
                own = evaluate(instance, r["solution"])
                if abs(r["objective"]-own)>1e-6:
                    raise AssertionError("Independent evaluation disagreement")
            r.pop("solution")
            out["methods"].append({"method":f"lace-{idx:02d}", **r})
            print(filename,idx,r["status"],r["objective"],round(r["wall_s"],3),flush=True)
        out["best_hard_budget_objective"] = min(
            (v["objective"] for v in out["methods"] if v["status"]=="FEASIBLE"),default=None)
        records.append(out)
    output = Path("results/tmp/psp-hard-timeout-audit.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({"source_sha":SHA,"benchmark_sha":os.environ.get("GITHUB_SHA"),
                                  "status":"diagnostic, previously exposed cases; not a held-out result",
                                  "cases":records},indent=2))
    print("SAVED",output)


if __name__=="__main__":
    main()
