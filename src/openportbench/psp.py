"""Independent implementation of the LACE port-scheduling evaluator.

Uses only the publicly documented problem contract, not LACE's config.py.
A result is invalid unless every constraint passes before scoring.
"""
from __future__ import annotations

import ast
import math
from pathlib import Path


def read_instance(path: str | Path) -> dict:
    """Read the LACE key = Python-literal PSP format without executing code."""
    data = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            raise ValueError(f"Unrecognized instance line: {line}")
        key = key.strip()
        if not key.isidentifier() or key in data:
            raise ValueError(f"Duplicate/invalid key {key}")
        data[key] = ast.literal_eval(value.strip())
    return data


def empty_solution(instance: dict) -> dict:
    n = instance["vessel_num"]
    return {
        "vessel_assignments": {i: None for i in range(n)},
        "inbound_tugboats": {i: [] for i in range(n)},
        "outbound_tugboats": {i: [] for i in range(n)},
    }


def evaluate(instance: dict, solution: dict) -> float:
    """Return the exact four-term PSP objective, or raise ValueError.

    Intervals are half-open [start, end); tug preparation counts as occupied.
    In particular prep may extend beyond the planning horizon, as in LACE.
    """
    n, j_count, k_count, horizon = (
        instance["vessel_num"], instance["berth_num"],
        instance["tugboat_num"], instance["time_periods"],
    )
    keys = ("vessel_assignments", "inbound_tugboats", "outbound_tugboats")
    if not isinstance(solution, dict) or set(solution) != set(keys):
        raise ValueError("Solution must have exactly the three PSP keys")
    for key in keys:
        if not isinstance(solution[key], dict) or set(solution[key]) != set(range(n)):
            raise ValueError(f"Invalid vessel index set in {key}")
    va, inbound, outbound = (solution[key] for key in keys)
    berth_occ = [[] for _ in range(j_count)]
    tug_occ = [[] for _ in range(k_count)]
    z1 = z2 = z3 = z4 = 0.0

    for i in range(n):
        place, ins, outs = va[i], inbound[i], outbound[i]
        if place is None:
            if ins or outs:
                raise ValueError(f"Unserved vessel {i} has tug bookings")
            z1 += instance["penalty_parameter"] * instance["vessel_priority_weights"][i]
            continue
        if not isinstance(place, list) or len(place) != 2:
            raise ValueError(f"Invalid berth assignment for vessel {i}")
        berth, t_berth = place
        if not isinstance(berth, int) or not 0 <= berth < j_count:
            raise ValueError("Invalid berth")
        if not isinstance(t_berth, int) or not 0 <= t_berth < horizon:
            raise ValueError("Invalid berth start")
        if instance["vessel_sizes"][i] > instance["berth_capacities"][berth]:
            raise ValueError("Incompatible berth")

        service_starts = []
        for pairs, kind in ((ins, "in"), (outs, "out")):
            if not isinstance(pairs, list) or not 1 <= len(pairs) <= instance["max_tugboats_per_service"]:
                raise ValueError(f"Invalid {kind} team size")
            if any(not isinstance(p, list) or len(p) != 2 for p in pairs):
                raise ValueError("Invalid tug assignment pair")
            if any(not isinstance(k, int) or not 0 <= k < k_count or
                   not isinstance(t, int) or not 0 <= t < horizon for k, t in pairs):
                raise ValueError("Invalid tug ID or service time")
            starts = {t for _, t in pairs}
            if len(starts) != 1:
                raise ValueError("Team does not start simultaneously")
            if len({k for k, _ in pairs}) != len(pairs):
                raise ValueError("Duplicate tug in same team")
            if sum(instance["tugboat_horsepower"][k] for k, _ in pairs) < instance["vessel_horsepower_requirements"][i]:
                raise ValueError("Insufficient team horsepower")
            service_starts.append(next(iter(starts)))
            duration = instance["vessel_inbound_service_times"][i] if kind == "in" else instance["vessel_outbound_service_times"][i]
            prep = instance["inbound_preparation_time"] if kind == "in" else instance["outbound_preparation_time"]
            for k, t in pairs:
                tug_occ[k].append((t, t + duration + prep))
                z4 += instance["tugboat_costs"][k] * duration

        t_in, t_out = service_starts
        eta = instance["vessel_etas"][i]
        if not (eta - instance["vessel_early_limits"][i] <= t_in <= eta + instance["vessel_late_limits"][i]):
            raise ValueError("Inbound arrival window violated")
        d_in = instance["vessel_inbound_service_times"][i]
        d_berth = instance["vessel_durations"][i]
        d_out = instance["vessel_outbound_service_times"][i]
        tolerance = instance["time_constraint_tolerance"]
        if not (0 <= t_berth - (t_in + d_in) <= tolerance):
            raise ValueError("Inbound-to-berth transition violated")
        if not (0 <= t_out - (t_berth + d_berth) <= tolerance):
            raise ValueError("Berth-to-outbound transition violated")
        if t_out + d_out > horizon:
            raise ValueError("Outbound service beyond horizon")
        berth_occ[berth].append((t_berth, t_berth + d_berth))
        alpha = instance["vessel_priority_weights"][i]
        z2 += alpha * instance["vessel_waiting_costs"][i] * (t_out + d_out - t_in)
        z3 += alpha * instance["vessel_jit_costs"][i] * abs(t_in - eta)

    for resource in [*berth_occ, *tug_occ]:
        resource.sort()
        if any(resource[p][1] > resource[p + 1][0] for p in range(len(resource) - 1)):
            raise ValueError("Resource overlap")
    weights = instance["objective_weights"]
    obj = sum(w * z for w, z in zip(weights, (z1, z2, z3, z4), strict=True))
    if not math.isfinite(obj):
        raise ValueError("Nonfinite objective")
    return float(obj)
