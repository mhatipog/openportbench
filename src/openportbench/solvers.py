"""Baseline algorithms for the complete discrete LACE PSP problem."""
from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from math import lcm
import time

from .psp import empty_solution, evaluate


def greedy(instance: dict, order: str = "fcfs") -> dict:
    """Construct valid schedules, enumerating berth, time and tug choices.

    FCFS orders by ETA; priority greedily orders by unserved penalty.
    Neither rule sees other vessels' future choices.
    """
    n = instance["vessel_num"]
    solution = empty_solution(instance)
    if order == "fcfs":
        vessels = sorted(range(n), key=lambda i: (instance["vessel_etas"][i], i))
    elif order == "priority":
        vessels = sorted(range(n), key=lambda i: (-instance["vessel_priority_weights"][i], instance["vessel_etas"][i], i))
    else:
        raise ValueError("Unknown greedy order")
    teams = []
    for i in range(n):
        choices = []
        for cnt in range(1, min(instance["max_tugboats_per_service"], instance["tugboat_num"]) + 1):
            for team in combinations(range(instance["tugboat_num"]), cnt):
                if sum(instance["tugboat_horsepower"][k] for k in team) >= instance["vessel_horsepower_requirements"][i]:
                    choices.append(team)
        teams.append(choices)
    for i in vessels:
        current = evaluate(instance, solution)
        best = None
        earliest = max(0, instance["vessel_etas"][i] - instance["vessel_early_limits"][i])
        latest = min(instance["time_periods"] - 1, instance["vessel_etas"][i] + instance["vessel_late_limits"][i])
        for t_in in range(earliest, latest + 1):
            for b in range(t_in + instance["vessel_inbound_service_times"][i],
                           t_in + instance["vessel_inbound_service_times"][i] + instance["time_constraint_tolerance"] + 1):
                if not 0 <= b < instance["time_periods"]:
                    continue
                for t_out in range(b + instance["vessel_durations"][i],
                                   b + instance["vessel_durations"][i] + instance["time_constraint_tolerance"] + 1):
                    if t_out + instance["vessel_outbound_service_times"][i] > instance["time_periods"]:
                        continue
                    for berth in range(instance["berth_num"]):
                        if instance["berth_capacities"][berth] < instance["vessel_sizes"][i]:
                            continue
                        for inbound_team in teams[i]:
                            for outbound_team in teams[i]:
                                solution["vessel_assignments"][i] = [berth, b]
                                solution["inbound_tugboats"][i] = [[k, t_in] for k in inbound_team]
                                solution["outbound_tugboats"][i] = [[k, t_out] for k in outbound_team]
                                try:
                                    score = evaluate(instance, solution)
                                    if score + 1e-9 < current and (best is None or score < best[0] - 1e-9):
                                        best = (score, [berth, b], [[k, t_in] for k in inbound_team], [[k, t_out] for k in outbound_team])
                                except ValueError:
                                    pass
        solution["vessel_assignments"][i] = best[1] if best else None
        solution["inbound_tugboats"][i] = best[2] if best else []
        solution["outbound_tugboats"][i] = best[3] if best else []
    evaluate(instance, solution)
    return solution


