# PSP solver tournament — reproducible comparison

> Research benchmark, **not a claim of maritime state of the art**. These rankings apply only to the specified generated LACE PSP inputs, hardware, warm-start convention and strict wall budget.

- Dataset split: **test**; LACE source: `d772b74690075f641be8077e69748ec482e9febf`
- OpenPortBench runner: `1bef1d38a86373d07c50a19bdc4946269934aa00`
- Unique input files: **6**; paired source observations: **12**
- Common initial incumbent source wall budget: **2.0 s**; each independent refinement hard budget: **5.0 s**
- Exact primary JSON SHA256: `eb5d9ddfdc975fcc370d632a307cf0c0b5f80b45a8afc9a7ff8371b031c9e559`

## Summary (per-instance normalized improvements)

| Method | Mean improvement vs common source | Mean actual wall | Full timed-out / total | Invalid | Method wins (ties included) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `warm-cp-sat` | 0.00% | 4.54 s | 8/12 | 0 | 0 |
| `fix-optimize-cp-sat` | 7.31% | 4.74 s | 0/12 | 0 | 11 |
| `restricted-highs-milp` | 0.68% | 1.53 s | 0/12 | 0 | 1 |

A hard timeout returns a valid *preserved incumbent*, **not** a new solver success. HiGHS `MASTER_OPTIMAL` is optimal only within the restricted generated candidate set; it is not a full PSP bound. Likewise, a CP-SAT neighborhood optimum does not prove global PSP optimality. Scores from different problem sizes must never be compared directly without within-instance normalization.

## Instance-level paired outcomes

| Input | Seeds | `warm-cp-sat` mean improvement | `fix-optimize-cp-sat` mean improvement | `restricted-highs-milp` mean improvement |
| --- | ---: | ---: | ---: | ---: |
| `80_10_15_T48_008.txt` | 2 | 0.00% | 7.46% | 0.25% |
| `80_10_15_T48_009.txt` | 2 | 0.00% | 11.58% | 0.00% |
| `100_15_30_T48_008.txt` | 2 | 0.00% | 2.67% | 0.33% |
| `100_15_30_T48_009.txt` | 2 | 0.00% | 11.36% | 2.43% |
| `150_20_40_T48_008.txt` | 2 | 0.00% | 6.01% | 1.08% |
| `150_20_40_T48_009.txt` | 2 | 0.00% | 4.76% | 0.00% |

## Reproduce

Install `pip install -e '.[dev]'` plus `mip networkx`. Checkout LACE at the source revision above, then run `scripts/solver_matrix.py` with the exact sizes, indices, split, seeds and budgets recorded in the JSON. The original LACE scorer and an independent PSP checker validate every final solution.

All measurements were obtained without paid solver licenses. These comparisons do not constitute a reproduction of a published ALNS algorithm, a commercial system, or an OpenAI mathematical theorem.
