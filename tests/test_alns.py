import pytest
from openportbench.alns import alns_psp
from openportbench.psp import empty_solution, evaluate
from test_psp import case


def test_alns_can_find_feasible_schedule_with_no_milp_or_cp_sat():
    a=case()
    s=empty_solution(a)
    r=alns_psp(a,s,seconds=1.5,seed=1,max_steps=100)
    assert r["status"]=="HEURISTIC_FEASIBLE"
    assert evaluate(a,r["solution"])==pytest.approx(r["objective"])
    assert r["objective"]<evaluate(a,s)
    assert r["steps"]>0


def test_alns_does_not_worsen_or_violate_resource_rules():
    a=case()
    s=empty_solution(a)
    s["vessel_assignments"][0]=[0,1]
    s["inbound_tugboats"][0]=[[0,0]]
    s["outbound_tugboats"][0]=[[0,3]]
    evaluate(a,s)
    for seed in (1,2,3):
        r=alns_psp(a,s,seconds=.8,seed=seed,max_steps=80)
        assert evaluate(a,r["solution"])==pytest.approx(r["objective"])
        assert r["objective"]<=evaluate(a,s)


def test_alns_invalid_config_rejected():
    a=case()
    with pytest.raises(ValueError):
        alns_psp(a,empty_solution(a),seconds=-1)
    with pytest.raises(ValueError):
        alns_psp(a,empty_solution(a),seconds=1,min_ruin=5,max_ruin=4)
