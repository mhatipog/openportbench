# PSP solver tournament — reproducible comparison

> Research benchmark, **not a claim of maritime state of the art**. These rankings apply only to the specified generated LACE PSP inputs, hardware, warm-start convention and strict wall budget.

- Dataset split: **train**; LACE source: `d772b74690075f641be8077e69748ec482e9febf`
- OpenPortBench runner: `4e801fc00402a61be20e57c119ebeddc1319ce81`
- Unique input files: **6**; paired source observations: **12**
- Common initial incumbent source wall budget: **0.8 s**; each independent refinement hard budget: **3.0 s**
- Exact primary JSON SHA256: `fd01ee862532e22f88d256c7ca66a2ffad9f171c46c647595358ade912436b34`

## Summary (per-instance normalized improvements)

| Method | Mean improvement vs common source | Mean actual wall | Full timed-out / total | Invalid | Method wins (ties included) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `warm-cp-sat` | 1.30% | 2.59 s | 10/12 | 0 | 2 |
| `fix-optimize-cp-sat` | 6.47% | 2.22 s | 0/12 | 0 | 9 |
| `restricted-highs-milp` | 5.30% | 0.70 s | 0/12 | 0 | 3 |

A hard timeout returns a valid *preserved incumbent*, **not** a new solver success. HiGHS `MASTER_OPTIMAL` is optimal only within the restricted generated candidate set; it is not a full PSP bound. Likewise, a CP-SAT neighborhood optimum does not prove global PSP optimality. Scores from different problem sizes must never be compared directly without within-instance normalization.

## Instance-level paired outcomes

| Input | Seeds | `warm-cp-sat` mean improvement | `fix-optimize-cp-sat` mean improvement | `restricted-highs-milp` mean improvement |
| --- | ---: | ---: | ---: | ---: |
| `20_2_3_T12_004.txt` | 2 | 0.00% | 6.00% | 3.68% |
| `20_2_3_T12_005.txt` | 2 | 7.80% | 7.80% | 5.93% |
| `40_3_4_T12_004.txt` | 2 | 0.00% | 6.54% | 6.00% |
| `40_3_4_T12_005.txt` | 2 | 0.00% | 8.02% | 8.32% |
| `60_5_8_T12_004.txt` | 2 | 0.00% | 5.95% | 5.34% |
| `60_5_8_T12_005.txt` | 2 | 0.00% | 4.51% | 2.50% |

## Reproduce

Install `pip install -e '.[dev]'` plus `mip networkx`. Checkout LACE at the source revision above, then run `scripts/solver_matrix.py` with the exact sizes, indices, split, seeds and budgets recorded in the JSON. The original LACE scorer and an independent PSP checker validate every final solution.

All measurements were obtained without paid solver licenses. These comparisons do not constitute a reproduction of a published ALNS algorithm, a commercial system, or an OpenAI mathematical theorem.
