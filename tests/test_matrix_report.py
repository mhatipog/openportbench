from openportbench.matrix_report import render_matrix
import pytest


def case():
    return {
        "protocol":"PSP-strict-common-incumbent-v1","split":"train",
        "source_sha":"abc","benchmark_commit":"def",
        "source_hard_wall_s":1,"refinement_hard_wall_s":3,
        "methods":["a","b"],
        "summary":{
            "metrics":{
                "a":{"mean_improvement_pct_instance_weighted":10,
                     "mean_observed_wall_s":1.5,"hard_timeout_count":0,
                     "observations":2,"invalid_count":0},
                "b":{"mean_improvement_pct_instance_weighted":0,
                     "mean_observed_wall_s":3,"hard_timeout_count":2,
                     "observations":2,"invalid_count":0},
            },
            "winner_counts_including_ties":{"a":2},
        },
        "rows":[{"file":"20_1_2_T12_004.txt","seed":i,"source_objective":100,
                 "input_sha256":"abc","methods":{
                     "a":{"objective":90.},"b":{"objective":100.},
                 }} for i in (1,2)],
    }


def test_markdown_has_provenance_methods_and_methodological_warnings():
    s=render_matrix(case(),source_hash="f"*64)
    assert "20_1_2_T12_004.txt" in s
    assert "10.00%" in s
    assert "2/2" in s
    assert "restricted" in s
    assert "f"*64 in s


def test_bad_protocol_rejected():
    doc=case()
    doc["protocol"]="different"
    with pytest.raises(ValueError):
        render_matrix(doc)
