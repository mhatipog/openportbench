import copy
import pytest
from openportbench.psp import evaluate, empty_solution
from openportbench.solvers import greedy


def case():
    return {
        "vessel_num": 2, "berth_num": 1, "tugboat_num": 2, "time_periods": 12,
        "vessel_sizes": [1, 1], "vessel_etas": [0, 0],
        "vessel_durations": [2, 2], "vessel_inbound_service_times": [1, 1],
        "vessel_outbound_service_times": [1, 1],
        "vessel_priority_weights": [2., 1.],
        "vessel_waiting_costs": [1., 1.], "vessel_jit_costs": [1., 1.],
        "vessel_horsepower_requirements": [2, 2],
        "vessel_early_limits": [0, 0], "vessel_late_limits": [1, 1],
        "berth_capacities": [2], "tugboat_horsepower": [2, 2],
        "tugboat_costs": [1., 2.],
        "inbound_preparation_time": 1, "outbound_preparation_time": 1,
        "max_tugboats_per_service": 1, "time_constraint_tolerance": 1,
        "penalty_parameter": 100., "objective_weights": [1., 1., 1., 1.],
    }


def test_empty_penalty():
    a = case()
    assert evaluate(a, empty_solution(a)) == 300.0


def test_greedy_valid():
    a = case()
    for order in ("fcfs", "priority"):
        s = greedy(a, order)
        assert evaluate(a, s) < 300


def test_overlap_and_power_refused():
    a = case()
    s = empty_solution(a)
    s["vessel_assignments"][0] = [0, 1]
    s["inbound_tugboats"][0] = [[0, 0]]
    s["outbound_tugboats"][0] = [[0, 3]]
    assert evaluate(a, s) < 300
    u = copy.deepcopy(s)
    u["vessel_assignments"][1] = [0, 1]
    u["inbound_tugboats"][1] = [[1, 0]]
    u["outbound_tugboats"][1] = [[1, 3]]
    with pytest.raises(ValueError, match="overlap"):
        evaluate(a, u)
    u = copy.deepcopy(s)
    u["inbound_tugboats"][0] = [[0, 0], [1, 0]]
    with pytest.raises(ValueError):
        evaluate(a, u)
    a["vessel_horsepower_requirements"][0] = 5
    with pytest.raises(ValueError, match="horsepower"):
        evaluate(a, s)


def test_tug_preparation_conflict():
    a = case()
    s = empty_solution(a)
    s["vessel_assignments"][0] = [0, 1]
    s["inbound_tugboats"][0] = [[0, 0]]
    s["outbound_tugboats"][0] = [[0, 3]]
    s["vessel_assignments"][1] = [0, 3]
    s["inbound_tugboats"][1] = [[0, 1]]
    s["outbound_tugboats"][1] = [[1, 5]]
    with pytest.raises(ValueError, match="overlap"):
        evaluate(a, s)


def test_cpsat_matches_bruteforce_single_vessel():
    pytest.importorskip("ortools")
    from openportbench.solvers import cp_sat
    a = case()
    a["vessel_num"] = 1
    for key in ("vessel_sizes", "vessel_etas", "vessel_durations",
                "vessel_inbound_service_times", "vessel_outbound_service_times",
                "vessel_priority_weights", "vessel_waiting_costs", "vessel_jit_costs",
                "vessel_horsepower_requirements", "vessel_early_limits", "vessel_late_limits"):
        a[key] = a[key][:1]
    exhaustive = [evaluate(a, empty_solution(a))]
    for tin in range(2):
        for berth_t in range(tin + 1, tin + 3):
            for tout in range(berth_t + 2, berth_t + 4):
                for ki in range(2):
                    for ko in range(2):
                        s = empty_solution(a)
                        s["vessel_assignments"][0] = [0, berth_t]
                        s["inbound_tugboats"][0] = [[ki, tin]]
                        s["outbound_tugboats"][0] = [[ko, tout]]
                        try:
                            exhaustive.append(evaluate(a, s))
                        except ValueError:
                            pass
    r = cp_sat(a, seconds=5, seed=1)
    assert r["status"] == "OPTIMAL"
    assert r["objective"] == pytest.approx(min(exhaustive))
    assert r["best_bound"] == pytest.approx(r["objective"])


