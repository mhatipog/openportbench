# OpenPortBench

**An open, reproducible benchmark for maritime scheduling algorithms.**

[Verified benchmarks](results/2026-10-27-budget-sweep.md) ·
[Reproduce results](docs/reproduction.md) ·
[Benchmark rules](docs/benchmarking.md) ·
[Contribute a method](CONTRIBUTING.md) ·
[CI](https://github.com/mhatipog/openportbench/actions/workflows/ci.yml)

OpenPortBench compares optimization approaches on the **same mathematical
problem, original instances, starting schedules, scoring rules, and enforced
time limits**. The first supported model is the integrated discrete
**Port Scheduling Problem (PSP)** from [PJ-NTU/LACE](https://github.com/PJ-NTU/LACE).
All feasible schedules are checked using an independently written PSP validator,
and published LACE experiments also cross-check the upstream evaluator.

**Status: reproducible research benchmark (v0.1), not an operational
port-dispatch system or a commercial-solver comparison.** The datasets in
the recorded results are generated academic instances, not real port traffic.

## Latest verified comparison

The [frozen scaling experiment of 27 October 2026](results/2026-10-27-budget-sweep.md)
tested four methods on **six original LACE test instances (80, 100, 150, 250,
300 and 500 vessels), two seeds each**. Each method received the *same
independently verified starting schedule* and identical externally enforced
refinement deadlines. The common starting schedule took a separate hard
2-second construction allowance.

| Method | Objective reduction, 3 s | Objective reduction, 10 s | Hard timeouts at 10 s |
| --- | ---: | ---: | ---: |
| CP-SAT fix-and-optimize (LNS) | **5.35%** | **9.02%** | 0/12 |
| Restricted-master HiGHS MILP | 0.26% | 0.26% | 4/12 |
| Adaptive ruin-and-recreate | 0.21% | 0.21% | 4/12 |
| Full warm-start CP-SAT | 0.00% | 0.00% | 10/12 |

Percentages are *per-instance normalized reductions of the same four-term PSP
objective relative to the common initial schedule*, averaged over distinct
instances. LNS had the lowest final objective in **12/12 paired trials at
both limits**. For 500 vessels, it improved the original objective by 1.61%
at 3 seconds and 2.37% at 10 seconds.

**Interpretation:** A timeout retains the valid starting schedule but is
reported as a solver timeout, *not* a successful solver result. HiGHS
`MASTER_OPTIMAL` certifies only the restricted candidate master, not a global
PSP optimum. These small synthetic experiments do **not** establish general
academic state of the art or commercial competitiveness.

[Detailed results, per-instance outcomes and bootstrap intervals](results/2026-10-27-budget-sweep.md) ·
[Primary raw JSON and SHA256](results/raw/2026-10-27-budget-sweep.json) ·
[Original CI experiment](https://github.com/mhatipog/openportbench/actions/runs/40576919339)

Earlier experiments remain available, but **must not be pooled** with the
latest protocol:
[four-method held-out, 5 s](results/2026-10-27-four-method-heldout.md) ·
[training, 3 s](results/2026-10-27-four-strategies-train.md) ·
[original LACE ten-heuristic portfolio comparison](results/2026-10-27-lns-portfolio.md).
The portfolio experiment used a different *allocated-budget* convention
and is not a directly equivalent strict end-to-end tournament.

## Methods and their limits

| Method | What is implemented | Interpretation |
| --- | --- | --- |
| Full OR-Tools CP-SAT | Complete integrated PSP; optional incumbent hint | A global optimum only when the full model returns `OPTIMAL` |
| CP-SAT LNS | Restricted exact neighborhood repairs with fixed outside vessels | A valid improvement heuristic; no global proof |
| HiGHS MILP | Sparse time-indexed set-partitioning over generated complete-vessel patterns | Restricted-master optimum only |
| Adaptive ruin-and-recreate | Randomized destroy/repair, regret insertion, simulated-annealing acceptance | Independent classical baseline, **not** a faithful reproduction of a named published ALNS |
| LACE portfolio | Ten original shipped heuristics at a pinned source revision | Historical external baseline; separately timed |
| FCFS / priority | Simple greedy constructions | Transparent construction controls |

The included [metric k-server and k-median experiments](docs/research-matrix.md)
are **separate mathematical subproblems**. They are not solvers for complete
PSP, nor implementations of OpenAI's newer theorem algorithms.

## Get started

Requires **Python 3.12+**. The strict comparison worker currently requires
**Linux or another Unix environment supporting `fork`**.

```bash
python -m pip install -e '.[dev]'
pytest -q

# Run one solver on a LACE PSP instance file
openportbench path/to/20_2_3_T12_001.txt --method cp-sat --seconds 5 --seed 1

# Run the four registered refinement approaches with a strict 3-second limit
openportbench compare path/to/20_2_3_T12_001.txt \
  --baseline empty --seconds 3 --seed 1 --output comparison.json
```

The standalone `compare` command validates with OpenPortBench's own scorer.
Its default `empty` baseline is **all vessels unserved**—feasible but
intentionally weak. For a more meaningful experiment, use
`--baseline fcfs`, `--baseline priority`, or a complete validated
`--initial-json path/to/schedule.json` schedule. Baseline construction time
is measured separately. Add `--include-solutions` to retain full schedules.

For paper-style, *dual-validator* comparisons on upstream datasets, use
the pinned [LACE reproduction instructions](docs/reproduction.md). No
paid optimization license or OpenAI API key is needed to run the benchmark.

## Reproducibility and scope

- **Identical PSP contract:** arrival windows, compatible berths, both tug
  services and horsepower teams, tug preparation time, resource non-overlap,
  stage transitions and LACE's original weighted objective.
- **Strict budgets:** full subprocess launch, model construction, solving
  and return-message time, rather than relying on advisory solver timers.
- **Auditable evidence:** per-run objective, input SHA256, source revision,
  status, runtime, parameters, solver versions, original JSON and
  transparent failed runs. Resample **instances**, not just seeds, for
  exploratory uncertainty intervals.
- **No mismatched leaderboards:** LACE's other three tug-routing formulations,
  tidal berth allocation, quay-crane planning and metric-placement experiments
  are different problems. Their published scores do not belong in the PSP table.

For the formal scientific assumptions and comparisons see
[benchmarking](docs/benchmarking.md) and [methodology](docs/methodology.md).
For literature and OpenAI applicability boundaries see the
[research matrix](docs/research-matrix.md).

## Handoff / further research

**The current benchmark is usable and self-contained for reproducible
algorithm comparisons.** Future extensions are optional, not prerequisites
for understanding or reproducing the recorded studies.

High-value future work: faithful reproduction of a published maritime ALNS
or decomposition method on an equivalent model; broader pre-registered
datasets and runtime budgets; and separate operational rescheduling tracks
for arrival delays, berth outages and tug availability. Do not relabel the
existing original ALNS-style baseline as a published-paper reproduction.

See [contribution guidelines](CONTRIBUTING.md) for evidence requirements.

OpenPortBench code is MIT licensed. Upstream algorithms and datasets retain
their own licenses and provenance; original LACE sources are fetched at the
pinned revision rather than bundled here.
