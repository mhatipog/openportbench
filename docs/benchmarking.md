# Benchmark protocol and solver comparability

OpenPortBench's primary deliverable is **the comparison evidence**:
pinned data, independently reproducible solver implementations, strict
wall-clock time limits, validation, full outputs, and explicit limitations.
Solver novelty is optional. An experimentally useful negative result is
better than an unverifiable leaderboard win.

## Canonical PSP scope

The currently independently verified formulation is LACE's integrated
Port Scheduling Problem (PSP). Preserve simultaneous tug teams, inbound
and outbound services, horsepower minima, tug preparation occupancy,
arrival windows, berth capacity and occupancy, time-transition tolerance,
service horizon and all four weighted objective components.

Other LACE maritime families and published berth-crane datasets use
*different mathematical models*. They are separate benchmark tracks;
none may silently share PSP ranks or global optimality claims.

Original benchmark LACE: PJ-NTU/LACE at
`d772b74690075f641be8077e69748ec482e9febf` (MIT license).

## Executable solver families

| Identifier | Family | Search representation | Bound/optimality status |
| --- | --- | --- | --- |
| `fcfs`, `priority` | deterministic construction | complete PSP heuristic | feasible only |
| `lace_01`–`lace_10` | upstream AI-evolved portfolio | ten independent shipped heuristics | feasible only |
| `warm-cp-sat` | constraint programming | complete PSP with optional verified warm start | global `OPTIMAL` only from full model |
| `fix-optimize-cp-sat` | LNS/matheuristic | small exact subproblems, unchanged resources fixed | conditional neighborhood optimum, never global |
| `restricted-highs-milp` | time-indexed set-partitioning MILP | limited candidate full-vessel columns, exact conflict model | `MASTER_OPTIMAL` applies to *restricted master only* |
| `adaptive-ruin-recreate` | adaptive neighborhood metaheuristic | randomized destroy/repair, regret insertion, simulated-annealing acceptance, no MILP/CP-SAT solver | feasible only, not a faithful published maritime ALNS |
| `identity` | feasibility control | unmodified verified incumbent | feasible only |

The set-partitioning MILP does **not** enumerate the complete PSP
feasible set, therefore it is not an independent full-formulation MILP
optimum. This distinction remains visible even when HiGHS says optimal.

Published maritime ALNS, decomposition, and commercial solver products
are **not yet independently reproduced** here. A literature mention or
a differently constrained model is not a comparable benchmark run.

## Required comparison protocol

1. Record exact input SHA256, split (train or test), repository source SHA,
   versions, OS and CPU, method, solver settings, seed and numerical tolerance.
2. Use identical input/objective and a common independently verified initial
   schedule for warm-start comparisons. Record source construction time
   separately. For cold starts, report the different start convention.
3. Give every method the same externally enforced wall deadline **from worker
   launch to receiving its result**, covering imports, construction, solver,
   serialization and worker overhead. If no result reaches the parent
   before the deadline: `TIMEOUT`, not `INFEASIBLE`, and return only the
   preserved incumbent with a clearly marked failed search.
4. Independently revalidate in the parent; compare all successful outputs
   against LACE's original evaluator. Never treat rejected candidates
   as successful or reward invalid schedules.
5. Record `OPTIMAL`, `FEASIBLE`, `UNKNOWN`, `TIMEOUT` and restricted-master
   statuses **separately**. A feasible fallback after an unknown search is
   not a solver-supplied optimality proof. Keep negative outcomes.
6. Aggregate paired comparisons **per input**, then across inputs. Different
   randomized seeds of one instance are not independent samples. Report
   median, coverage, number of instances, feasibility rates, gaps where
   global bounds exist, wall time, and hardware conditions.
7. Never tune on test instances. Keep train and test manifests explicit and
   register new methods before running untouched test splits.
8. Archive *all* outcomes in JSON with reproducible source hash. Treat a
   tiny selection of synthetic examples as exploratory, not SOTA evidence.

Currently `scripts/solver_matrix.py` enforces the strict timing and
feasibility rules for **four** implemented refiners (global CP-SAT,
CP-SAT fix-and-optimize, HiGHS MILP and a classical ALNS-style heuristic).
The first archived experiments contain **three** strategies, before the
ALNS-like comparator was introduced. The
original ten LACE heuristics have separate strict-wall comparisons under
`scripts/benchmark_lns_portfolio.py`. The full across-dataset replication,
hardware/calibration matching and multiple deadline sweeps remain future work.

## Current research evidence

* [Strict ten-method LACE baseline](../results/2026-10-27-lns-portfolio.md):
  12/12 paired wins by CP-SAT neighborhood hybrid in six held-out test
  inputs, short seven-second *allocated* budget, mean 6.33% reduced objective.
  This previous protocol allocated wall time equally but did not place the
  *entire* hybrid in a single hard-stop worker. Do **not** blend this claim
  with results from the newer strict common-incumbent protocol.
* [Three different solver families under exactly enforced wall limits](../results/2026-10-27-solver-matrix-heldout.md):
  12 paired trials on six original LACE test cases, 80–150 vessels. This
  stronger protocol shows speed–quality tradeoffs and explicit full CP-SAT
  timeouts.
* [Training-only solver comparison](../results/2026-10-27-solver-matrix-train.md)
* [Other held-out LNS comparison](../results/2026-10-27-lns-heldout.md)
* [Training parameter choice and negative results](../results/2026-10-27-lns-training.md)

All these are **research results on synthetic LACE instances**, not
comparisons with commercial terminal systems or real port operational logs.

## Publication checklist for new method adapters

* Source and license of original algorithm, theorem and implementation
  pinned (do not label a generic heuristic as a faithful published algorithm).
* Mathematical contract identical or explicitly a distinct track.
* Feasibility and objective independent cross-checks.
* A meaningful tiny-case oracle test where exact optimum can be proved.
* Deterministic seeds and safe no-solution / timeout behavior.
* Per-method resources, strict wall deadline, reproducible artifact.
* Include failures and null outcomes in summary, not only successes.
* No "beats commercial product" claim without running equivalent licensed
  product code against identical objective and constraints.

## Extensibility roadmap

Prioritize: (1) complete untouched test-set sweeps at several budgets,
(2) a genuinely independent published ALNS and full MILP/decomposition model
under the **same** PSP objective, (3) robust arrival-delay and tug-outage
replanning benchmark with feasibility and stability metrics, (4) separate
published quay crane, tidal berth and tug routing models with authorized
datasets. OpenAI mathematical k-server and k-median methods may be additional
tracks only after exact theorem-algorithm implementation is verified.

Academic motivation (not direct score comparators):

* [LACE, Nature Machine Intelligence 2026](https://www.nature.com/articles/s42256-026-01307-8)
* [MILP-ALNS berth and crane planning, Guissou et al., 2026](https://biblio.ugent.be/publication/01K5RKF5N72FMHYKPTZYCEGH43)
* [ADP-MLNS joint vessel and tug scheduling, 2026](https://www.sciencedirect.com/science/article/pii/S0029801826032671)
