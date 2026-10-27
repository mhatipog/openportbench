"""Public comparison interface checks (no LACE external checkout)."""
import json
import pytest
from openportbench.comparison_cli import compare, read_initial
from openportbench.psp import empty_solution, evaluate
from test_psp import case


def test_two_solver_families_in_standalone_comparison():
    a=case()
    d=compare(a,methods=("restricted-highs-milp","adaptive-ruin-recreate"),
              seconds=3.,seed=1)
    assert d["protocol"]=="PSP-standalone-strict-comparison-v1"
    assert d["source"]["method"]=="all-unserved"
    assert len(d["methods"])==2
    for result in d["methods"].values():
        assert result["status"]=="FEASIBLE", result["error"]
        assert result["objective"] <= evaluate(a,empty_solution(a))
        assert "solution" not in result


def test_json_incumbent_integer_keys_and_validation(tmp_path):
    a=case()
    s=empty_solution(a)
    p=tmp_path/"old.json"
    p.write_text(json.dumps({"solution":s}))
    assert read_initial(p)==s
    d=compare(a,methods=("identity",),seconds=2.,initial=read_initial(p))
    assert d["source"]["method"]=="verified-input"
    assert d["methods"]["identity"]["status"]=="FEASIBLE"


def test_invalid_methods_or_bad_incumbent(tmp_path):
    a=case()
    for methods in ((),("absent",),("identity","identity")):
        with pytest.raises(ValueError):
            compare(a,methods=methods)
    with pytest.raises(ValueError):
        compare(a,methods=("identity",),seconds=0)
    p=tmp_path/"broken.json"
    p.write_text("{}")
    with pytest.raises(ValueError):
        read_initial(p)
