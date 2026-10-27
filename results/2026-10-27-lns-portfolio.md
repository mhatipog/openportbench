# Prespecified frozen LNS vs the shipped full LACE portfolio

**27 October 2026 — Completed and independently validated.**
This is a concrete short-runtime algorithm engineering result on LACE's
generated research PSP test data, **not** a new approximation theorem,
a global optimization proof, operational port validation, or a claim
to be state of the art across maritime planning literature.

## Reproducible evidence

* [Successful GitHub Actions run](https://github.com/mhatipog/openportbench/actions/runs/40559857046)
* [Original 12-pair JSON artifact](https://github.com/mhatipog/openportbench/actions/runs/40559857046/artifacts/12760830549)
* Raw JSON SHA256:
  `55c66737014022846b4c17a146c51381e94b9c132960bfd5cad05ce37b7510df`
* Benchmark source commit `a1fb1f374cc2882f563879b9d298538544e4dfaa`;
  original LACE source `d772b74690075f641be8077e69748ec482e9febf`.
* Six **previously unused** original test files ending `_006` and `_007`
  in the 80-, 100- and 150-vessel families; two seeds (1, 2) per file.
  The frozen LNS parameters (neighborhood=14, max rounds=10) were selected
  using **training** data and not modified for this comparison.
* Four logical CPU GitHub-hosted x86_64 Ubuntu/Linux runner, Python 3.12.15,
  OR-Tools 9.15.6755; all code and data are freely reproducible.
* Every feasible result was independently scored by OpenPortBench's
  separately written PSP evaluator **and** the original LACE evaluator.
  Infeasible/error/timeout results do not count toward portfolio best.

## Equal allocated budget, not equal actual compute

Baseline: ten **unchanged shipped LACE portfolio heuristics**; each gets a
true, externally enforced 0.7-second deadline, including worker startup
and evaluation, for 7 seconds of *allocated* aggregate wall time.

Hybrid: original LACE heuristic_01 has an externally enforced 2-second
deadline and then restricted-resource CP-SAT LNS has a nominal 5-second
refinement budget. LNS measures end-to-end model setup but has a soft
outer limit; every actual wall time is recorded. **The two methods are
not identical search algorithms or identical consumed CPU time.**

Original LACE's unbounded advisory runner is deliberately not used for
this comparison. Some LACE heuristic executions time out here; counting a
timed-out method's hypothetical late answer would invalidate the runtime
claim.

## Paired objective results

All values use **the original LACE integrated PSP objective**, lower is better.
Paired percentage: `100*(best-LACE-portfolio - LNS)/best-LACE-portfolio`.

| Vessel count | Independent test cases | Seeded pairs where LNS better | Mean LNS reduction | Mean LACE portfolio wall | Mean hybrid wall |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 80 | 2 | 4/4 | **4.36%** | 6.74 s | 4.94 s |
| 100 | 2 | 4/4 | **7.19%** | 6.89 s | 6.51 s |
| 150 | 2 | 4/4 | **7.43%** | 6.95 s | 5.83 s |
| **Total** | **6** | **12/12** | **6.33%** (instance-weighted) | — | — |

At the **instance** level, mean paired improvements across two seeds:

| Held-out PSP file | Mean reduction |
| --- | ---: |
| `80_10_15_T48_006.txt` | 4.37% |
| `80_10_15_T48_007.txt` | 4.35% |
| `100_15_30_T48_006.txt` | 7.91% |
| `100_15_30_T48_007.txt` | 6.47% |
| `150_20_40_T48_006.txt` | 7.72% |
| `150_20_40_T48_007.txt` | 7.14% |

A descriptive 95% percentile bootstrap clustered by **original instance**
(2000 resamples, deterministic seed 2026) was **[5.18%, 7.45%]** for
the instance-weighted average reduction. This interval does not
account for sampling only six particular synthetic instances and
cannot establish an effect for real ports, other planning models or
unsampled difficulty categories.

### Feasibility and failure accounting

* LACE best-of-ten: 86/120 attempts finished feasibly; **34/120** timed
  out under the strict 0.7-second bound, not mathematical infeasibility.
  Feasible counts: 40/40 at 80 vessels; 30/40 at 100; 16/40 at 150.
* Each of the 12 final hybrid solutions was valid under both evaluators.
  This is a heuristic feasible incumbent; it does **not** certify global
  optimality or provide a new approximation factor.
* Neither competitor exceeded 110% of its nominal **aggregate wall budget**
  in the measured runs. All original method-level statuses, wall times,
  error messages, input SHA256 hashes and output objectives are in the
  original JSON.
* The hybrid sometimes used less wall time than its allocation, whereas
  the portfolio consumed nearly all. We do not infer universal algorithm
  speedups from the observed CPU and wall differences.

## What is genuinely useful, and what remains unproven

**Useful:** On these six held-out synthetic integrated PSP instances with
a short 7-second budget, feasible incumbent + exact conditional resource
neighborhoods consistently returned lower cost than both single global
warm CP-SAT and the full shipped LACE heuristic portfolio under the
specified strict-wall protocol. The method avoids full-model growth
by fixing berth and tug intervals for unmodified vessels.

**Not proven:** superiority at longer budgets, results on full 100-instance
LACE test set, statistical generalization, global optimality, robustness to
tug outages/late arrivals, or novelty over prior published fix-and-optimize
and ALNS approaches.

**Next:** a reproducible stratified wider test across untouched instances
with the *same frozen code* and multiple budgets, then controlled arrival
perturbation and repair. Compare with published ALNS/matheuristics on
mathematically identical data before claiming broader state-of-the-art
performance. Do not retune against now-exposed `_004`–`_007` files.
