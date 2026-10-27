"""Restricted time-indexed set-packing MILP for *the same* LACE PSP.

This is an independent solver *family* (SciPy/HiGHS MILP), not a reformulation
that retains all feasible solutions. It optimizes exactly over a bounded set of
complete per-vessel schedules (columns), including a verified initial incumbent.

Every column models *both* tug services, berth, full intervals and objective.
Unlike the complete CP-SAT model, global optimality in this restricted master
does not establish global PSP optimality.
"""
from __future__ import annotations

from itertools import combinations
import math
import time

from .psp import evaluate


def _teams(instance: dict, i: int, limit: int = 3):
    powers = instance["tugboat_horsepower"]
    costs = instance["tugboat_costs"]
    count = instance["max_tugboats_per_service"]
    need = instance["vessel_horsepower_requirements"][i]
    eligible = []
    for length in range(1, min(count, len(powers)) + 1):
        for team in combinations(range(len(powers)), length):
            if sum(powers[k] for k in team) >= need:
                eligible.append((sum(costs[k] for k in team), team))
    eligible.sort(key=lambda v: (v[0], len(v[1]), v[1]))
    return [team for _, team in eligible[:limit]]


def _vessel_cost(a: dict, i: int, t_in: int, t_out: int,
                 team_in: tuple[int, ...], team_out: tuple[int, ...]) -> float:
    weights = a["objective_weights"]
    priority = a["vessel_priority_weights"][i]
    d_in = a["vessel_inbound_service_times"][i]
    d_out = a["vessel_outbound_service_times"][i]
    z_wait = priority * a["vessel_waiting_costs"][i] * (t_out + d_out - t_in)
    z_jit = priority * a["vessel_jit_costs"][i] * abs(t_in-a["vessel_etas"][i])
    z_tug = sum(a["tugboat_costs"][k] * d_in for k in team_in) + sum(
        a["tugboat_costs"][k] * d_out for k in team_out)
    return weights[1]*z_wait + weights[2]*z_jit + weights[3]*z_tug


def _pattern(i, berth, berth_start, t_in, t_out, team_in, team_out, a):
    if berth is None:
        penalty = (a["objective_weights"][0] * a["penalty_parameter"]
                   * a["vessel_priority_weights"][i])
        return (None, (), float(penalty))
    d_in = a["vessel_inbound_service_times"][i]
    d_out = a["vessel_outbound_service_times"][i]
    d_berth = a["vessel_durations"][i]
    resources = [("berth", berth, t) for t in range(berth_start, berth_start+d_berth)]
    for t in range(t_in, t_in+d_in+a["inbound_preparation_time"]):
        resources.extend(("tug", k, t) for k in team_in)
    for t in range(t_out, t_out+d_out+a["outbound_preparation_time"]):
        resources.extend(("tug", k, t) for k in team_out)
    return (
        (berth, berth_start, t_in, t_out, tuple(team_in), tuple(team_out)),
        tuple(resources),
        float(_vessel_cost(a, i, t_in, t_out, tuple(team_in), tuple(team_out))),
    )


def _incumbent_pattern(i, a, solution):
    place = solution["vessel_assignments"][i]
    if place is None:
        return _pattern(i, None, None, None, None, (), (), a)
    return _pattern(i, place[0], place[1],
                    solution["inbound_tugboats"][i][0][1],
                    solution["outbound_tugboats"][i][0][1],
                    tuple(k for k, _ in solution["inbound_tugboats"][i]),
                    tuple(k for k, _ in solution["outbound_tugboats"][i]), a)


def columns_for_vessel(a: dict, i: int, incumbent: dict,
                       max_columns: int = 24, team_options: int = 2):
    """Diverse bounded columns. Original incumbent ALWAYS retained."""
    if max_columns < 2:
        raise ValueError("max_columns must be >= 2")
    incumbent_pattern = _incumbent_pattern(i, a, incumbent)
    candidates = {incumbent_pattern[0]: incumbent_pattern}
    none = _pattern(i, None, None, None, None, (), (), a)
    candidates[None] = none
    teams = _teams(a, i, limit=team_options)
    if not teams:
        return list(candidates.values())
    eta = a["vessel_etas"][i]
    earliest = max(0, eta-a["vessel_early_limits"][i])
    latest = min(a["time_periods"]-1, eta+a["vessel_late_limits"][i])
    incumbent_start = (incumbent_pattern[0][2] if incumbent_pattern[0] is not None
                       else eta)
    start_choices = {earliest, latest, max(earliest, min(latest, eta)),
                     max(earliest, min(latest, incumbent_start))}
    for delta in (-2, -1, 1, 2):
        start_choices.add(max(earliest, min(latest, incumbent_start+delta)))
    epsilon = a["time_constraint_tolerance"]
    berth_gap_choices = {0, epsilon}
    outbound_gap_choices = {0, epsilon}
    # Enumerate up to a modest number of compatible berths, choosing capacity
    # fit first and preserving incumbent berth as an option.
    fit_berths = [b for b, capacity in enumerate(a["berth_capacities"])
                  if capacity >= a["vessel_sizes"][i]]
    fit_berths.sort(key=lambda b: (a["berth_capacities"][b], b))
    chosen_berths = fit_berths[:min(len(fit_berths), 4)]
    if incumbent_pattern[0] is not None:
        berth = incumbent_pattern[0][0]
        if berth not in chosen_berths:
            chosen_berths.append(berth)
    for t_in in sorted(start_choices):
        for gap_in in berth_gap_choices:
            t_berth = t_in + a["vessel_inbound_service_times"][i] + gap_in
            if not 0 <= t_berth < a["time_periods"]:
                continue
            for gap_out in outbound_gap_choices:
                t_out = t_berth + a["vessel_durations"][i] + gap_out
                if t_out+a["vessel_outbound_service_times"][i] > a["time_periods"]:
                    continue
                for berth in chosen_berths:
                    for in_team in teams:
                        for out_team in teams:
                            pat = _pattern(i, berth, t_berth, t_in, t_out,
                                           in_team, out_team, a)
                            candidates[pat[0]] = pat
    fixed = ([incumbent_pattern] if incumbent_pattern[0] is None\n             else [incumbent_pattern, none])\n    slots = max_columns - len(fixed)
    # Retain low-cost schedules but promote diversity across starts/berths.
    ranked = sorted((v for key, v in candidates.items()
                     if key not in {None, incumbent_pattern[0]}),
                    key=lambda v: (v[2], v[0]))
    chosen = []
    used = set()
    # Reserve one option for each (arrival, berth), then fill by cost.
    for item in ranked:
        signature = (item[0][0], item[0][2])
        if signature not in used:
            used.add(signature)
            chosen.append(item)
        if len(chosen) >= slots:
            break
    chosen_keys = {item[0] for item in chosen}
    for item in ranked:
        if len(chosen) >= slots:
            break
        if item[0] not in chosen_keys:
            chosen.append(item)
            chosen_keys.add(item[0])
    return fixed + chosen


