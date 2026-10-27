"""Common PSP solver interface and strict, same-budget comparison harness.

All refiners accept the same independently verified incumbent. The entire
method runs in a separately timed Unix worker; no method may exceed the
benchmark wall deadline or silently return a late improved result.
"""
from __future__ import annotations

import multiprocessing as mp
import random
import time

from .psp import evaluate

METHODS = ("warm-cp-sat", "fix-optimize-cp-sat", "restricted-highs-milp", "identity")


def refine(instance: dict, incumbent: dict, method: str, seconds: float, seed: int):
    if method == "warm-cp-sat":
        from .solvers import cp_sat
        return cp_sat(instance, seconds=seconds, seed=seed, hint_solution=incumbent)
    if method == "fix-optimize-cp-sat":
        from .neighborhood import improve_psp
        return improve_psp(instance, incumbent, seconds=seconds, seed=seed,
                           neighborhood_size=14, max_rounds=10)
    if method == "restricted-highs-milp":
        from .pattern_milp import pattern_milp
        return pattern_milp(instance, incumbent, seconds=seconds,
                            max_columns=24, team_options=2)
    if method == "identity":
        return {"solution": incumbent, "status": "UNCHANGED", "objective": evaluate(instance, incumbent)}
    raise ValueError(f"Unknown solver: {method}")


def _worker(conn, instance, incumbent, method, seconds, seed):
    try:
        random.seed(seed)
        start = time.perf_counter()
        result = refine(instance, incumbent, method, seconds, seed)
        score = evaluate(instance, result["solution"])
        if abs(score - result["objective"]) > 1e-5:
            raise ValueError("Method's objective does not match independent validator")
        data = {key: value for key, value in result.items()
                if key not in ("solution", "rounds")}
        data.update({"solution": result["solution"], "objective": score,
                     "reported_elapsed_s": time.perf_counter()-start})
        conn.send({"status": "SUCCESS", "result": data})
    except BaseException as exc:
        conn.send({"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"})
    finally:
        conn.close()


def strict_refine(instance: dict, incumbent: dict, method: str,
                  seconds: float, seed: int = 1) -> dict:
    """Parent independently validates worker output or preserves the incumbent.

    Worker status `TIMEOUT` is distinct from mathematical infeasibility and
    from CP-SAT's `UNKNOWN`. A timed-out optimization has no accepted late
    result; fallback objective remains feasible, but method is marked failed.
    """
    if method not in METHODS or seconds <= 0:
        raise ValueError("Invalid method or wall budget")
    initial = evaluate(instance, incumbent)
    if "fork" not in mp.get_all_start_methods():
        raise RuntimeError("Strict benchmarking currently requires Unix fork")
    ctx = mp.get_context("fork")
    receiver, sender = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_worker,
                       args=(sender, instance, incumbent, method, seconds, seed))
    start = time.perf_counter()
    proc.start()
    sender.close()
    deadline = start+seconds
    message = None
    while time.perf_counter() < deadline:
        if receiver.poll(max(0, min(0.02, deadline-time.perf_counter()))):
            try:
                message = receiver.recv()
            except EOFError:
                break
            break
        if not proc.is_alive():
            break
    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=0.25)
        if proc.is_alive():
            proc.kill()
            proc.join()
    else:
        proc.join(timeout=0)
    elapsed = time.perf_counter()-start
    receiver.close()
    record = {
        "method": method, "seed": seed, "hard_wall_budget_s": seconds,
        "wall_s": elapsed, "initial_objective": initial,
        "objective": initial, "improved": False, "solution": incumbent,
        "solver_status": None, "valid": True, "error": None,
    }
    if message is None:
        record["status"] = "TIMEOUT" if elapsed >= seconds else "WORKER_ERROR"
        record["error"] = ("Hard wall-clock deadline exceeded" if elapsed >= seconds
                           else f"Worker exited {proc.exitcode} without output")
        return record
    if message["status"] != "SUCCESS":
        record["status"] = "ERROR"
        record["error"] = message.get("error")
        return record
    candidate = message["result"]["solution"]
    try:
        score = evaluate(instance, candidate)
        if abs(score-message["result"]["objective"]) > 1e-5:
            raise ValueError("Objective mismatch in parent")
        if score < initial - 1e-6:
            record.update(solution=candidate, objective=score, improved=True)
        elif score > initial + 1e-6:
            raise ValueError("Optimizer returned a solution worse than incumbent")
        record["status"] = "FEASIBLE"
        record["solver_status"] = message["result"].get("status")
        record["source"] = message["result"].get("incumbent_source")
        record["reported_elapsed_s"] = message["result"].get("reported_elapsed_s")
        record["master_optimal"] = message["result"].get("master_optimal")
        record["full_cp_sat_bound"] = (
            message["result"].get("best_bound") if method == "warm-cp-sat" else None)
        record["candidate_columns"] = message["result"].get("columns")
        return record
    except (ValueError, AssertionError) as exc:
        record["status"] = "INVALID"
        record["error"] = str(exc)
        record["valid"] = False
        return record


def sanitize(record: dict) -> dict:
    """Persist only benchmark measures; never huge Python-keyed solutions."""
    return {k:v for k,v in record.items() if k != "solution"}