@pytest.mark.parametrize("prep", [0, 1, 3])
def test_two_vessel_cp_sat_against_exhaustive_search(prep):
    """Enumerate every team/time/berth decision, including skipping a vessel.

    Checks the *full* model on adversarial preparation gaps, not merely
    whether CP-SAT solutions pass the same checker used in production.
    """
    pytest.importorskip("ortools")
    from openportbench.solvers import cp_sat
    from itertools import product
    a = case()
    a["inbound_preparation_time"] = prep
    a["outbound_preparation_time"] = prep

    def candidates(i):
        yield None
        for tin in range(max(0, a["vessel_etas"][i] - a["vessel_early_limits"][i]),
                         a["vessel_etas"][i] + a["vessel_late_limits"][i] + 1):
            for berth_time in range(tin + a["vessel_inbound_service_times"][i],
                                    tin + a["vessel_inbound_service_times"][i] + a["time_constraint_tolerance"] + 1):
                for out_time in range(berth_time + a["vessel_durations"][i],
                                      berth_time + a["vessel_durations"][i] + a["time_constraint_tolerance"] + 1):
                    if out_time + a["vessel_outbound_service_times"][i] > a["time_periods"]:
                        continue
                    for in_tug, out_tug in product(range(a["tugboat_num"]), repeat=2):
                        yield ([0, berth_time], [[in_tug, tin]], [[out_tug, out_time]])

    best = float("inf")
    for c0, c1 in product(candidates(0), candidates(1)):
        solution = empty_solution(a)
        for i, c in enumerate((c0, c1)):
            if c is not None:
                (solution["vessel_assignments"][i],
                 solution["inbound_tugboats"][i],
                 solution["outbound_tugboats"][i]) = c
        try:
            best = min(best, evaluate(a, solution))
        except ValueError:
            pass
    exact = cp_sat(a, seconds=5, seed=3)
    assert exact["status"] == "OPTIMAL"
    assert exact["objective"] == pytest.approx(best)
    assert exact["best_bound"] == pytest.approx(best)


def test_cp_sat_valid_hint_preserves_optimum():
    pytest.importorskip("ortools")
    from openportbench.solvers import cp_sat
    a = case()
    hint = greedy(a, order="priority")
    assert evaluate(a, hint) < evaluate(a, empty_solution(a))
    cold = cp_sat(a, seconds=5, seed=1)
    warm = cp_sat(a, seconds=5, seed=1, hint_solution=hint)
    assert cold["status"] == warm["status"] == "OPTIMAL"
    assert cold["objective"] == pytest.approx(warm["objective"])
    assert warm["best_bound"] == pytest.approx(warm["objective"])


def test_cp_sat_rejects_invalid_hint():
    pytest.importorskip("ortools")
    from openportbench.solvers import cp_sat
    a = case()
    invalid = empty_solution(a)
    invalid["vessel_assignments"][0] = [0, 0]
    with pytest.raises(ValueError):
        cp_sat(a, seconds=1, hint_solution=invalid)


def test_cp_sat_fallback_incumbent_is_always_feasible():
    pytest.importorskip("ortools")
    from openportbench.solvers import cp_sat
    a = case()
    fallback = greedy(a, "priority")
    r = cp_sat(a, seconds=0.001, seed=2, hint_solution=fallback)
    assert r["solution"] is not None
    assert r["objective"] <= evaluate(a, fallback) + 1e-6
    assert r["incumbent_source"] in ("verified_hint", "cp-sat")
    if r["incumbent_source"] == "verified_hint":
        assert r["status"] != "OPTIMAL"
