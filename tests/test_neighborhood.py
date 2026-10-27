"""Nontrivial LNS tests: full contract, fixed blockers and a brute-force oracle."""
import pytest

from openportbench.neighborhood import (
    _block_unchanged, _combine, _select, improve_psp,
    repair_neighborhood, restrict_instance,
)
from openportbench.psp import empty_solution, evaluate
from openportbench.solvers import cp_sat


def instance():
    return {
        "vessel_num": 3, "berth_num": 1, "tugboat_num": 2, "time_periods": 12,
        "vessel_sizes": [1, 1, 1], "vessel_etas": [0, 1, 2],
        "vessel_durations": [2, 2, 2],
        "vessel_inbound_service_times": [1, 1, 1],
        "vessel_outbound_service_times": [1, 1, 1],
        "vessel_priority_weights": [1., 4., 2.],
        "vessel_waiting_costs": [1., 1., 1.],
        "vessel_jit_costs": [1., 1., 1.],
        "vessel_horsepower_requirements": [3, 3, 3],
        "vessel_early_limits": [0, 0, 0], "vessel_late_limits": [1, 1, 1],
        "berth_capacities": [2], "tugboat_horsepower": [3, 3],
        "tugboat_costs": [1., 2.],
        "inbound_preparation_time": 1, "outbound_preparation_time": 1,
        "max_tugboats_per_service": 1, "time_constraint_tolerance": 1,
        "penalty_parameter": 100., "objective_weights": [1., 1., 1., 1.],
    }


def test_project_and_fixed_interval_accounting():
    a = instance()
    sol = empty_solution(a)
    sol["vessel_assignments"][0] = [0, 1]
    sol["inbound_tugboats"][0] = [[0, 0]]
    sol["outbound_tugboats"][0] = [[0, 3]]
    evaluate(a, sol)
    chosen = [1, 2]
    reduced = restrict_instance(a, chosen)
    assert reduced["vessel_num"] == 2
    assert reduced["vessel_priority_weights"] == [4., 2.]
    assert evaluate(reduced, _select(sol, chosen)) == pytest.approx(600.)
    b, t = _block_unchanged(a, sol, chosen)
    assert b == {0: [(1, 3)]}
    assert t == {0: [(0, 2), (3, 5)]}


def test_lns_fixed_berth_and_tugs_preserve_upstream_constraints():
    a = instance()
    sol = empty_solution(a)
    sol["vessel_assignments"][0] = [0, 1]
    sol["inbound_tugboats"][0] = [[0, 0]]
    sol["outbound_tugboats"][0] = [[0, 3]]
    evaluate(a, sol)
    # Fix vessel 0. Other vessels cannot use its berth or tug intervals.
    r = repair_neighborhood(a, sol, selected=[1, 2], seconds=3, seed=1)
    assert evaluate(a, r["solution"]) == pytest.approx(r["objective"])
    assert r["objective"] <= evaluate(a, sol)
    assert r["solution"]["vessel_assignments"][0] == [0, 1]
    assert r["solution"]["inbound_tugboats"][0] == [[0, 0]]
    assert r["solution"]["outbound_tugboats"][0] == [[0, 3]]


def test_full_neighborhood_recovers_independently_proven_optimum():
    a = instance()
    empty = empty_solution(a)
    exact = cp_sat(a, seconds=5, seed=1)
    assert exact["status"] == "OPTIMAL"
    local = repair_neighborhood(a, empty, selected=[0, 1, 2],
                                seconds=5, seed=1)
    assert local["restricted_solver_status"] == "OPTIMAL"
    assert local["objective"] == pytest.approx(exact["objective"])
    assert local["objective"] == pytest.approx(evaluate(a, local["solution"]))


def test_anytime_repair_never_deteriorates():
    a = instance()
    empty = empty_solution(a)
    first = improve_psp(a, empty, seconds=2.2, seed=6,
                        neighborhood_size=2, max_rounds=3)
    second = improve_psp(a, first["solution"], seconds=1.8, seed=8,
                         neighborhood_size=2, max_rounds=2)
    for r in (first, second):
        assert evaluate(a, r["solution"]) == pytest.approx(r["objective"])
    assert second["objective"] <= first["objective"] <= evaluate(a, empty)


def test_invalid_neighborhood_rejected():
    a = instance()
    with pytest.raises(ValueError):
        restrict_instance(a, [0, 0])
    with pytest.raises(ValueError):
        restrict_instance(a, [3])
    with pytest.raises(ValueError):
        improve_psp(a, empty_solution(a), seconds=-1)


def test_fixed_resource_blocks_are_active():
    a = instance()
    # All horizon berth occupied by a pre-existing vessel; the only free
    # vessel must stay unserved despite potentially favorable penalty.
    a["vessel_num"] = 1
    for name, val in list(a.items()):
        if name.startswith("vessel_") and isinstance(val, list):
            a[name] = val[:1]
    result = cp_sat(a, seconds=2, blocked_berths={0: [(0, 12)]})
    assert result["status"] == "OPTIMAL"
    assert result["solution"]["vessel_assignments"][0] is None
