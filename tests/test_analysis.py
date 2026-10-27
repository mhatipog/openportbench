from openportbench.analysis import summarize_pairs
import pytest


def example():
    def r(file, seed, a, b):
        return {"filename": file, "seed": seed, "methods": {
            "restricted_lns": {"objective": a, "refinement_wall_s": 1.,
                               "upstream_verified": True},
            "warm_full_cp_sat": {"objective": b, "refinement_wall_s": 2.,
                                 "upstream_verified": True},
        }}
    return {"experiment": "test", "rows": [
        r("20_1_1_T12_001.txt", 1, 8, 10),
        r("20_1_1_T12_001.txt", 2, 8, 10),
        r("40_1_1_T12_001.txt", 1, 11, 10),
        r("40_1_1_T12_001.txt", 2, 11, 10),
    ]}


def test_cluster_by_instance_not_seed():
    summary = summarize_pairs(example(), repeats=200, bootstrap_seed=1)
    assert summary["verified_pairs"] == 4
    assert summary["fully_compared_instance_count"] == 2
    assert summary["mean_gain_pct_equal_weight_per_instance"] == pytest.approx(5.)
    assert summary["cases"][0]["paired_wins"] == 2
    assert summary["cases"][1]["paired_losses"] == 2
    assert summary["instance_cluster_bootstrap_95pct"][0] >= -10.000000001
    assert summary["instance_cluster_bootstrap_95pct"][1] <= 20.000000001


def test_missing_verification_explicit():
    doc = example()
    doc["rows"][0]["methods"]["restricted_lns"]["upstream_verified"] = False
    summary = summarize_pairs(doc, repeats=200)
    assert summary["verified_pairs"] == 3
    assert len(summary["excluded_pairs"]) == 1


def test_no_paired_data_does_not_invent_interval():
    doc = example()
    doc["rows"] = [doc["rows"][0]]
    summary = summarize_pairs(doc, repeats=200)
    assert summary["instance_cluster_bootstrap_95pct"] is None


def test_invalid_bootstrap_rejected():
    with pytest.raises(ValueError):
        summarize_pairs(example(), repeats=0)
