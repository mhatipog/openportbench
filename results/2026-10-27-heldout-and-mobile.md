# Independent PSP size-stratified and mathematical-subproblem results

Date: 2026-10-27. These are small **engineering experiments**, not state-of-the-art
claims. Separate mathematical problems and objective units must never be pooled.

## 1. LACE PSP: original held-out test instance per vessel-count tier

* [Successful workflow](https://github.com/mhatipog/openportbench/actions/runs/40550247223)
* [Original machine-readable JSONL artifact](https://github.com/mhatipog/openportbench/actions/runs/40550247223/artifacts/12753728321)
* OpenPortBench source f9ec76a4ab2a30d9e9527000982238bfa2caf985
* Upstream LACE pinned to d772b74690075f641be8077e69748ec482e9febf
* Seeds [1], ten published shipped LACE heuristics, advisory budget 0.15 s each.
* Original LACE and independent OpenPortBench PSP evaluators both accepted all
  **60 returned heuristic schedules** and agreed on each objective.
* Runner: AMD EPYC 9V74 80-Core, 4 logical CPUs; Linux 7.0.0-1017-azure
  x86_64; Python 3.12.15, OR-Tools 9.15.6755, NumPy 2.5.4, SciPy 1.18.1.
* Input file hashes, method-level CPU/wall times, process peak RSS, source
  revisions, seeds, costs and error records are in the JSONL artifact.

| Vessels | LACE test file | Best of 10 objectives | Observed sum of ten method wall times (s) | Runs over 1.1x advisory limit |
| ---: | --- | ---: | ---: | ---: |
| 80 | 80_10_15_T48_001.txt | 61342.713964 | 1.7032 | 6 / 10 |
| 100 | 100_15_30_T48_001.txt | 50152.724080 | 1.6026 | 3 / 10 |
| 150 | 150_20_40_T48_001.txt | 79877.150742 | 4.0529 | 9 / 10 |
| 250 | 250_20_50_T48_001.txt | 172790.127735 | 15.3386 | 9 / 10 |
| 300 | 300_25_60_T48_001.txt | 200804.761467 | 23.5316 | 9 / 10 |
| 500 | 500_40_100_T48_001.txt | 324577.105316 | 117.4553 | 9 / 10 |

**Negative result and protocol correction:** 45/60 method invocations exceeded
their advisory per-heuristic budget by >10%. In the largest tier, the sum of
actual heuristic runtimes was about **78.3 times** the allocated 1.5 s. The
upstream LACE runner passes a time-limit parameter but does not enforce a hard
timeout. It is therefore incorrect to treat these as equal-runtime portfolio
versus exact solver comparisons. This requires per-method hard wall-clock
enforcement and a pre-declared rule for solver/model setup time.

Our unhinted CP-SAT reached **UNKNOWN** without an incumbent on the 80-vessel
instance: nominal 1.5 s solver allocation, actual model-and-solve wall 1.8413 s,
reported lower bound 0.0. The bound is not evidence of an optimum or a useful
gap without a feasible incumbent. Larger tiers were SKIPPED_SIZE_CAP at >80
vessels, not solved or proven infeasible. CP-SAT peak RSS field 130232 KB
reflects process high-water memory, not independently attributable solver peak.

**Contamination note:** these six held-out instances are now exposed to
diagnosis. Do not tune methods on them and later call results on the same six
blinded. Any subsequent method must be frozen on the original train set and
evaluated on previously unused test instances, with the exposure stated.

## 2. Classical metric location and dispatch experiments

* [Successful run](https://github.com/mhatipog/openportbench/actions/runs/40550573039)
* [Raw 24-record artifact](https://github.com/mhatipog/openportbench/actions/runs/40550573039/artifacts/12753639557)
* Source commit 72661d9b7bc49ebed378e63d37e12c95d10220e9; Python 3.12.15,
  Linux 7.0.0-1017-azure x86_64.
* 12 predeclared seeds, no tuning. All examples **synthetic**.
* Exact small-instance solvers used as independent reference; these
  algorithms DO NOT reproduce OpenAI #110 or #125.

| Study | Exact offline objective (mean) | Greedy/nearest mean | Improved/other mean | Interpretation |
| --- | ---: | ---: | ---: | --- |
| k-median: 5x5 Manhattan grid, 3 bases, 25 weighted demands | 127.0833 | Forward-greedy 138.4167 | Best one-swap 133.0833 | One-swap better than greedy by 5.3333 units, but still 6.0 above exact on average; exact solution reached in 3/12 seeds |
| k-server: 8-node cycle metric, 2 servers, 30 requests | 29.7500 | Nearest 31.8333 | Random-two 48.8333; next-request preview 31.5833 | Randomization *hurt* this simplistic policy. Preview used unavailable future requests and only helped by 0.25 edges on average |

The mean values are descriptive only; twelve synthetic instances do not
justify maritime performance claims, competitive ratio guarantees or
improvements to the published mathematical algorithms. In particular,
preview2 is **not online** and cannot be presented as a practical policy
without advance demand forecasts.

## 3. What the measurements change

* Prioritize correct **wall-time enforcement** and instance sharding before
  running all 100 held-out instances. Recording just the advisory time hides
  two orders of magnitude of work on the largest example.
* Restore feasible CP-SAT incumbents through independently validated
  heuristic hints, and charge heuristic time to the hybrid's entire budget.
* Benchmark promising optimizers first on training tiers 20/40/60 vessels,
  then freeze versions before testing previously unused large instances.
* Keep strategic base location and dynamic dispatch separate from berth/tug
  integrated PSP: their objectives and feasible sets differ.
