"""Strict-budget worker runner: solve process is killed at a wall deadline.

Fork requires Linux/Unix. Caller must validate any returned solution independently.
This isolates advisory-time upstream heuristics without trusting their timers.
"""
from __future__ import annotations
import multiprocessing as mp
import random
import time


def _execute(conn, spec, instance, solver, seconds, seed):
    try:
        random.seed(seed)
        try:
            import numpy as np
            np.random.seed(seed)
        except ImportError:
            pass
        tools = spec.tools(instance)
        start = time.perf_counter()
        solution = solver(instance, tools, seconds)
        if not isinstance(solution, dict):
            raise TypeError("Solver returned non-dict solution")
        feasible, error = tools["is_feasible"](solution)
        score = tools["objective"](solution) if feasible else None
        conn.send({"status": "FEASIBLE" if feasible else "INVALID",
                   "objective": score, "solution": solution if feasible else None,
                   "error": error, "solver_reported_elapsed_s": time.perf_counter()-start})
    except BaseException as exc:
        conn.send({"status": "ERROR", "objective": None,
                   "solution": None, "error": f"{type(exc).__name__}: {exc}"})
    finally:
        conn.close()


def run_hard_deadline(spec, instance, solver, seconds, seed=1):
    """Terminate a solver that fails to return within its full wall budget.

    Timer starts before the worker is launched; includes fork startup and
    results returned through the pipe. Validator time is outside the budget.
    """
    if not seconds > 0:
        raise ValueError("seconds must be positive")
    if "fork" not in mp.get_all_start_methods():
        raise RuntimeError("Strict LACE worker currently requires Unix fork")
    ctx = mp.get_context("fork")
    receiver, sender = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_execute, args=(sender, spec, instance, solver, seconds, seed))
    t0 = time.perf_counter()
    proc.start()
    sender.close()
    deadline = t0 + seconds
    message = None
    # Drain the pipe while the worker is live. Joining before recv() can
    # deadlock on sufficiently large solutions (full OS pipe buffer).
    while time.perf_counter() < deadline:
        remaining = deadline - time.perf_counter()
        if receiver.poll(min(0.02, remaining)):
            try:
                message = receiver.recv()
            except EOFError:
                message = None
            break
        if not proc.is_alive():
            break
    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=1)
        if proc.is_alive():
            proc.kill()
            proc.join()
    else:
        proc.join(timeout=0)
    elapsed = time.perf_counter() - t0
    receiver.close()
    if message is not None:
        message["wall_s"] = elapsed
        return message
    if elapsed >= seconds:
        return {"status": "TIMEOUT", "objective": None, "solution": None,
                "error": "Hard wall-clock deadline exceeded", "wall_s": elapsed}
    return {"status": "ERROR", "objective": None, "solution": None,
            "error": f"Worker exited {proc.exitcode} without returning data", "wall_s": elapsed}
