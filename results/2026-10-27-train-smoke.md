# Verified training-instance smoke run — 27 October 2026

**Status:** 4/4 LACE portfolios executed with successful run; one independent
PSP exact comparison completed. This is a small reproducibility smoke test,
**not** reproduction of the aggregate statistics in the LACE paper.

* [Successful GitHub Actions run](https://github.com/mhatipog/openportbench/actions/runs/40546686818)
* [JSON report artifact (expires 10 November 2026)](https://github.com/mhatipog/openportbench/actions/runs/40546686818/artifacts/12752219395)
* OpenPortBench source commit `24637ff83b3f3edb8729e1efea1087be3bf787b5`
* LACE source commit `d772b74690075f641be8077e69748ec482e9febf`

## Measured values

Scores are LACE-defined cost units, **lower is better**. All portfolios used
ten shipped heuristic implementations, each allocated 0.35 seconds and seeded
with 1. All 40 heuristic runs returned upstream-feasible results; no run
exceeded the 10%-tolerance advisory budget check.

| Training instance | LACE portfolio best | Total observed LACE run time (s) |
| --- | ---: | ---: |
| PSP `20_2_3_T12_001.txt` | 13542.1118377 | 3.260268 |
| Multi-tug routing+scheduling `n10_K5_T24_00001.txt` | 18317.7405612 | 3.314972 |
| Multi-base tug routing+scheduling `12_6_3_001.txt` | 4123.31118688 | 3.253010 |
| Variable-speed tug routing `n10_m3_a30_001.txt` | 2428.35454767 | 2.559313 |

Upstream evaluator was used for all four problem families. For PSP only,
every feasible LACE result was **additionally checked against OpenPortBench's
independently implemented evaluator**, including the objective.

### PSP: four baselines on the same instance

| Method | Certified objective | Actual wall time (s) | Bound | Proof status |
| --- | ---: | ---: | ---: | --- |
| FCFS greedy | 14658.9480462 | 0.140641 | — | Feasible, unproven |
| Priority greedy | 13620.5165893 | 0.167586 | — | Feasible, unproven |
| LACE ten-heuristic portfolio | 13542.1118377 | 3.260268 (sum) | — | Feasible, unproven |
| CP-SAT (1 worker, seed 1) | **12736.2769343** | **2.091971** | **12736.2769343** | **OPTIMAL** |

CP-SAT's available time budget was 3.5 seconds (= 10 x 0.35 s), and it
terminated with a proven optimum in about 2.09 seconds. Its objective was
805.8349034 lower than this LACE portfolio result (5.9506% relative
reduction). **No speedup or statistical generalization is claimed.**
Differences in external Python overhead and best-of-ten selection remain
important; this is a single instance, not a solver leaderboard.

## Reproducibility metadata

| Component | Recorded value |
| --- | --- |
| Execution | Public GitHub-hosted `ubuntu-latest` runner |
| Platform | Linux 6.17.0-1022-azure x86_64, glibc 2.39 |
| CPU architecture / logical CPUs | x86_64 / 4 (specific CPU SKU not reported) |
| Python | 3.12.15 |
| OR-Tools | 9.15.6755 |
| NumPy | 2.5.4 |
| SciPy | 1.18.1 |
| CP-SAT objective scale | 10,000,000 |
| CP-SAT threads | 1 |
| Random seed | 1 |

The instance SHA256 digests recorded in the uploaded JSON are:

| Input | SHA256 |
| --- | --- |
| PSP | `2cd9fc87132b535588e22dec70b4595ef1e1163c6f2ae4b7a4b3b6ecfd7298cb` |
| Tug routing+scheduling | `7bbb2589a46554488bf5be5e6248b05bcc585fcfd661def5036c3daa48eaae45` |
| Multi-base tug routing+scheduling | `a45482d26d7e9bf7cf6d74b7321fffc856f80c75d340a715fa271d7f4d13f836` |
| Variable-speed tug | `e9c250bcabb9ad68817a63ffbf83402be625d126ffd281cb2f2b8856f923106c` |

## Limitations and next experiments

* Four portfolios reproduced on *one training instance each*, not the
  paper's 100 test instances per problem. No evidence yet of performance
  gains at scale, under uncertainties, or on real port traffic.
* Three tug families still rely on upstream LACE validation only. Their
  results must not be compared numerically with PSP objectives.
* This was not a blind evaluation. A meaningful next study should fix methods
  and seeds on train, then run a larger untouched test suite and report
  paired comparisons, infeasibility counts and uncertainty.
* We have **not** yet implemented HiGHS/CBC MILP, hybrid repair, Pareto
  analysis, failure scenarios or a separate ORlib berth-allocation contract.
