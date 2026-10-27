"""Pre-registered synthetic metric location/dispatch experiment (not a theorem reproduction)."""
import hashlib
import json
import os
import platform
import random
import sys
import time
from pathlib import Path

from openportbench.mobile import (
    kmedian_exact, kmedian_greedy, kmedian_one_swap,
    dispatch, offline_dispatch_optimum,
)


def main():
    data = []
    for seed in range(1, 13):
        rng = random.Random(seed)
        grid = [(i, j) for i in range(5) for j in range(5)]
        dist = [[abs(x-x2) + abs(y-y2) for x2, y2 in grid] for x, y in grid]
        weights = [rng.randint(1, 7) for _ in grid]
        t0 = time.perf_counter()
        opt, centers = kmedian_exact(dist, 3, weights)
        t_exact = time.perf_counter() - t0
        g, cg = kmedian_greedy(dist, 3, weights)
        s, cs = kmedian_one_swap(dist, 3, weights)
        data.append({"track": "synthetic_kmedian_grid", "seed": seed,
                     "metric": "5x5 unit Manhattan grid", "k": 3,
                     "objective_unit": "weighted grid steps",
                     "exact": opt, "greedy": g, "one_swap": s,
                     "exact_runtime_s": t_exact, "exact_centers": centers})
        # Separate from the location study: cyclic 8-node dock-side corridor.
        m = [[min(abs(i-j), 8-abs(i-j)) for j in range(8)] for i in range(8)]
        requests = [rng.randrange(8) for _ in range(30)]
        starts = (0, 4)
        true_opt = offline_dispatch_optimum(m, starts, requests)
        methods = {name: dispatch(m, starts, requests, name, seed)["distance"]
                   for name in ("nearest", "random_two", "preview2")}
        assert all(v >= true_opt for v in methods.values())
        data.append({"track": "synthetic_kserver_ring", "seed": seed,
                     "metric": "8-node undirected cycle shortest-path metric",
                     "k": 2, "n_requests": len(requests),
                     "objective_unit": "movement edges",
                     "offline_exact": true_opt, **methods,
                     "preview2_uses_future_requests": True})
    result = {"label": "synthetic mathematical subproblems, NOT real port data",
              "algorithms": "classical baselines, NOT the OpenAI #110/#125 published algorithms",
              "source_commit": os.environ.get("GITHUB_SHA"),
              "python": sys.version.split()[0], "platform": platform.platform(),
              "experiment_protocol": "seeds 1..12, no tuning and no held-out LACE data",
              "rows": data}
    path = Path("results/tmp/metric-mobility.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    print("RESULT", path)
    for track in ("synthetic_kmedian_grid", "synthetic_kserver_ring"):
        rows = [r for r in data if r["track"] == track]
        keys = ("exact", "greedy", "one_swap") if "median" in track else ("offline_exact", "nearest", "random_two", "preview2")
        print(track, {key: round(sum(r[key] for r in rows)/len(rows), 4) for key in keys})


if __name__ == "__main__":
    main()
