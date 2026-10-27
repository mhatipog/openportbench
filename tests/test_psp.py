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