def _build(a, incumbent, max_columns=24, team_options=2):
    """Sparse exact set partitioning over candidate full-service patterns."""
    from scipy.sparse import coo_matrix
    n = a["vessel_num"]
    patterns, vessel_ids = [], []
    resource_rows = {}
    for i in range(n):
        for pat in columns_for_vessel(a, i, incumbent, max_columns, team_options):
            patterns.append(pat)
            vessel_ids.append(i)
            for resource in pat[1]:
                resource_rows.setdefault(resource, n+len(resource_rows))
    rows, cols, values = [], [], []
    for j, (pat, i) in enumerate(zip(patterns, vessel_ids, strict=True)):
        rows.append(i); cols.append(j); values.append(1.0)
        for resource in pat[1]:
            rows.append(resource_rows[resource])
            cols.append(j)
            values.append(1.0)
    shape = (n+len(resource_rows), len(patterns))
    A = coo_matrix((values, (rows, cols)), shape=shape).tocsr()
    return A, patterns, vessel_ids


def _decode(a, patterns, vessel_ids, chosen):
    from .psp import empty_solution
    s = empty_solution(a)
    for idx in chosen:
        description = patterns[idx][0]
        i = vessel_ids[idx]
        if description is None:
            continue
        berth, berth_start, t_in, t_out, team_in, team_out = description
        s["vessel_assignments"][i] = [berth, berth_start]
        s["inbound_tugboats"][i] = [[k, t_in] for k in team_in]
        s["outbound_tugboats"][i] = [[k, t_out] for k in team_out]
    return s


def pattern_milp(a: dict, incumbent: dict, *, seconds: float = 3.,
                 max_columns: int = 24, team_options: int = 2) -> dict:
    """Solve restricted HiGHS MILP; fall back to verified incumbent.

    Time bound is advisory until called through a strict process deadline.
    """
    from scipy.optimize import Bounds, LinearConstraint, milp
    import numpy as np
    started = time.perf_counter()
    initial = evaluate(a, incumbent)
    A, patterns, vessel_ids = _build(a, incumbent, max_columns, team_options)
    build_s = time.perf_counter() - started
    if build_s >= seconds:
        return {"solution": incumbent, "objective": initial, "status": "BUILD_TIMEOUT",
                "master_optimal": False, "columns": len(patterns),
                "wall_s": time.perf_counter() - started, "build_s": build_s}
    lower = np.concatenate((np.ones(a["vessel_num"]),
                             np.full(A.shape[0]-a["vessel_num"], -np.inf)))
    upper = np.ones(A.shape[0])
    c = np.array([p[2] for p in patterns], dtype=float)
    r = milp(c=c, integrality=np.ones(len(patterns)),
             bounds=Bounds(np.zeros(len(patterns)), np.ones(len(patterns))),
             constraints=LinearConstraint(A, lower, upper),
             options={"time_limit": max(.01, seconds-build_s)})
    returned = incumbent
    score = initial
    raw_status = int(r.status)
    if r.x is not None:
        select = np.flatnonzero(r.x > .5).tolist()
        if len(select) == a["vessel_num"] and len({vessel_ids[j] for j in select}) == a["vessel_num"]:
            candidate = _decode(a, patterns, vessel_ids, select)
            measured = evaluate(a, candidate)
            if abs(measured - float(c[select].sum())) > 1e-5:
                raise AssertionError("HiGHS pattern MILP disagrees with independent checker")
            if measured < score - 1e-6:
                returned, score = candidate, measured
    return {"solution": returned, "objective": score,
            "status": {0:"MASTER_OPTIMAL",1:"MASTER_LIMIT",2:"MASTER_INFEASIBLE",
                       3:"MASTER_UNBOUNDED",4:"MASTER_ERROR"}.get(raw_status,"MASTER_OTHER"),
            "master_optimal": raw_status==0, "master_best_bound": (
                float(r.mip_dual_bound) if getattr(r,"mip_dual_bound",None) is not None
                and math.isfinite(float(r.mip_dual_bound)) else None),
            "columns": len(patterns), "rows": A.shape[0],
            "wall_s": time.perf_counter()-started, "build_s": build_s}
