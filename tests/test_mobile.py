import itertools
import random
import pytest
from openportbench.mobile import (
    check_metric, median_cost, kmedian_exact, kmedian_greedy,
    kmedian_one_swap, dispatch, offline_dispatch_optimum,
)


def line_metric(n=7):
    return [[abs(i-j) for j in range(n)] for i in range(n)]


def test_metric_rejects_triangle_violation():
    with pytest.raises(ValueError):
        check_metric([[0, 1, 6], [1, 0, 1], [6, 1, 0]])


@pytest.mark.parametrize("k", [1, 2, 3])
def test_kmedian_exact_dominates_heuristics(k):
    m = line_metric()
    weights = [1, 3, 1, 2, 4, 1, 2]
    exact, sites = kmedian_exact(m, k, weights)
    greedy, _ = kmedian_greedy(m, k, weights)
    improved, sites2 = kmedian_one_swap(m, k, weights)
    assert exact <= improved <= greedy
    assert median_cost(m, sites, weights) == exact
    assert median_cost(m, sites2, weights) == improved


def test_dispatch_offline_is_lower_bound():
    metric = line_metric(5)
    for seq in itertools.product(range(5), repeat=3):
        optimum = offline_dispatch_optimum(metric, (0, 4), seq)
        nearest = dispatch(metric, (0, 4), seq)
        random_run = dispatch(metric, (0, 4), seq, method="random_two", seed=7)
        preview = dispatch(metric, (0, 4), seq, method="preview2")
        assert optimum <= nearest["distance"]
        assert optimum <= random_run["distance"]
        assert optimum <= preview["distance"]
        assert len(nearest["actions"]) == len(seq)


def test_seeding_random_two_reproducible():
    metric = line_metric(9)
    a = dispatch(metric, (0, 8), [4, 5, 3, 7, 1, 6], "random_two", seed=18)
    b = dispatch(metric, (0, 8), [4, 5, 3, 7, 1, 6], "random_two", seed=18)
    assert a == b
