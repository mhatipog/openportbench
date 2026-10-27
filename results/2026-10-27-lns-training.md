# PSP restricted CP-SAT neighborhood ablation — training only

Date: 2026-10-27. **This is not a maritime state-of-the-art claim.**

## Problem and methods

Same original LACE integrated PSP mathematical formulation and objective.
Input origin: PJ-NTU/LACE pinned at commit
`d772b74690075f641be8077e69748ec482e9febf`.
All 9 experiment observations per configuration used LACE's **train** split:
`20_2_3_T12_002.txt`, `40_3_4_T12_002.txt`,
`60_5_8_T12_002.txt`; seed 1, 2 and 3 per file.

All methods started from the *same* LACE shipped `heuristic_01` incumbent,
returned within a real 0.6-second **hard process deadline**, and validated
independently against both OpenPortBench and original LACE evaluators.
Then each method received the same nominal **2.5-second refinement allocation**,
including measured but not strictly externally terminated Python model setup.
Actual wall time, CPU, input hashes, solver statuses, memory high-water mark
and individual round results are in the archived Actions JSON artifacts.
CPU: GitHub-hosted AMD EPYC 7763, four logical CPUs; Python 3.12.15;
OR-Tools 9.15.6755 single search worker, NumPy 2.5.4, SciPy 1.18.1.

Both LNS variants use the exact conditional PSP model with other vessels'
berth/tug occupancy modeled as fixed blocking intervals. LNS **never** proves
global PSP optimality when its restricted neighborhood is optimal; report
`HEURISTIC_FEASIBLE` separately from true CP-SAT search and proof status.

## Configuration and paired results

* [V1 workflow](https://github.com/mhatipog/openportbench/actions/runs/40557587715)
  source `4aaca17b7ba0fe46e70f59e031a3b6779fab508f`;
  neighborhoods of **10**, maximum **5** rounds;
  [raw JSON](https://github.com/mhatipog/openportbench/actions/runs/40557587715/artifacts/12757139011),
  SHA256 `4f111bb9b8027f0b29e88ade2961d87226351d9c86304474eff10010091e00fd`.
* [V2 workflow](https://github.com/mhatipog/openportbench/actions/runs/40558019714)
  source `830d8ec4dab5aba6b23bba9d3ea532fb8ab29f08`;
  neighborhoods of **14**, maximum **10** rounds;
  [raw JSON](https://github.com/mhatipog/openportbench/actions/runs/40558019714/artifacts/12757853503),
  SHA256 `ed89a05574b7f37a022349da40e29f12d2e9cac3a00027f8414ed2d1436a9b1e`.

Lower objective is better; means across three *seeds on the same instance*.

| Vessels | V1 LNS mean | V2 LNS mean | V2 warm full CP-SAT mean | V2 gain vs warm full | V2 mean LNS wall / CP wall |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | 12216.7195 | 12188.4498 | 12188.4498 | tie | 0.346 / 0.536 s |
| 40 | 28187.7161 | 27181.5123 | 27973.4445 | 2.83% lower | 1.337 / 2.516 s |
| 60 | 38546.4049 | 37387.1761 | 39133.6106 | 4.46% lower | 1.845 / 2.533 s |

V2 had 3/3 wins versus warm full at both 40 and 60 vessels,
and 3/3 ties at 20 vessels. V1 lost to warm full on average at 20 and 40.
The changes are measured **training-set observations**; three seeds on one
input per size cannot estimate general population performance or robust
confidence intervals. Timings and scores differ slightly between separately
scheduled V1/V2 runs even for the same CP-SAT formulation.

## Frozen decision before held-out experiments

Freeze `neighborhood_size=14`, `max_rounds=10`, seed behavior and selection
logic at the V2 source version. No further adjustment based on LACE test data.
Evaluate on previously unused `_004` and `_005` test instances in 80/100/150
vessel groups, with a hard 2-second construction deadline and nominal
5-second refinement allocation. Keep every failure/timeout and candidate
provenance. The `_001`–`_003` test samples were previously inspected, so
must not be reused as blind confirmation for this revised method.

LNS remains an engineering implementation of classical fix-and-optimize
(matheuristic) ideas, **not** a new approximation-theory result.