def cp_sat(
    instance: dict,
    seconds: float = 5.0,
    seed: int = 1,
    hint_solution: dict | None = None,
    blocked_berths: dict[int, list[tuple[int, int]]] | None = None,
    blocked_tugs: dict[int, list[tuple[int, int]]] | None = None,
) -> dict:
    """Full PSP CP-SAT model, no scenario/choice pruning.

    Integer time exactly matches LACE's discrete-time contract. Decimal
    coefficients are represented rationally, then scaled exactly.
    """
    from ortools.sat.python import cp_model

    model = cp_model.CpModel()
    n, bcount, kcount, horizon = (instance["vessel_num"], instance["berth_num"],
                                   instance["tugboat_num"], instance["time_periods"])
    sizes = instance["vessel_sizes"]
    served, ti, tb, to, dev, berth_assign, xin, xout = [], [], [], [], [], [], [], []
    berth_intervals = [[] for _ in range(bcount)]
    tug_intervals = [[] for _ in range(kcount)]
    cost_terms = []

    lam = [Fraction(str(x)) for x in instance["objective_weights"]]
    costs = []
    for i in range(n):
        a = Fraction(str(instance["vessel_priority_weights"][i]))
        costs.append((
            lam[0] * Fraction(str(instance["penalty_parameter"])) * a,
            lam[1] * a * Fraction(str(instance["vessel_waiting_costs"][i])),
            lam[2] * a * Fraction(str(instance["vessel_jit_costs"][i])),
        ))
    tug_coeff = [lam[3] * Fraction(str(x)) for x in instance["tugboat_costs"]]
    scale = 1
    for c in [v for cs in costs for v in cs] + tug_coeff:
        scale = lcm(scale, c.denominator)
        if scale > 1_000_000_000:
            raise ValueError("Objective requires a scale >1e9; refusing lossy rounding")
    for i in range(n):
        active = model.new_bool_var(f"served_{i}")
        served.append(active)
        s_in = model.new_int_var(0, horizon - 1, f"in_{i}")
        s_b = model.new_int_var(0, horizon - 1, f"berth_{i}")
        s_out = model.new_int_var(0, horizon - 1, f"out_{i}")
        for v in (s_in, s_b, s_out):
            model.add(v == 0).only_enforce_if(active.Not())
        ti.append(s_in); tb.append(s_b); to.append(s_out)
        model.add(s_in >= instance["vessel_etas"][i] - instance["vessel_early_limits"][i]).only_enforce_if(active)
        model.add(s_in <= instance["vessel_etas"][i] + instance["vessel_late_limits"][i]).only_enforce_if(active)
        model.add(s_b >= s_in + instance["vessel_inbound_service_times"][i]).only_enforce_if(active)
        model.add(s_b <= s_in + instance["vessel_inbound_service_times"][i] + instance["time_constraint_tolerance"]).only_enforce_if(active)
        model.add(s_out >= s_b + instance["vessel_durations"][i]).only_enforce_if(active)
        model.add(s_out <= s_b + instance["vessel_durations"][i] + instance["time_constraint_tolerance"]).only_enforce_if(active)
        model.add(s_out + instance["vessel_outbound_service_times"][i] <= horizon).only_enforce_if(active)
        shift = model.new_int_var(-horizon * 2, horizon * 2, f"shift_{i}")
        model.add(shift == s_in - instance["vessel_etas"][i] * active)
        delta = model.new_int_var(0, horizon * 2, f"deviation_{i}")
        model.add_abs_equality(delta, shift)
        dev.append(delta)

        placements = []
        for b in range(bcount):
            if instance["berth_capacities"][b] < sizes[i]:
                continue
            lit = model.new_bool_var(f"v{i}_berth{b}")
            placements.append((b, lit))
            berth_intervals[b].append(model.new_optional_interval_var(
                s_b, instance["vessel_durations"][i],
                s_b + instance["vessel_durations"][i], lit, f"berth_{i}_{b}"))
        model.add(sum(lit for _, lit in placements) == active)
        berth_assign.append(placements)
        directions = []
        for kind, start, duration, prep in (
            ("in", s_in, instance["vessel_inbound_service_times"][i], instance["inbound_preparation_time"]),
            ("out", s_out, instance["vessel_outbound_service_times"][i], instance["outbound_preparation_time"]),
        ):
            flags = []
            for k in range(kcount):
                lit = model.new_bool_var(f"{kind}_{i}_{k}")
                flags.append(lit)
                tug_intervals[k].append(model.new_optional_interval_var(
                    start, duration + prep, start + duration + prep, lit, f"{kind}_{i}_{k}"))
                cost_terms.append((lit, int(tug_coeff[k] * duration * scale)))
            model.add(sum(flags) >= active)
            model.add(sum(flags) <= instance["max_tugboats_per_service"] * active)
            model.add(sum(instance["tugboat_horsepower"][k] * flags[k] for k in range(kcount))
                      >= instance["vessel_horsepower_requirements"][i] * active)
            directions.append(flags)
        xin.append(directions[0]); xout.append(directions[1])
        penalty, port, jit = [int(c * scale) for c in costs[i]]
        cost_terms.extend([
            (1 - active, penalty),
            (s_out - s_in + instance["vessel_outbound_service_times"][i] * active, port),
            (delta, jit),
        ])
    # Fixed intervals are occupied by vessels outside a restricted-search
    # neighborhood. They are not model decisions; the problem's variable
    # vessels retain every original PSP constraint and its exact objective.
    for kind, restrictions, buckets in (
        ("berth", blocked_berths or {}, berth_intervals),
        ("tug", blocked_tugs or {}, tug_intervals),
    ):
        for resource_id, windows in restrictions.items():
            if not 0 <= resource_id < len(buckets):
                raise ValueError(f"Invalid blocked {kind} ID: {resource_id}")
            for idx, (start, end) in enumerate(windows):
                if not (isinstance(start, int) and isinstance(end, int)
                        and 0 <= start < end):
                    raise ValueError(f"Invalid blocked {kind} interval: {start, end}")
                buckets[resource_id].append(model.new_fixed_size_interval_var(
                    start, end - start, f"fixed_{kind}_{resource_id}_{idx}"
                ))
    for intervals in berth_intervals + tug_intervals:
        model.add_no_overlap(intervals)
    # Safe incumbent injection: a complete, independently verified PSP
    # schedule. CP-SAT hints are guidance only, never hard fixing.
    if hint_solution is not None:
        evaluate(instance, hint_solution)
        for i in range(n):
            place = hint_solution["vessel_assignments"][i]
            active = int(place is not None)
            model.add_hint(served[i], active)
            model.add_hint(ti[i], hint_solution["inbound_tugboats"][i][0][1] if active else 0)
            model.add_hint(tb[i], place[1] if active else 0)
            model.add_hint(to[i], hint_solution["outbound_tugboats"][i][0][1] if active else 0)
            model.add_hint(dev[i], abs(hint_solution["inbound_tugboats"][i][0][1] - instance["vessel_etas"][i]) if active else 0)
            for berth, lit in berth_assign[i]:
                model.add_hint(lit, int(active and berth == place[0]))
            in_team = {pair[0] for pair in hint_solution["inbound_tugboats"][i]}
            out_team = {pair[0] for pair in hint_solution["outbound_tugboats"][i]}
            for k in range(kcount):
                model.add_hint(xin[i][k], int(k in in_team))
                model.add_hint(xout[i][k], int(k in out_team))

    model.minimize(sum(expr * coeff for expr, coeff in cost_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = seed
    t0 = time.perf_counter()
    status = solver.solve(model)
    elapsed = time.perf_counter() - t0
    result = empty_solution(instance)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for i in range(n):
            if not solver.value(served[i]):
                continue
            berth = next(b for b, lit in berth_assign[i] if solver.value(lit))
            result["vessel_assignments"][i] = [berth, solver.value(tb[i])]
            result["inbound_tugboats"][i] = [[k, solver.value(ti[i])] for k in range(kcount) if solver.value(xin[i][k])]
            result["outbound_tugboats"][i] = [[k, solver.value(to[i])] for k in range(kcount) if solver.value(xout[i][k])]
        check = evaluate(instance, result)
        if abs(check - solver.objective_value / scale) > 1e-6:
            raise AssertionError(f"CP-SAT objective disagreement: checker={check} model={solver.objective_value / scale}")
    solver_feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    solver_objective = evaluate(instance, result) if solver_feasible else None
    selected_solution = result if solver_feasible else None
    source = "cp-sat" if solver_feasible else None
    # A hint is an independently feasible incumbent, whether or not the
    # solver explores the hinted assignment before the deadline. Preserve it.
    if hint_solution is not None:
        incumbent_obj = evaluate(instance, hint_solution)
        if (not solver_feasible or incumbent_obj < solver_objective - 1e-6):
            if status == cp_model.OPTIMAL:
                raise AssertionError("Verified incumbent undercuts a claimed optimum")
            selected_solution = hint_solution
            source = "verified_hint"
    return {
        "status": solver.status_name(status),  # raw CP-SAT proof/search status
        "solution": selected_solution,
        "objective": evaluate(instance, selected_solution) if selected_solution is not None else None,
        "solver_objective": solver_objective,  # may be None even with a hint
        "incumbent_source": source,
        "best_bound": solver.best_objective_bound / scale if status in (cp_model.OPTIMAL, cp_model.FEASIBLE, cp_model.UNKNOWN) else None,
        "runtime_s": elapsed,
        "seed": seed,
        "scale": scale,
    }
