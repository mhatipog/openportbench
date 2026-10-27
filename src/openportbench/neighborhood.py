"""Incumbent-preserving, restricted-neighborhood CP-SAT for the full LACE PSP.

All unchanged vessels are represented by their *occupied resource intervals*.
Only selected vessel variables are rebuilt in the exact subproblem. Therefore
each successful move remains feasible for the complete original formulation.

This is a conventional large-neighborhood-search baseline, not a novel
mathematical approximation or implementation of an OpenAI theorem.
"""
from __future__ import annotations

import copy
import random
import time

from .psp import empty_solution, evaluate
from .solvers import cp_sat


def restrict_instance(instance: dict, selected: list[int]) -> dict:
    """Project PSP's per-vessel arrays; keep all system and resource parameters."""
    n = instance["vessel_num"]
    if not selected or len(set(selected)) != len(selected) or any(
        not isinstance(i, int) or not 0 <= i < n for i in selected
    ):
        raise ValueError("Neighborhood must contain distinct valid vessel IDs")
    result = instance.copy()
    result["vessel_num"] = len(selected)
    for key, value in instance.items():
        if key.startswith("vessel_") and isinstance(value, list):
            if len(value) != n:
                raise ValueError(f"Unexpected array shape: {key}")
            result[key] = [value[i] for i in selected]
    return result


def _select(solution: dict, selected: list[int]) -> dict:
    return {
        key: {j: copy.deepcopy(solution[key][i]) for j, i in enumerate(selected)}
        for key in ("vessel_assignments", "inbound_tugboats", "outbound_tugboats")
    }


def _block_unchanged(instance: dict, solution: dict, selected: list[int]):
    """Build exact half-open blocking intervals, including tug preparation."""
    free = set(selected)
    berths = {}
    tugs = {}
    for i in range(instance["vessel_num"]):
        if i in free:
            continue
        place = solution["vessel_assignments"][i]
        if place is None:
            continue
        berth, start = place
        berths.setdefault(berth, []).append(
            (start, start + instance["vessel_durations"][i])
        )
        for kind, duration, preparation in (
            ("inbound_tugboats", instance["vessel_inbound_service_times"][i],
             instance["inbound_preparation_time"]),
            ("outbound_tugboats", instance["vessel_outbound_service_times"][i],
             instance["outbound_preparation_time"]),
        ):
            for tug, start_time in solution[kind][i]:
                tugs.setdefault(tug, []).append(
                    (start_time, start_time + duration + preparation)
                )
    return berths, tugs


def _combine(original: dict, local: dict, selected: list[int]) -> dict:
    candidate = copy.deepcopy(original)
    for j, i in enumerate(selected):
        for key in ("vessel_assignments", "inbound_tugboats", "outbound_tugboats"):
            candidate[key][i] = copy.deepcopy(local[key][j])
    return candidate


def repair_neighborhood(
    instance: dict, incumbent: dict, selected: list[int],
    seconds: float, seed: int = 1,
) -> dict:
    """One *exactly formulated* conditional PSP neighborhood solve.

    The search status and bound apply to the restricted neighborhood only:
    never advertise them as global PSP optimality certificates.
    """
    before = evaluate(instance, incumbent)
    sub = restrict_instance(instance, selected)
    hint = _select(incumbent, selected)
    evaluate(sub, hint)
    berths, tugs = _block_unchanged(instance, incumbent, selected)
    result = cp_sat(sub, seconds=seconds, seed=seed, hint_solution=hint,
                    blocked_berths=berths, blocked_tugs=tugs)
    local = result.pop("solution")
    candidate = _combine(incumbent, local, selected) if local is not None else incumbent
    after = evaluate(instance, candidate)
    if after > before + 1e-6:
        # CP-SAT can return a valid but worse incumbent, which LNS must reject.
        candidate, after = incumbent, before
    return {"solution": candidate, "objective": after, "initial_objective": before,
            "improved": after < before - 1e-6, "selected": list(selected),
            "restricted_solver_status": result["status"],
            "restricted_best_bound": result["best_bound"],
            "incumbent_source": result.get("incumbent_source"),
            "solver_s": result["runtime_s"]}


def improve_psp(
    instance: dict, incumbent: dict, *, seconds: float = 3.,
    seed: int = 1, neighborhood_size: int = 8,
    max_rounds: int = 6,
) -> dict:
    """Anytime bounded-neighborhood repair; never worsens valid incumbents.

    The advisory wall timer includes the repair's model construction, but a
    running CP-SAT solve may exceed the deadline. Use an outer OS process
    timeout when a *hard* end-to-end deadline is required.
    """
    if seconds <= 0 or max_rounds < 1 or neighborhood_size < 1:
        raise ValueError("Positive budget, neighborhood size and rounds required")
    start = time.perf_counter()
    incumbent_objective = evaluate(instance, incumbent)
    best = copy.deepcopy(incumbent)
    best_score = incumbent_objective
    n = instance["vessel_num"]
    k = min(n, neighborhood_size)
    rng = random.Random(seed)
    diagnostics = []
    if n == 0:
        raise ValueError("PSP must contain vessels")
    # Prefer high-penalty unserved vessels as anchors, then vary arrival
    # neighborhoods. This selection is deterministic given a fixed seed.
    unserved = [i for i in range(n) if best["vessel_assignments"][i] is None]
    unserved.sort(key=lambda i: -instance["vessel_priority_weights"][i])
    served = [i for i in range(n) if best["vessel_assignments"][i] is not None]
    rng.shuffle(served)
    anchors = unserved + served
    if not anchors:
        anchors = list(range(n))
    for iteration in range(max_rounds):
        left = seconds - (time.perf_counter() - start)
        if left < 0.16:
            break
        anchor = anchors[iteration % len(anchors)]
        eta = instance["vessel_etas"][anchor]
        ranked = sorted(range(n), key=lambda i: (
            abs(instance["vessel_etas"][i] - eta),
            i != anchor, -instance["vessel_priority_weights"][i], i
        ))
        chosen = sorted(set([anchor] + [i for i in ranked if i != anchor][:k - 1]))
        # Model setup is not covered by solver's timer. Keep a conservative
        # fraction of remaining time for the final validation and merge.
        solver_budget = min(0.8, max(0.08, left * 0.55))
        round_start = time.perf_counter()
        outcome = repair_neighborhood(instance, best, chosen, solver_budget,
                                      seed=seed + iteration)
        spent = time.perf_counter() - round_start
        if outcome["improved"]:
            best = outcome["solution"]
            best_score = outcome["objective"]
        diagnostics.append({
            "round": iteration, "anchor": anchor, "selected": chosen,
            "improved": outcome["improved"], "objective": outcome["objective"],
            "solver_status": outcome["restricted_solver_status"],
            "solver_s": outcome["solver_s"], "wall_s": spent,
        })
    assert abs(evaluate(instance, best) - best_score) < 1e-6
    return {"solution": best, "objective": best_score,
            "initial_objective": incumbent_objective,
            "improved": best_score < incumbent_objective - 1e-6,
            "wall_s": time.perf_counter() - start,
            "rounds": diagnostics, "status": "HEURISTIC_FEASIBLE"}
