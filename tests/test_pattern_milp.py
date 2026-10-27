import copy
import pytest
from openportbench.psp import empty_solution, evaluate
from openportbench.pattern_milp import columns_for_vessel, pattern_milp, _build
from test_psp import case


def test_unserved_incumbent_kept_and_column_validation():
    a = case()
    incumbent = empty_solution(a)
    cols = columns_for_vessel(a, 0, incumbent, max_columns=10)
    assert cols[0][0] is None
    assert len(cols) <= 10
    A, choices, vessel_ids = _build(a, incumbent, max_columns=10)
    assert A.shape[1] == len(choices) == len(vessel_ids)
    assert choices[0][0] is None


def test_milp_improves_feasible_schedule_and_matches_independent_score():
    a = case()
    s = empty_solution(a)
    result = pattern_milp(a, s, seconds=3., max_columns=40)
    assert result["status"] in ("MASTER_OPTIMAL","MASTER_LIMIT")
    assert result["master_optimal"] or result["status"]=="MASTER_LIMIT"
    assert evaluate(a, result["solution"]) == pytest.approx(result["objective"])
    assert result["objective"] < evaluate(a, s)


def test_milp_keeps_valid_warm_incumbent_no_regression():
    a = case()
    s = empty_solution(a)
    s["vessel_assignments"][0] = [0, 1]
    s["inbound_tugboats"][0] = [[0, 0]]
    s["outbound_tugboats"][0] = [[0, 3]]
    evaluate(a, s)
    result = pattern_milp(a, s, seconds=2.)
    assert evaluate(a, result["solution"]) == pytest.approx(result["objective"])
    assert result["objective"] <= evaluate(a, s)


def test_intervals_include_outbound_preparation_and_no_tug_collisions():
    a = case()
    s = empty_solution(a)
    result = pattern_milp(a, s, seconds=2., max_columns=40)
    evaluate(a, result["solution"])
    for key in ("inbound_tugboats", "outbound_tugboats"):
        assert set(result["solution"][key]) == {0, 1}


def test_restrict_column_count_and_invalid_config():
    a=case()
    s=empty_solution(a)
    assert len(columns_for_vessel(a,0,s,max_columns=2))==2
    with pytest.raises(ValueError):
        columns_for_vessel(a,0,s,max_columns=1)
