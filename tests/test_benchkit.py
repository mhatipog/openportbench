import pytest
from openportbench.benchkit import METHODS, strict_refine, sanitize
from openportbench.psp import empty_solution, evaluate
from test_psp import case


def test_methods_registry_distinct_families():
    assert len(METHODS) == len(set(METHODS))
    assert "restricted-highs-milp" in METHODS
    assert "fix-optimize-cp-sat" in METHODS


def test_strict_baseline_and_parent_validation():
    a=case()
    initial=empty_solution(a)
    result=strict_refine(a,initial,"identity",seconds=2.)
    assert result["status"]=="FEASIBLE"
    assert result["objective"]==evaluate(a,initial)
    assert "solution" not in sanitize(result)


@pytest.mark.parametrize("method",["warm-cp-sat","fix-optimize-cp-sat","restricted-highs-milp"])
def test_strict_solver_respects_model(method):
    a=case()
    initial=empty_solution(a)
    result=strict_refine(a,initial,method,seconds=4.)
    assert result["status"]=="FEASIBLE", result["error"]
    assert result["valid"]
    assert evaluate(a,result["solution"])==pytest.approx(result["objective"])
    assert result["objective"]<=evaluate(a,initial)
    assert result["wall_s"] <= 4.3


def test_strict_timeout_without_late_result():
    a=case()
    s=empty_solution(a)
    result=strict_refine(a,s,"warm-cp-sat",seconds=0.00001)
    assert result["status"] in ("TIMEOUT","WORKER_ERROR")
    assert result["objective"]==evaluate(a,s)


def test_invalid_method_budget():
    with pytest.raises(ValueError):
        strict_refine(case(),empty_solution(case()),"unknown",seconds=1)
    with pytest.raises(ValueError):
        strict_refine(case(),empty_solution(case()),"identity",seconds=0)
