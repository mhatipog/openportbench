# OpenPortBench

**Independent, reproducible maritime planning optimization benchmarks.**
The first supported exact formulation is LACE's *Port Scheduling Problem* (PSP),
not a simplified berth-only proxy. The benchmark accepts LACE's unmodified
instances and scores all methods with an independent feasibility checker.

**Status: research prototype.** This repository does not claim deployment at
the Port of Antwerp-Bruges or validation on operational traffic. LACE's four
port problems use generated academic test instances. See
[methodology](docs/methodology.md) and [reproduction](docs/reproduction.md).

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
