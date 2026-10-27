# PSP solver tournament — reproducible comparison

> Research benchmark, **not a claim of maritime state of the art**. These rankings apply only to the specified generated LACE PSP inputs, hardware, warm-start convention and strict wall budget.

- Dataset split: **train**; LACE source: `d772b74690075f641be8077e69748ec482e9febf`
- OpenPortBench runner: `082f4504eca1d49ef6a9ca2203234e67253b59cd`
- Unique input files: **6**; paired source observations: **12**
- Common initial incumbent source wall budget: **0.8 s**; each independent refinement hard budget: **3.0 s**
- Exact primary JSON SHA256: `5f0b0e6a79df90541f19bf311cae9adec502a9e07c6d13c701a43bf7ec17b124`

## Summary (per-instance normalized improvements)

| Method | Mean improvement vs common source | Mean actual wall | Full timed-out / total | Invalid | Method wins (ties included) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `warm-cp-sat` | 1.18% | 2.75 s | 10/12 | 0 | 2 |
| `fix-optimize-cp-sat` | 6.50% | 2.40 s | 0/12 | 0 | 12 |
| `restricted-highs-milp` | 3.40% | 1.28 s | 1/12 | 0 | 0 |
| `adaptive-ruin-recreate` | 1.11% | 0.66 s | 0/12 | 0 | 0 |

A hard timeout returns a valid *preserved incumbent*, **not** a new solver success. HiGHS `MASTER_OPTIMAL` is optimal only within the restricted generated candidate set; it is not a full PSP bound. Likewise, a CP-SAT neighborhood optimum does not prove global PSP optimality. Scores from different problem sizes must never be compared directly without within-instance normalization.

## Instance-level paired outcomes

| Input | Seeds | `warm-cp-sat` mean improvement | `fix-optimize-cp-sat` mean improvement | `restricted-highs-milp` mean improvement | `adaptive-ruin-recreate` mean improvement |
| --- | ---: | ---: | ---: | ---: | ---: |
| `20_2_3_T12_006.txt` | 2 | 7.10% | 7.10% | 5.32% | 0.87% |
| `20_2_3_T12_007.txt` | 2 | 0.00% | 9.20% | 6.68% | 2.06% |
| `40_3_4_T12_006.txt` | 2 | 0.00% | 6.84% | 1.44% | 0.48% |
| `40_3_4_T12_007.txt` | 2 | 0.00% | 3.03% | 0.85% | 1.35% |
| `60_5_8_T12_006.txt` | 2 | 0.00% | 6.35% | 2.26% | 0.51% |
| `60_5_8_T12_007.txt` | 2 | 0.00% | 6.48% | 3.84% | 1.38% |

## Reproduce

Install `pip install -e '.[dev]'` plus `mip networkx`. Checkout LACE at the source revision above, then run `scripts/solver_matrix.py` with the exact sizes, indices, split, seeds and budgets recorded in the JSON. The original LACE scorer and an independent PSP checker validate every final solution.

All measurements were obtained without paid solver licenses. These comparisons do not constitute a reproduction of a published ALNS algorithm, a commercial system, or an OpenAI mathematical theorem.
