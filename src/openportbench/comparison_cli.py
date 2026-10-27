"""Standalone PSP comparison without requiring the LACE upstream checkout.

The publication-quality LACE tournament is scripts/solver_matrix.py, which
also invokes the independently pinned LACE objective evaluator.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

from .benchkit import METHODS, strict_refine, sanitize
from .psp import read_instance, evaluate, empty_solution
from .solvers import greedy

DEFAULT=("warm-cp-sat","fix-optimize-cp-sat",
         "restricted-highs-milp","adaptive-ruin-recreate")


def read_initial(path):
    payload=json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload,dict) and "solution" in payload:
        payload=payload["solution"]
    keys=("vessel_assignments","inbound_tugboats","outbound_tugboats")
    if not isinstance(payload,dict) or set(payload)!=set(keys):
        raise ValueError("Not a full PSP schedule")
    return {key:{int(k):v for k,v in payload[key].items()} for key in keys}


def compare(a, *, methods=DEFAULT, seconds=3., seed=1,
            initial=None, baseline="empty", solutions=False):
    if not methods or len(methods)!=len(set(methods)) or any(m not in METHODS for m in methods):
        raise ValueError("Methods must be unique and registered")
    if not seconds>0:
        raise ValueError("Budget must be positive")
    start=time.perf_counter()
    if initial is not None:
        source=initial
        source_name="verified-input"
    elif baseline=="empty":
        source=empty_solution(a)
        source_name="all-unserved"
    elif baseline in ("fcfs","priority"):
        source=greedy(a,order=baseline)
        source_name=baseline
    else:
        raise ValueError("Unknown construction baseline")
    score=evaluate(a,source)
    source_wall=time.perf_counter()-start
    outcome={}
    for method in methods:
        candidate=strict_refine(a,source,method,seconds,seed)
        evaluate(a,candidate["solution"])
        outcome[method]=candidate if solutions else sanitize(candidate)
    return {
        "protocol":"PSP-standalone-strict-comparison-v1",
        "disclaimer":"Independent PSP validation only. For formally archived scores "
                     "use scripts/solver_matrix.py with the original LACE verifier.",
        "source":{"method":source_name,"objective":score,"wall_s":source_wall},
        "hard_refinement_s":seconds,"seed":seed,"methods":outcome,
        "environment":{"python":sys.version.split()[0],"platform":platform.platform()},
    }


def main(argv=None):
    p=argparse.ArgumentParser(description="Fair strict-wall solver comparison on one PSP file")
    p.add_argument("instance")
    p.add_argument("--methods",default=",".join(DEFAULT))
    p.add_argument("--seconds",type=float,default=3.)
    p.add_argument("--seed",type=int,default=1)
    p.add_argument("--baseline",choices=["empty","fcfs","priority"],default="empty")
    p.add_argument("--initial-json",default=None)
    p.add_argument("--include-solutions",action="store_true")
    p.add_argument("--output",default=None)
    args=p.parse_args(argv)
    path=Path(args.instance)
    a=read_instance(path)
    s=read_initial(args.initial_json) if args.initial_json else None
    doc=compare(a,methods=tuple(args.methods.split(",")),seconds=args.seconds,
                seed=args.seed,initial=s,baseline=args.baseline,
                solutions=args.include_solutions)
    doc.update(input_path=str(path),input_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    for method,r in doc["methods"].items():
        print(f"{method:27} {r['status']:12} objective={r['objective']:.4f} "
              f"wall={r['wall_s']:.3f}s improved={r['improved']}")
    if args.output:
        output=Path(args.output)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(doc,indent=2,sort_keys=True,allow_nan=False)+"\n")
        print(f"Machine-readable results: {output}")
    return doc


if __name__=="__main__":
    main()
