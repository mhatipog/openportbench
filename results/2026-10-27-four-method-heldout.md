# PSP solver tournament — reproducible comparison

> Research benchmark, **not a claim of maritime state of the art**. These rankings apply only to the specified generated LACE PSP inputs, hardware, warm-start convention and strict wall budget.

- Dataset split: **test**; LACE source: `d772b74690075f641be8077e69748ec482e9febf`
- OpenPortBench runner: `2257a80fd9ff151e1e4bffbe5fc32d58a29595d1`
- Unique input files: **6**; paired source observations: **12**
- Common initial incumbent source wall budget: **2.0 s**; each independent refinement hard budget: **5.0 s**
- Exact primary JSON SHA256: `64aa0565e569dc64abe13cca96282fcf1a481c7909317e913c6f978ef2673f46`

## Summary (per-instance normalized improvements)

| Method | Mean improvement vs common source | Mean actual wall | Full timed-out / total | Invalid | Method wins (ties included) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `warm-cp-sat` | 0.00% | 4.49 s | 8/12 | 0 | 0 |
| `fix-optimize-cp-sat` | 8.65% | 4.71 s | 0/12 | 0 | 12 |
| `restricted-highs-milp` | 0.70% | 1.35 s | 0/12 | 0 | 0 |
| `adaptive-ruin-recreate` | 0.53% | 1.83 s | 0/12 | 0 | 0 |

A hard timeout returns a valid *preserved incumbent*, **not** a new solver success. HiGHS `MASTER_OPTIMAL` is optimal only within the restricted generated candidate set; it is not a full PSP bound. Likewise, a CP-SAT neighborhood optimum does not prove global PSP optimality. Scores from different problem sizes must never be compared directly without within-instance normalization.

## Instance-level paired outcomes

| Input | Seeds | `warm-cp-sat` mean improvement | `fix-optimize-cp-sat` mean improvement | `restricted-highs-milp` mean improvement | `adaptive-ruin-recreate` mean improvement |
| --- | ---: | ---: | ---: | ---: | ---: |
| `80_10_15_T48_010.txt` | 2 | 0.00% | 7.67% | 0.29% | 0.11% |
| `80_10_15_T48_011.txt` | 2 | 0.00% | 12.70% | 1.96% | 1.47% |
| `100_15_30_T48_010.txt` | 2 | 0.00% | 11.99% | 1.00% | 0.85% |
| `100_15_30_T48_011.txt` | 2 | 0.00% | 9.83% | 0.47% | 0.47% |
| `150_20_40_T48_010.txt` | 2 | 0.00% | 3.34% | 0.34% | 0.13% |
| `150_20_40_T48_011.txt` | 2 | 0.00% | 6.37% | 0.14% | 0.13% |

## Reproduce

Install `pip install -e '.[dev]'` plus `mip networkx`. Checkout LACE at the source revision above, then run `scripts/solver_matrix.py` with the exact sizes, indices, split, seeds and budgets recorded in the JSON. The original LACE scorer and an independent PSP checker validate every final solution.

All measurements were obtained without paid solver licenses. These comparisons do not constitute a reproduction of a published ALNS algorithm, a commercial system, or an OpenAI mathematical theorem.
