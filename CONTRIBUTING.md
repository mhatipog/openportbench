# Contributing a benchmark method or dataset

OpenPortBench primarily exists to **compare competing algorithmic ideas
fairly and reproducibly**. Small, well-validated negative results are welcome;
unsupported state-of-the-art claims are not.

## Add a PSP optimization method

1. Identify the original source: DOI/paper version, repository commit,
   license, algorithm class and exactly which claims are reproduced.
   A generic ruin-and-recreate heuristic is **not** a faithful reproduction
   of a specific published ALNS algorithm.
2. Confirm the exact PSP mathematical model in
   [docs/methodology.md](docs/methodology.md). If constraints differ, create
   a **separate track**; do not silently simplify the original PSP to get
   attractive scores.
3. Expose a callable taking
   `(instance: dict, incumbent: dict, seconds: float, seed: int)`
   and returning a mapping with `solution`, `objective`, `status`.
   The `solution` must have precisely the keys expected by
   `openportbench.psp.evaluate`; do not mutate the input instance or
   initial incumbent.
4. Add the method to `openportbench.benchkit.METHODS` and the `refine`
   dispatch function. The strict benchmark runner will run it in an
   isolated Unix subprocess, enforce its entire wall budget, validate
   twice and preserve the starting schedule if it errors or times out.
5. Add a **test with exact small-case independent optimum** if feasible,
   at least one resource-conflict adversarial test, no-worse fallback tests
   and seed-reproducibility checks. Include meaningful failures, not only
   successes.
6. Run `pytest -q`; then the training-only tournament on original
   LACE train instances. **Freeze** the method and all parameters before
   asking for an untouched test-set comparison.
7. Publish the original experiment JSON with exact source revision,
   instance hashes, seed, hardware, versions, objective cross-checks,
   strict wall durations, and a generated Markdown report. Archive it
   in `results/raw/` with a pinned digest.

For a new method, do **not** retroactively insert it into an existing
historical run or silently retune methods against released test instances.

## Reproduce the canonical tournament

See [docs/benchmarking.md](docs/benchmarking.md), the checked-in
`scripts/solver_matrix.py`, and associated workflows in
`.github/workflows/solver-matrix*.yml`.
These are intentionally free of paid API keys and commercial solver
licenses.

Examples:

```sh
pip install -e '.[dev]'
pip install mip networkx
LACE_ROOT="$PWD/lace_source" python scripts/solver_matrix.py \
    --split train --sizes 20,40,60 --indices 004,005 \
    --seeds 1,2 --source-seconds 0.8 --refine-seconds 3 \
    --output results/tmp/matrix.json
python scripts/render_solver_matrix.py results/tmp/matrix.json \
    --output results/tmp/matrix.md
```

`lace_source` must point to the pinned upstream commit in the methodology
and contain the original train/test instances. Verify its Git revision.

## Prior published methods: evidence levels

* **Referenced**: paper abstract, source code or dataset exists, without
  a verified equivalent formulation.
* **Ported**: implementation written or reproducibly run on an equivalent
  mathematical contract; exact assumptions and modifications documented.
* **Validated**: correctness independently demonstrated and unit tests
  include adversarial cases.
* **Benchmarked**: paired experiments run against identical inputs,
  objectives, fixed budgets, hardware and deterministic seeds.
* **Operationally evaluated**: disruption and deployment scenarios
  tested on authorized representative operational data.

Only claim a method is experimentally competitive at the supported level.
The paper's own result on a different berth/crane or tug routing model
is **not** a direct score against LACE PSP.

## Responsible benchmarking

Never publish private vessel schedules or sensitive operational logs.
Before redistributing datasets or third-party implementations, check
their licenses and provenance. Do not include secrets, API tokens,
customer data, or proprietary benchmark code in issues or submissions.

## Final study protection

Treat [the 27 October 2026 3 s / 10 s benchmark](results/2026-10-27-budget-sweep.md)
as a frozen historical study. Its raw JSON, checksum and original-source
commit are provenance records, not an editable current leaderboard. New
papers, algorithms or parameter settings should get a **new separately named
study** and a fresh pre-registered holdout manifest. Run the standard test
suite, preserve failures, and never convert a restricted MILP certificate into
a full PSP optimality claim.
