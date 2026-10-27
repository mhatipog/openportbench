# Reproducing the smoke comparison

The bounded [research workflow](../.github/workflows/research.yml) checks
out both OpenPortBench and PJ-NTU/LACE at exact revisions.

LACE revision: `d772b74690075f641be8077e69748ec482e9febf`

Inputs (one **training** instance per track):
* PSP: `port_scheduling_problem/instances/train/20_2_3_T12_001.txt`
* Tug scheduling: `multi_tugboat_routing_and_scheduling_problem/instances/train/n10_K5_T24_00001.txt`
* Multi-base tug: `multi_base_tugboat_routing_and_scheduling_problem/instances/train/12_6_3_001.txt`
* Variable-speed tug: `multi_tugboat_routing_problem_with_variable_speed/instances/train/n10_m3_a30_001.txt`

Manual local reproduction:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pip install numpy scipy mip networkx
git clone --filter=blob:none --no-checkout https://github.com/PJ-NTU/LACE lace_source
git -C lace_source checkout d772b74690075f641be8077e69748ec482e9febf
LACE_ROOT="$PWD/lace_source" python scripts/reproduce_lace.py --seconds-per-heuristic 0.35 --seed 1 --output results/smoke.json
```

All results are tagged with the source SHA, instance content SHA256, platform,
CPU, Python/solver package versions and per-method timing. JSON is uploaded
as a GitHub Actions workflow artifact (short retention), not silently
committed as a permanent paper result. Repeat with more instances and
multiple seeds before using any comparison in an article or interview.

`--seconds-per-heuristic` is advisory for the upstream portfolio; its
functions do not necessarily respect a hard deadline. Any overrun is
reported in actual elapsed time. The single CP-SAT PSP run gets 10 times
the per-heuristic allocated budget.

## Reproduce the strict solver tournament

Checkout LACE at the exact SHA above and install `pip install -e '.[dev]'
plus `mip networkx`. Then run:

```sh
LACE_ROOT="$PWD/lace_source" python scripts/solver_matrix.py \\
  --split train --sizes 20,40,60 --indices 004,005 --seeds 1,2 \\
  --source-seconds 0.8 --refine-seconds 3 \\
  --output results/tmp/solver-matrix.json
```

The runner records each method's timeout, feasibility, original-instance
SHA256 and two-verifier objective agreement. HiGHS is installed via SciPy;
no commercial solver license is required. See [canonical comparison
protocol](benchmarking.md). The older portfolio workflow uses a different
budget allocation convention, so do not combine its scores into one
incompatible league table.
