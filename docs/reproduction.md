# Reproducing OpenPortBench results

This guide is for the **original, pinned LACE PSP benchmark**. It is
different from the standalone `openportbench compare` CLI, which accepts
individual PSP files but does not load the original LACE scorer.

The canonical archived study is the
[3-second/10-second four-method scaling comparison](../results/2026-10-27-budget-sweep.md);
its original [machine-readable JSON](../results/raw/2026-10-27-budget-sweep.json)
is permanently checked into this repository. The source run is
[GitHub Actions #40576919339](https://github.com/mhatipog/openportbench/actions/runs/40576919339).

## Environment and upstream source

- Python **3.12+**, Linux/Unix with `fork`, Git.
- Free Python packages: OR-Tools, SciPy/HiGHS, NumPy, and the upstream
  LACE dependencies `mip` and `networkx`.
- Original LACE commit:
  `d772b74690075f641be8077e69748ec482e9febf`.
- Original benchmark implementation SHA: **`e9cb07334951530ca102a8be26aa7abf62ea4b91`**.
  The archived study used that revision; later documentation updates are
  not part of the historical experiment.

From the OpenPortBench repository root:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pip install mip networkx
pytest -q

git clone https://github.com/PJ-NTU/LACE lace_source
git -C lace_source checkout d772b74690075f641be8077e69748ec482e9febf
git -C lace_source rev-parse HEAD
```

For the closest historical reproduction, check out the OpenPortBench
implementation commit in a separate working tree, since current source and
dependencies may evolve:

```bash
git worktree add --detach ../openportbench-20261027 e9cb07334951530ca102a8be26aa7abf62ea4b91
```

If running from `../openportbench-20261027`, install that worktree
(`python -m pip install -e '.[dev]'`) and point `LACE_ROOT` to the
absolute location of `lace_source` in the first checkout. A GitHub Actions
hosted runner configuration can be studied in
[solver-budget-sweep.yml](../.github/workflows/solver-budget-sweep.yml).

## Reproduce the final 3 s vs 10 s scaling study

Using the current checkout from the repository root, with the pinned LACE
checkout under `lace_source/`:

```bash
LACE_ROOT="$PWD/lace_source" python scripts/solver_matrix.py \
  --split test \
  --sizes 80,100,150,250,300,500 \
  --indices 012 --seeds 1,2 \
  --source-seconds 2 --refine-budgets 3,10 \
  --methods warm-cp-sat,fix-optimize-cp-sat,restricted-highs-milp,adaptive-ruin-recreate \
  --output results/tmp/solver-budget-sweep.json
```

- Six **test** files at suffix `_012`, two seeds per file.
- Exactly **one original LACE heuristic_01 starting schedule** generated
  per file and seed under an externally enforced **2-second** wall deadline.
  Each refiner sees that same verified schedule at *both* runtime budgets.
- Each refiner gets its own independent **3-second or 10-second strict wall
  deadline**, including subprocess startup, model building, solve, solution
  validation and return. Late outputs are not accepted.
- The complete original PSP objective is verified by this project's
  evaluator and the original LACE evaluator. Missing or late output is a
  **timeout**, with common starting-schedule fallback; it is not a solver win
  or global-optimum certificate.

The studied source code, versions, original inputs and recorded outcomes are
reproducible; **wall times, randomized search paths and resulting objectives
may vary across hardware, OS, dependency releases, and seeds**. Published
SHA256 identifies the **historical artifact**, not necessarily a byte-for-byte
result obtainable on a different machine.

For a study matching the archived environment more closely, consult
[its frozen `pip freeze` snapshot](../results/raw/2026-10-27-budget-sweep-dependencies.txt).
Even matching Python packages cannot guarantee the same runner hardware
or runtime scheduling.

## Generate a report

The source JSON includes `summary_by_budget`, individual failure records,
method configurations, input hashes, hardware and solver versions.
To regenerate the comparison report from the JSON:

```bash
python - <<'PY'
from pathlib import Path
import hashlib
import json
from openportbench.matrix_profile import render_sweep

p = Path("results/tmp/solver-budget-sweep.json")
raw = p.read_bytes()
report = render_sweep(json.loads(raw), hashlib.sha256(raw).hexdigest())
Path("results/tmp/solver-budget-sweep.md").write_text(report)
print("SHA256:", hashlib.sha256(raw).hexdigest())
PY
```

The authoritative [published report](../results/2026-10-27-budget-sweep.md)
lists the archived JSON digest
`76e5d3d62c2e9233acf841fad11d74965d60ac726a64263ba961774141bde815`.
The [archival workflow](../.github/workflows/archive-budget-sweep.yml)
checked the original artifact and committed the frozen JSON, report and
environment snapshot.

## Earlier studies: separate protocols, not one leaderboard

| Study | Source/report | Why it differs |
| --- | --- | --- |
| Four-method 5 s held-out | [Report](../results/2026-10-27-four-method-heldout.md) | Different source inputs (`_010/_011`) and runtime budget |
| Four-method 3 s training | [Report](../results/2026-10-27-four-strategies-train.md) | Training split and different source instances |
| Three-method 5 s held-out | [Report](../results/2026-10-27-solver-matrix-heldout.md) | Older algorithm roster (`_008/_009`) |
| LNS versus original LACE ten-heuristic portfolio | [Report](../results/2026-10-27-lns-portfolio.md) | Equal **allocated** time, not equal externally hard-limited end-to-end hybrid budget |

An older [research smoke workflow](../.github/workflows/research.yml)
reproduces one training input from each of LACE's **four distinct** port
problem families, using `scripts/reproduce_lace.py`. This smoke workflow
uses **advisory** per-heuristic timing, so it must not be conflated with
the final strict PSP tournament.

For method constraints, success/failure definitions and study comparability,
see [benchmarking.md](benchmarking.md) and
[methodology.md](methodology.md).
