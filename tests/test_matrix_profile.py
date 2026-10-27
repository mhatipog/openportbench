from openportbench.matrix_profile import (
    confidence_interval, summarize_sweep, render_sweep, _clustered_values,
)
import pytest


def sample():
    rows=[]
    for filename in ("80_1_2_T48_012.txt","150_1_2_T48_012.txt"):
        for seed in (1,2):
            rows.append({
                "file":filename,"input_sha256":filename,"seed":seed,
                "source_status":"FEASIBLE","source_objective":100.,
                "methods_by_budget":{
                    "3":{
                        "a":{"objective":95., "wall_s":1., "status":"FEASIBLE","valid":True},
                        "b":{"objective":100., "wall_s":3., "status":"TIMEOUT","valid":True},
                    },
                    "10":{
                        "a":{"objective":90., "wall_s":2., "status":"FEASIBLE","valid":True},
                        "b":{"objective":97., "wall_s":9., "status":"FEASIBLE","valid":True},
                    },
                }
            })
    return {
        "protocol":"PSP-strict-common-incumbent-sweep-v1",
        "source_sha":"lace","benchmark_commit":"runner",
        "source_hard_wall_s":2., "split":"test",
        "refinement_hard_budgets_s":[3.,10.],
        "methods":["a","b"],
        "rows":rows,
    }


def test_multi_budget_same_baseline_and_instance_bootstrap():
    doc=sample()
    results=summarize_sweep(doc)
    assert results["3"]["metrics"]["a"]["mean_improvement_pct_instance_weighted"]==5.
    assert results["3"]["metrics"]["b"]["hard_timeout_count"]==4
    assert results["10"]["metrics"]["a"]["mean_improvement_pct_instance_weighted"]==10.
    assert _clustered_values(doc,3.,"a")==[5.,5.]
    assert confidence_interval([5.,5.])["lower"]==5.
    assert confidence_interval([5.])["lower"] is None
    doc["summary_by_budget"]=results
    report=render_sweep(doc,"012345")
    assert "80_1_2_T48_012.txt" in report
    assert "150_1_2_T48_012.txt" in report
    assert "95% cluster" in report
    assert "10.00%" in report


def test_bad_protocol_and_zero_reference_rejected():
    doc=sample()
    doc["protocol"]="invalid"
    with pytest.raises(ValueError):
        summarize_sweep(doc)
    doc=sample()
    doc["rows"][0]["source_objective"]=0
    with pytest.raises(ValueError):
        _clustered_values(doc,3.,"a")
