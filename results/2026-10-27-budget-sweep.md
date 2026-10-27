# Strict end-to-end wall-time PSP algorithm performance profiles

> Exploratory synthetic benchmark. There is no commercial or published SOTA equivalence implied by these rankings.

- Source: **LACE** commit `d772b74690075f641be8077e69748ec482e9febf`, **test** split
- Runner: `e9cb07334951530ca102a8be26aa7abf62ea4b91`
- Unmodified input instances: **6**; observations with different random seeds: **12**
- Source heuristic strict construction budget: **2.0 s** (common to every method AND all refinement budgets within a trial)
- Method refinement deadlines (strict worker-launch-to-response): **3 s**, **10 s**
- Raw primary JSON SHA256: `76e5d3d62c2e9233acf841fad11d74965d60ac726a64263ba961774141bde815`
- Failed source construction: **0** of 12; those trials are excluded from paired rankings

## Equal-budget comparisons

| Budget | Method | Mean per-instance gain | 95% cluster bootstrap CI* | Mean observed wall | Hard timeouts | Successful outputs |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 3 s | `warm-cp-sat` | 0.00% | [0.00%, 0.00%] | 2.85 s | 10/12 | 2/12 |
| 3 s | `fix-optimize-cp-sat` | 5.35% | [2.61%, 8.51%] | 2.91 s | 0/12 | 12/12 |
| 3 s | `restricted-highs-milp` | 0.26% | [0.03%, 0.59%] | 1.94 s | 4/12 | 8/12 |
| 3 s | `adaptive-ruin-recreate` | 0.21% | [0.02%, 0.55%] | 1.87 s | 4/12 | 8/12 |
| 10 s | `warm-cp-sat` | 0.00% | [0.00%, 0.00%] | 9.40 s | 10/12 | 2/12 |
| 10 s | `fix-optimize-cp-sat` | 9.02% | [4.33%, 14.29%] | 5.80 s | 0/12 | 12/12 |
| 10 s | `restricted-highs-milp` | 0.26% | [0.03%, 0.59%] | 4.27 s | 4/12 | 8/12 |
| 10 s | `adaptive-ruin-recreate` | 0.21% | [0.02%, 0.55%] | 4.22 s | 4/12 | 8/12 |

*95% confidence intervals are **descriptive percentile bootstrap intervals over distinct instance files** (3,000 resamples, seed 2026). With few instances they can be unreliable; seeds of a single instance are NOT independent research replications. These intervals do not account for benchmark/dataset selection bias.

## Per-instance improvement curves

| Input | Seeds | Budget | `warm-cp-sat` | `fix-optimize-cp-sat` | `restricted-highs-milp` | `adaptive-ruin-recreate` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `80_10_15_T48_012.txt` | 2 | 3 s | 0.00% | 8.84% | 0.00% | 0.00% |
| `80_10_15_T48_012.txt` | 2 | 10 s | 0.00% | 9.95% | 0.00% | 0.00% |
| `100_15_30_T48_012.txt` | 2 | 3 s | 0.00% | 11.83% | 1.00% | 1.00% |
| `100_15_30_T48_012.txt` | 2 | 10 s | 0.00% | 19.72% | 1.00% | 1.00% |
| `150_20_40_T48_012.txt` | 2 | 3 s | 0.00% | 4.22% | 0.37% | 0.16% |
| `150_20_40_T48_012.txt` | 2 | 10 s | 0.00% | 13.14% | 0.37% | 0.16% |
| `250_20_50_T48_012.txt` | 2 | 3 s | 0.00% | 3.45% | 0.20% | 0.13% |
| `250_20_50_T48_012.txt` | 2 | 10 s | 0.00% | 6.86% | 0.20% | 0.13% |
| `300_25_60_T48_012.txt` | 2 | 3 s | 0.00% | 2.12% | 0.00% | 0.00% |
| `300_25_60_T48_012.txt` | 2 | 10 s | 0.00% | 2.11% | 0.00% | 0.00% |
| `500_40_100_T48_012.txt` | 2 | 3 s | 0.00% | 1.61% | 0.00% | 0.00% |
| `500_40_100_T48_012.txt` | 2 | 10 s | 0.00% | 2.37% | 0.00% | 0.00% |

## Interpretation

Improvements are percentage reductions of the independently verified complete four-term PSP objective versus the **same source schedule** across all budgets in a paired trial. A timeout preserves that source score as an explicit fallback, never counts as a feasible solver output, and must not be labelled optimal. Fully timed CP-SAT is the only complete PSP model; HiGHS is optimal only over candidate columns and ALNS/LNS give no global certificates. A wall-time deadline is not equal CPU consumption. No single approach is declared universal SOTA.

## Original benchmark provenance

- [Successful original Actions run](https://github.com/mhatipog/openportbench/actions/runs/40576919339)
- [Immutable raw Actions artifact](https://github.com/mhatipog/openportbench/actions/runs/40576919339/artifacts/12767942280)
- Complete raw input hashes and all failed/time-limited solver outcomes: [archived JSON](raw/2026-10-27-budget-sweep.json)
- Python dependency snapshot: [archived environment](raw/2026-10-27-budget-sweep-dependencies.txt)
