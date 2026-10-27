# Methodology and claims register

## Scope and equivalence

The baseline model is the **entire** discrete-time Port Scheduling Problem
(PSP) described by PJ-NTU/LACE, pinned at commit
`d772b74690075f641be8077e69748ec482e9febf`. We use its original input fields and solution structure.
Each vessel is either not served or receives one compatible berth, a common
inbound tug-team start and common outbound tug-team start. Tug power sum and
max team size are enforced separately for both services. Half-open service
intervals include LACE preparation time for tug non-overlap. Berth stays
cannot overlap. ETA/earliness/lateness constrain inbound start. Both stage
gaps are between zero and epsilon, inclusive. Outbound service must complete
by the horizon. Preparation can extend past the horizon, matching upstream.

The objective is
`lambda_1 * sum_unserved(M*alpha_i) + lambda_2 *
sum_served(alpha_i*beta_i*(t_out+tau_out-t_in)) + lambda_3 *
sum_served(alpha_i*gamma_i*abs(t_in-ETA_i)) + lambda_4 *
sum_used_tug_services(c_k*tau_service)`.
Decimal input costs are lifted to exact rational CP-SAT coefficients
(no floating point objective rounding); the scale is reported and capped
to prevent overflow-prone formulations. The independent verifier computes
the native floating-point objective, cross-checked with the CP-SAT objective
up to 1e-6 absolute tolerance.

No capacity or task constraint is dropped to make CP-SAT appear stronger.
An all-unserved schedule is feasible. The scorer rejects any resource overlap.
The model assumes nonnegative, integral times and positive durations as in
LACE's generator; exotic malformed inputs are not a supported benchmark.

## Reproduction protocol

1. Pin upstream source and data to a commit SHA, record checksums, solver
   versions, Python, OS, CPU and declared runtime budgets.
2. Run upstream's ten *shipped* portfolio heuristics on exactly the same
   unmodified instance, separately from any new search or training.
3. Record every heuristic's feasibility, objective, measured elapsed time and
   error. Only valid results count toward the per-instance portfolio minimum.
4. On PSP, re-score each feasible LACE result through the independent verifier,
   compare costs to upstream and fail loudly on disagreement.
5. Run FCFS, priority greedy, and full PSP CP-SAT with seed and solver bound.
   Check the CP-SAT solution with both independent and upstream evaluators.
6. Record configured budgets **and actual runtimes**. Portfolio has 10 x
   per-heuristic allocation, CP-SAT a single equal-total allocation. This
   aligns *allocated* CPU time, not overhead, parallelism or wall-time strictness.
7. Treat 1-instance smoke measurements as engineering evidence only. They
   cannot support general winner claims or effect-size confidence intervals.

LACE's `run_solve` does not enforce an external hard timeout. Individual
heuristics may exceed their own advisory time budget; flag such deviations
and avoid declaring a strictly equal-runtime competition in that case.

## Train/test and stochastic experiments

Original LACE `instances/train` and `instances/test` remain distinct.
Our smoke uses only one named training instance per problem. Never tune on
held-out `test`. Later studies must pre-register seeds and parameter grids,
fix tuning on train, freeze code, and evaluate a sufficiently large reserved
test set. Use paired instance differences, bootstrap confidence intervals
at the instance level, and report failures/timeouts. Aggregate comparisons
must not silently discard unsolved instances.

## Operational realism and research backlog

* Current PSP: generated academic instances, not port traffic, no channel
  tidal/safety constraints, pilot dispatch, berth geometry or real arrival data.
* Next: external BAP tidal window datasets; model them **separately**, since
  BAP and PSP are not mathematically equivalent. Inspect licenses before redistribution.
* Next: exact MILP in HiGHS/CBC, bounded heuristic-repair hybrids, adversarial
  small-instance exhaustive regression, CP-SAT performance profiling.
* Next: delay/outage scenario robustness and Pareto frontiers, with scenario
  distributions named and held fixed for each method; do not compare
  objectives from different constraint sets.
* OpenTNSim models vessel movements/discrete-event traffic, complementary to
  the scheduling benchmark rather than a drop-in baseline.
* The randomized online k-server result concerns serving requests by moving
  k servers under a metric. Tug movements could *eventually* form an online
  repositioning subproblem, but this is not a known solver or competitive
  guarantee for berth and tug scheduling.

## Data and license boundary

No LACE instances or heuristics are copied into OpenPortBench. The
reproduction workflow obtains LACE at a pinned source SHA, keeping
provenance visible. OpenPortBench's independently written code is MIT.
