"""Run PSP baselines on a LACE-format instance file."""
import argparse
import json
import platform
import sys
from .psp import read_instance, evaluate
from .solvers import greedy, cp_sat


def main():
    p = argparse.ArgumentParser()
    p.add_argument("instance", help="LACE PSP text file")
    p.add_argument("--method", choices=["fcfs", "priority", "cp-sat"], default="cp-sat")
    p.add_argument("--seconds", type=float, default=5.0)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()
    instance = read_instance(args.instance)
    if args.method == "cp-sat":
        result = cp_sat(instance, seconds=args.seconds, seed=args.seed)
    else:
        import time
        t0 = time.perf_counter()
        solution = greedy(instance, order=args.method)
        result = {"status": "FEASIBLE_UNPROVEN", "objective": evaluate(instance, solution),
                  "best_bound": None, "runtime_s": time.perf_counter() - t0, "solution": solution}
    result["method"] = args.method
    result["instance"] = args.instance
    result["environment"] = {"python": sys.version, "platform": platform.platform()}
    if args.method == "cp-sat":
        import ortools
        result["environment"]["ortools"] = ortools.__version__
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
