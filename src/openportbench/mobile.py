"""Separated resource-location and online-dispatch mathematical subproblems.

These algorithms DO NOT reproduce OpenAI #110 or #125. They supply executable
classical comparators on metrics with independently computable small optima.
"""
from __future__ import annotations
from functools import lru_cache
from itertools import combinations
import random


def check_metric(dist):
    n = len(dist)
    if n < 2 or any(len(row) != n for row in dist):
        raise ValueError("Metric must be a square matrix with at least two sites")
    for i in range(n):
        if dist[i][i] != 0:
            raise ValueError("Metric diagonal must be zero")
        for j in range(n):
            if i != j and (dist[i][j] <= 0 or dist[i][j] != dist[j][i]):
                raise ValueError("Positive symmetric metric required")
            for k in range(n):
                if dist[i][j] > dist[i][k] + dist[k][j]:
                    raise ValueError("Triangle inequality violation")
    return n


def median_cost(dist, centers, weights=None):
    n = len(dist)
    if not centers or not set(centers) <= set(range(n)):
        raise ValueError("Centers required and must refer to metric nodes")
    if weights is None:
        weights = [1] * n
    if len(weights) != n or any(x < 0 for x in weights):
        raise ValueError("Weights must be nonnegative and one per demand node")
    return sum(weights[i] * min(dist[i][j] for j in centers) for i in range(n))


def kmedian_exact(dist, k, weights=None):
    n = check_metric(dist)
    if not 1 <= k <= n:
        raise ValueError("Invalid k")
    return min(((median_cost(dist, sites, weights), sites)
                for sites in combinations(range(n), k)),
               key=lambda x: (x[0], x[1]))


def kmedian_greedy(dist, k, weights=None):
    n = check_metric(dist)
    if not 1 <= k <= n:
        raise ValueError("Invalid k")
    centers = []
    while len(centers) < k:
        options = ((median_cost(dist, tuple(centers) + (j,), weights), j)
                   for j in range(n) if j not in centers)
        centers.append(min(options)[1])
    centers.sort()
    return median_cost(dist, centers, weights), tuple(centers)


def kmedian_one_swap(dist, k, weights=None):
    """Full-best-improvement one-swap local search from greedy solution."""
    value, sites = kmedian_greedy(dist, k, weights)
    chosen = set(sites)
    while True:
        best = (value, tuple(sorted(chosen)))
        for x in sorted(chosen):
            for y in range(len(dist)):
                if y in chosen:
                    continue
                candidate = tuple(sorted((chosen - {x}) | {y}))
                cand = (median_cost(dist, candidate, weights), candidate)
                if cand < best:
                    best = cand
        if best[0] >= value:
            return value, tuple(sorted(chosen))
        value, sites = best
        chosen = set(sites)


def dispatch(dist, starts, requests, method="nearest", seed=1):
    """Legal k-server sequence with movement-only objective.

    nearest and random_two are online. preview2 is an explicitly non-online
    rolling 2-request lookahead benchmark (a one-request oracle).
    """
    n = check_metric(dist)
    if len(starts) < 1 or any(x not in range(n) for x in starts):
        raise ValueError("Invalid initial server nodes")
    if any(x not in range(n) for x in requests):
        raise ValueError("Invalid requests")
    state = tuple(starts)
    rng = random.Random(seed)
    total = 0
    actions = []
    for index, request in enumerate(requests):
        lengths = [(dist[position][request], i) for i, position in enumerate(state)]
        lengths.sort()
        if method == "nearest":
            move = lengths[0][1]
        elif method == "random_two":
            shortlist = lengths[:2]
            move = shortlist[0][1] if len(shortlist) == 1 or rng.random() < 0.75 else shortlist[1][1]
        elif method == "preview2":
            if index+1 == len(requests):
                move = lengths[0][1]
            else:
                next_req = requests[index+1]
                candidates = []
                for cost, i in lengths:
                    future = tuple(request if j == i else p for j, p in enumerate(state))
                    second = min(dist[p][next_req] for p in future)
                    candidates.append((cost + second, cost, i))
                move = min(candidates)[2]
        else:
            raise ValueError("Unknown method")
        travelled = dist[state[move]][request]
        state = tuple(request if j == move else p for j, p in enumerate(state))
        total += travelled
        actions.append(move)
    return {"distance": total, "actions": actions, "end_positions": state}


def offline_dispatch_optimum(dist, starts, requests):
    """DP exact offline k-server oracle, exponential in number of servers.

    Inappropriate for large real dispatch: an upper benchmark bound on the
    quality of online policies, not a deployable online strategy.
    """
    n = check_metric(dist)
    if len(starts) < 1 or any(x not in range(n) for x in starts) or any(x not in range(n) for x in requests):
        raise ValueError("Invalid starts or requests")
    states = {tuple(starts): 0}
    for req in requests:
        updated = {}
        for positions, cost in states.items():
            for i, position in enumerate(positions):
                next_positions = tuple(req if j == i else x for j, x in enumerate(positions))
                value = cost + dist[position][req]
                updated[next_positions] = min(value, updated.get(next_positions, float("inf")))
        states = updated
    return min(states.values())
