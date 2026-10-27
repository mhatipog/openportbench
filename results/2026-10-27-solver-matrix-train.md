# First fair solver-family tournament — training samples

Date: 27 October 2026. **Exploratory experiment, not state of the art.**

Source upstream PJ-NTU/LACE commit
`d772b74690075f641be8077e69748ec482e9febf`.
[Successful experiment](https://github.com/mhatipog/openportbench/actions/runs/40564515672)
at OpenPortBench commit `4e801fc00402a61be20e57c119ebeddc1319ce81`.
[Raw JSON artifact](https://github.com/mhatipog/openportbench/actions/runs/40564515672/artifacts/12762441580).
Raw JSON SHA256:
`fd01ee862532e22f88d256c7ca66a2ffad9f171c46c647595358ade912436b34`.

## Common protocol

Three source files, `20_2_3_T12_004.txt`,
`40_3_4_T12_004.txt`, `60_5_8_T12_004.txt`, plus corresponding
`_005` files. All are from the **train** split; seeds 1 and 2.
The original LACE heuristic_01 had a strict **0.8-second** process wall
budget to generate one common valid incumbent per paired method.

Each method then received an independently enforced **3.0-second** wall
deadline measured from worker launch until receipt of candidate, including
model building, process startup, execution, and serialization. Candidate
returns after deadline are ignored. The original LACE objective and the
independent PSP evaluator both validated all resulting schedules. Missing
optimizer candidates fall back to the **same** valid starting incumbent
with the solver labelled as `TIMEOUT`, not as having found an optimum.

Three competing algorithm families:

* Full global CP-SAT, complete PSP with hint.
* Exact CP-SAT submodels over neighborhoods, incumbent preserved; size 14.
* SciPy 1.18.1 / open-source HiGHS **restricted-master** time-indexed MILP,
  24 candidate patterns per vessel (maximum), two cheapest sufficient tug
  team options. This **does not enumerate all PSP plans** and its master's
  optimality is not a PSP global bound.

## Verified training results

All mean improvements compare the original PSP objective to the **common
verified heuristic_01 incumbent**, averaging each source instance equally
after aggregating two seed runs. Different instance objective magnitudes
must not be pooled before converting to within-instance percentages.

| Refiner | Mean improvement | Mean strict wall time | Completed valid / 12 | Hard timeouts |
| --- | ---: | ---: | ---: | ---: |
| CP-SAT fix-and-optimize LNS | **6.47%** | 2.22 s | 12 | 0 |
| HiGHS restricted-master MILP | 5.30% | **0.70 s** | 12 | 0 |
| Full warm-start CP-SAT | 1.30% | 2.59 s | 2 | 10 |

All full CP-SAT solver timeouts retained the source incumbent. On the two
20-vessel `_005` runs, full CP-SAT did finish and returned `OPTIMAL`.
All 12 HiGHS restricted-master runs returned `MASTER_OPTIMAL`, which
proves only their finite candidate master, **not** the true PSP optimum.

The faster restricted MILP result is scientifically useful even though it
produced worse objective values on average than the LNS refiner. It is
evidence for a speed/quality trade-off, not for academic solver dominance.
All trial input SHA256 hashes, statuses, source timings and per-run numbers
are preserved in the JSON.

## Next stage (must avoid tuning on exposed tests)

With these three method configurations fixed, compare on new original
`_008/_009` PSP test instances of 80/100/150 vessels, with a longer but
strict identical refinement deadline. Add published ALNS and full MILP
competitors only when their mathematical formulations and source rights
can be established. Treat different LACE scheduling families separately.
