# PSP hybrid replication and actual proof-status audit — 27 October 2026

These are fixed, small paired engineering trials, not general SOTA evidence.
Source LACE commit: d772b74690075f641be8077e69748ec482e9febf.
All returned candidates were checked with both the upstream PSP evaluator and
OpenPortBench's independent evaluator, with independently evaluated cost.

## Model and comparison

CP-SAT is the complete discrete LACE PSP formulation, one search worker,
OR-Tools 9.15.6755. The hybrid gives CP-SAT a **validated**, complete LACE
heuristic_01 incumbent. The cold solver gets no hint. There is no hard fixing
of decisions. Both receive approximately two seconds total allocated work on
train, and five seconds on test. Heuristic construction time is deducted from
the hybrid solver's allocation, and both total wall times include model setup
overhead, occasionally exceeding allocation. Seed 1, 2, 3 comparisons
alternate the order of cold/hybrid to reduce caching/order bias.

The new incumbent-preserving wrapper can return an independently validated
heuristic candidate when CP-SAT never discovers one. In that situation
CP-SAT search status remains UNKNOWN, incumbent_source is verified_hint,
raw_solver_objective is null, and the hybrid does **not** claim an exact
search solution or a proof.

## Stage 1: original training tiers (source 0c18b653)

[Verified train run](https://github.com/mhatipog/openportbench/actions/runs/40551425051),
[raw artifact](https://github.com/mhatipog/openportbench/actions/runs/40551425051/artifacts/12754023533).

| Vessel tier | Mean cold objective (3 seeds) | Mean heuristic-hinted objective | Improvement in cost | Pairwise wins / ties / losses |
| ---: | ---: | ---: | ---: | --- |
| 20 | 12736.2769 | 12736.2769 | 0.0% | 0 / 3 / 0 |
| 40 | 27681.6323 | 27517.9266 | 0.59% | 2 / 0 / 1 |
| 60 | 45833.0870 | 39976.2156 | 12.78% | 3 / 0 / 0 |

All reported CP-SAT outputs were feasible; none of these fixed-budget
runs were proven optimal. With three seeds and one input per tier, there
is no defensible statistical generalization.

## Stage 2: first previously untested held-out files ending in 002
(source 0b617acc; before fallback implementation)

[Verified test run](https://github.com/mhatipog/openportbench/actions/runs/40552310581),
[raw artifact](https://github.com/mhatipog/openportbench/actions/runs/40552310581/artifacts/12755556529).

* At 80 vessels: cold CP-SAT produced 88093.5843 for each of three seeds;
  hinted CP-SAT scored 57836.4566, 56623.5301, 56193.1648.
* At 100 vessels: cold and hinted CP-SAT both reported UNKNOWN with no
  feasible incumbent in all three seeds. The source LACE heuristic itself
  returned valid candidates in about 0.33 s. This diagnosis motivated
  an incumbent-preserving fallback. It is not evidence of infeasibility.
* These 002 cases are now exposed and cannot be used for later blind
  validation of changes motivated by them.

## Stage 3: frozen incumbent preservation, new test files ending in 003
(source fbef0502; separate first use of 003 files)

[Verified test run](https://github.com/mhatipog/openportbench/actions/runs/40553292608),
[raw artifact](https://github.com/mhatipog/openportbench/actions/runs/40553292608/artifacts/12754484836).

| Vessel tier | Cold CP-SAT (seeds 1/2/3) | Hybrid final incumbent (seeds 1/2/3) | Proof/selection |
| --- | --- | --- | --- |
| 80 | 86272.9508 / 86272.9508 / 86272.9508 | 56387.7679 / 59308.0064 / 55710.4588 | CP-SAT FEASIBLE all; 2/3 equal to initial LACE hint, 1/3 improved hint by ~2.282 |
| 100 | no incumbent / no incumbent / no incumbent | 50865.1077 / 51674.0545 / 50783.3880 | CP-SAT UNKNOWN all; **verified_hint fallback** all, no CP-SAT-feasible incumbent or proof |

The difference between 80-vessel cold and hinted CP-SAT is large, but
almost all of the gain comes from the preexisting source heuristic's
incumbent. We do **not** claim that the CP-SAT search improved those
three objective values by that entire margin. The 100-vessel fallbacks
prevent loss of a valid candidate, not a research-level solve breakthrough.

## Stage 4: hard-deadline bias audit

[Corrected strict-wall run](https://github.com/mhatipog/openportbench/actions/runs/40553225194),
[raw artifact](https://github.com/mhatipog/openportbench/actions/runs/40553225194/artifacts/12755209156).

One seed, ten shipped LACE heuristics per case, 0.5 s **hard wall budget**
per run including worker startup (shared NumPy imports preloaded).

| PSP vessels | Feasible runs / 10 | Timeouts / 10 |
| ---: | ---: | ---: |
| 20 (train) | 10 | 0 |
| 80 (already exposed test case 001) | 4 | 6 |
| 500 (already exposed test case 001) | 0 | 10 |

This is an important **negative result**. It demonstrates that claims
using LACE's unbounded advisory timers need a corrected wall-clock
protocol. No returned feasible schedule on the 500-vessel instance
means an unserved result at the deadline, **not mathematical infeasibility**.
The first implementation incorrectly charged repeated worker import
startup; that result was invalidated, the worker fixed to drain pipe
before join, common imports preloaded, and the entire audit rerun.

## Research implications

* First priority: benchmark a *shared usable incumbent* on all scales,
  with explicit source and full construction time, before exact refinement.
* CP-SAT needs local-neighborhood/decomposition work to scale beyond
  approximately 80 vessels within this short budget. At 100 it could
  not find a model incumbent even when given feasible hints.
* Keep provenance/status/upper-bound fields separate. A fallback incumbent
  does not convert UNKNOWN into FEASIBLE or OPTIMAL solver proof status.
* Full 100-case held-out replication has **not** been completed. Remaining
  test instances need pre-registered shard selection, proper deadline
  enforcement and checkpoints, without tuning on already inspected tests.
* Not implemented or tested: faithful OpenAI #110/#125 algorithms, full
  tug-family independent evaluators, HiGHS/CBC for complete PSP, real port
  operational data, robust outage/replanning trials.
