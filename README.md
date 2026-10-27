# OpenPortBench

**Benchmark optimization algorithms, don't just showcase one.**

OpenPortBench is an open, independently reproducible maritime optimization
**comparison platform**. It runs competing algorithm families on identical
problem formulations, checks every returned schedule, enforces measurable
time budgets and publishes raw negative as well as positive results.

**Independent, reproducible maritime planning optimization benchmarks.**
The first supported exact formulation is LACE's *Port Scheduling Problem* (PSP),
not a simplified berth-only proxy. The benchmark accepts LACE's unmodified
instances and scores all methods with an independent feasibility checker.

**Status: research prototype.** [Research comparison matrix](docs/research-matrix.md) and [metric subproblem experiments](scripts/metric_experiments.py). [First measured, reproducible smoke results](results/2026-10-27-train-smoke.md). This repository does not claim deployment at
the Port of Antwerp-Bruges or validation on operational traffic. LACE's four
port problems use generated academic test instances. See
[methodology](docs/methodology.md) and [reproduction](docs/reproduction.md).

## Benchmark-first architecture

| Benchmark family | Implementation | What it actually proves |
| --- | --- | --- |
| LACE 10-heuristic portfolio | Original MIT-licensed upstream at a pinned commit | Full published baseline; strict wall deadline on each heuristic |
| Greedy FCFS and priority | Independent PSP constructors | Cheap, transparent controls |
| Full CP-SAT | OR-Tools complete model | A *global* proof only if the solver returns `OPTIMAL` |
| CP-SAT fix-and-optimize (LNS) | Exact restricted neighborhoods | Valid heuristic incumbents; **no global optimality proof** |
| Time-indexed pattern MILP | SciPy / open-source HiGHS | Independent solver family; optimal only among explicitly enumerated vessel patterns |
| Online k-server and static k-median | Separate synthetic subproblem track | **Not** solutions to complete integrated PSP |

[Benchmark protocol, scoring and how to add an algorithm](docs/benchmarking.md)
explains what can be compared and exactly how. Source datasets and algorithm
implementations are pinned; constraints are never silently dropped.

### Common-incumbent tournament

Use the original LACE instance checkout (see [reproduction](docs/reproduction.md)).
The script obtains a verified source incumbent, then runs *each* refiner behind
its own strict external deadline. Every candidate gets checked twice: once
inside the worker, again in the parent, and finally against upstream LACE
on complete recorded experiments.

```sh
pip install -e '.[dev]'
pip install mip networkx
LACE_ROOT="$PWD/lace_source" python scripts/solver_matrix.py \
  --split train --sizes 20,40,60 --indices 004,005 \
  --seeds 1,2 --source-seconds 0.8 --refine-seconds 3 \
  --output results/tmp/solver-matrix.json
```

A single comparison budget cannot substitute for [multi-budget performance
profiles](docs/benchmarking.md). Only methods using the **same** original PSP
objective and constraints belong on the same ranking. Costs from different
families or instances must never be compared directly.

## Quick start (Python 3.12+)

```sh
python -m pip install -e '.[dev]'
pytest -q
# Obtain a LACE PSP .txt instance (see the reproduction guide)
openportbench path/to/20_2_3_T12_001.txt --method fcfs
openportbench path/to/20_2_3_T12_001.txt --method priority
openportbench path/to/20_2_3_T12_001.txt --method cp-sat --seconds 5 --seed 1
```

Methods report their actual elapsed times, feasibility-certified objectives
and, for CP-SAT, a valid solver best bound where available. No seed or
runtime extrapolation is considered evidence of a speedup.

## Measured optimization results (research instances)

* [Frozen LNS versus all ten LACE heuristics, strict 7-second budget](results/2026-10-27-lns-portfolio.md): 12/12 paired reductions across six held-out PSP cases; 6.33% mean lower objective. **Not a broad state-of-the-art claim**.
* [Frozen LNS versus warm full CP-SAT](results/2026-10-27-lns-heldout.md): 12/12 paired reductions across separate held-out PSP instances.
* [LNS training configuration and negative results](results/2026-10-27-lns-training.md): transparent selection and independent validation.
* Original inputs, SHA256 checksums and complete method-level JSON records are in [results/raw/](results/raw/).

## Research tracks

| Problem (LACE slug) | Data | Upstream 10-heuristic reproduction | Independent exact formulation |
| --- | --- | --- | --- |
| `port_scheduling_problem` | generated research PSP | automated smoke reproduction | implemented with CP-SAT and independent feasibility evaluator |
| `multi_tugboat_routing_and_scheduling_problem` | generated research tug routes | automated upstream reproduction | not implemented |
| `multi_base_tugboat_routing_and_scheduling_problem` | generated research multi-base tug routes | automated upstream reproduction | not implemented |
| `multi_tugboat_routing_problem_with_variable_speed` | generated research variable-speed tug routes | automated upstream reproduction | not implemented |

The automated reproduction runs **existing** shipped LACE heuristics; it does
not run the LLM evolution stage, use an API key, or establish the correctness
of the published paper's aggregate scores. Its deterministic smoke set is not
a replacement for an unseen test-set evaluation.

## Why this is different

* **Verification first.** The scorer is independent of LACE's Python evaluator,
  with cross-comparison against the upstream evaluator in the research workflow.
* **Like-for-like mathematical formulation.** The CP-SAT model includes both
  inbound and outbound tug service, preparation occupancy, team horsepower,
  berth fit, time-window and sequence-slack requirements, and LACE's weighted
  objective with rational coefficient scaling.
* **Accounting for compute.** LACE's *portfolio best* gets ten heuristic runs;
  a single CP-SAT run gets the same **allocated aggregate** wall-clock budget.
  Actual elapsed wall time is recorded, not assumed equal. Hardware,
  package versions, and source revisions accompany each JSON result.
* **Honest limitations.** Non-optimal solutions never receive an "optimal"
  label. Missing baselines and limited samples are marked as such.

## Directions

A full blinded test sweep, stronger neighborhood search, fair budget-matched
hybrids, scenario uncertainty, MILP alternatives and a distinct tidal-restricted
berth-allocation track are in the [research backlog](docs/methodology.md).

## References and attribution

* [PJ-NTU/LACE](https://github.com/PJ-NTU/LACE), MIT; the upstream
  implementation, generated maritime instances, and evolved portfolio.
* [TUDelft-CITG/OpenTNSim](https://github.com/TUDelft-CITG/OpenTNSim), MIT;
  maritime traffic *simulation*, not an equivalent PSP optimization model.
* [MATHPROG ORlib BAP data](https://github.com/andreas-ernst/Mathprog-ORlib);
  tidal-constraint berth-allocation research data, a **different** model.
* [OpenAI mathematics / randomized online k-server](https://github.com/openai/math);
  interesting for future sequential tug-positioning research, but its
  theoretical guarantee does **not** apply to this offline PSP model.

OpenPortBench source is MIT-licensed. Third-party code and datasets remain in
their original repositories with their own attribution/license terms.
