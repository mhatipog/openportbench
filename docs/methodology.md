# Methodology, assumptions and claim boundaries

**Scope (27 October 2026):** OpenPortBench is a reproducible comparison
framework for algorithms solving the *integrated discrete Port Scheduling
Problem* (PSP) supplied by PJ-NTU/LACE at Git commit
`d772b74690075f641be8077e69748ec482e9febf`.

The research deliverable is the **benchmark evidence**, not a port planning
product. The canonical current results are in
[the four-method, two-budget scaling report](../results/2026-10-27-budget-sweep.md).
Historical experiments are kept intact even when their budget conventions
differ.

## Exact PSP mathematical contract

For every vessel, a valid schedule either leaves it unserved (incurring
the source penalty), or assigns it:

1. A berth with sufficient capacity, an integer start time and a
   non-overlapping berth occupancy interval.
2. A simultaneous inbound tug team and simultaneous outbound tug team,
   each satisfying minimum aggregate horsepower and maximum team size.
3. Inbound and outbound **tug occupancy intervals including preparation
   time**, with no overlap for an individual tug.
4. Inbound start inside the vessel's ETA / allowed earliness / lateness
   window; valid bounded gaps between inbound, berthing and outbound; and
   outbound service completion within the model horizon.

Berth/tug occupancies are half-open. As in the upstream source, preparation
can extend beyond the service horizon. The objective is the original weighted
sum of four terms:

```text
penalties for unserved vessels
+ priority-weighted total time in port for served vessels
+ priority-weighted deviation from ETA
+ cost of inbound and outbound tug utilization
```

Weights, vessel priorities, costs, durations and constraints come directly
from the unmodified LACE instance. The independent feasibility checker
(`src/openportbench/psp.py`) recomputes the source objective for each
candidate. Historical research workflows also cross-check the original
LACE evaluator; a disagreement invalidates a result.

Full CP-SAT represents the original PSP with integer times and rationally
scaled weighted coefficients. Its global `OPTIMAL` status is meaningful
**only for the complete model**. The LNS approach solves exact *conditional
neighborhoods* with unaffected vessels fixed; it cannot transfer the
neighborhood's best bound to the global PSP. HiGHS solves an exact binary
set-partitioning *master over generated candidate patterns*, not every
feasible full PSP schedule; `MASTER_OPTIMAL` does not prove original PSP
optimality. The classical ALNS-style code is original and does not claim to
reproduce a specific paper's algorithm.

## Strict paired-refinement comparison

The canonical study uses `scripts/solver_matrix.py` under
[the scaling workflow](../.github/workflows/solver-budget-sweep.yml):

- **Dataset:** six original PSP `test` inputs with suffix `_012`,
  80/100/150/250/300/500 vessels, two random seeds per instance.
- **Starting schedule:** original LACE `heuristic_01`, with a separate
  externally hard-limited **2 s** worker deadline. One common verified
  incumbent is reused across every method and refinement budget within a
  paired trial.
- **Treatments:** full warm CP-SAT; CP-SAT fix-and-optimize (LNS);
  restricted HiGHS MILP; classical adaptive ruin-and-recreate.
- **Budgets:** strict **3 s and 10 s** per refinement method, timed from
  worker launch through model creation, solving and return message.
- **Validation:** independently verify source and returned full schedules;
  cross-check upstream LACE objective; record statuses, timeouts, environment,
  input SHA256, exact method configurations and wall time.
- **Aggregation:** convert each objective difference to percentage improvement
  *within that same input and seed*, average seeds per instance, and average
  **distinct instances**. The exploratory 95% intervals are percentile
  bootstraps of entire instance groups, not of correlated seeds.

**Failure convention:** A search timeout or unavailable candidate keeps the
already verified incumbent as a *fallback*. The fallback's objective is
included in the observed quality result, while the actual method is marked
`TIMEOUT` or `ERROR`, not `FEASIBLE` or `OPTIMAL`. We report both
quality and successful-return counts; a failure cannot silently become a win.

The same **wall-clock** deadline is not equal CPU work, memory pressure, or
optimization energy. Method launch overhead, cached imports and processor
contention can change outcomes. The LNS methods may finish earlier than
their allowance. Rankings are therefore **conditional on protocol and
hardware**, not timeless properties of an algorithm.

## Protocol evolution and historical comparisons

Early results used non-strict advisory timers or ten LACE heuristic workers
versus one nominally equal-budget hybrid. Some training runs determined the
initial neighborhood size or method direction. These remain useful but are
**not interchangeable** with the later end-to-end hard-deadline tournament.
Published held-out inputs are now *exposed*; subsequent tuning cannot claim
those files as pristine unseen tests.

[Experimental chronology and raw results](../README.md#latest-verified-comparison) ·
[Full provenance and reproduction](reproduction.md) ·
[Canonical benchmark rules](benchmarking.md).

## Evidence level and limits

- **Established:** software executes; regression tests pass; four distinct
  algorithm strategies are benchmarked on pinned synthetic PSP instances;
  full objectives are independently checked and original trial records are
  archived; LNS currently wins these specific tested comparisons.
- **Not established:** new mathematical theorem; superiority to published
  maritime ALNS/decomposition methods; superiority to commercial terminal
  software; production dispatch service; actual Antwerp/Rotterdam operational
  traffic and disturbance handling.
- **Unvalidated:** deployment reliability, real human dispatch workflows,
  tidal/channel/pilot constraints, weather disruption, tug crew shifts,
  carbon/fuel multiobjective performance, generalization to unobserved
  real-world distributions.

The three other LACE port problems, tidal berth allocation, quay crane
allocation and metric k-server/k-median are **different mathematical models**.
OpenTNSim is a complementary vessel-traffic simulation tool, not a drop-in
solver under the identical objective. Cross-problem rankings are scientifically
invalid without an explicit equivalence argument.

## Maintenance / future studies

The current published study is **complete enough to hand off**. Further work
should start as a new registered experiment rather than modifying its historical
raw JSON or scorecards. Recommended next tracks: faithful documented reproduction
of a published ALNS/decomposition method; a larger unseen test manifest with
pre-registered budgets; and separately validated operational delay/outage
replanning with feasibility and stability metrics. Source rights and dataset
licenses must be checked first.

OpenPortBench's original implementation is MIT-licensed. The LACE source and
instances are retrieved from their own pinned repository.
