# Frozen LNS: first held-out LACE PSP verification (27 October 2026)

This is a limited but **independently measured engineering finding**,
not a new mathematical theorem, optimality certificate, state-of-the-art
maritime benchmark, or validation with a real port's operational data.

## Prespecified evaluation

* [Successful pinned experiment](https://github.com/mhatipog/openportbench/actions/runs/40558571853)
* [Complete machine-readable run artifact](https://github.com/mhatipog/openportbench/actions/runs/40558571853/artifacts/12757029322)
* Source commit: `75180009b77af8f3e1a82b0e6311638e71dba146`;
  upstream LACE: `d772b74690075f641be8077e69748ec482e9febf`.
* Raw JSON SHA256:
  `27e6d53935ff0a1ab5055ea47bda487323fc89729e8ba2ae56cd07b8edd0a9bc`.
* Six previously unused original LACE **test** files: `_004` and
  `_005` from the 80-, 100- and 150-vessel families, with seeds 1 and 2.
  This was the first evaluation of the frozen LNS configuration on those files.
* LACE shipped heuristic_01 creates the **same** initial feasible solution
  for both methods, with 2.0-second hard wall deadline; no tuning on test.
* Refinement budget: nominal 5.0 seconds per method including Python model
  construction, actual wall measured. Warm global CP-SAT receives the hint;
  classical resource-blocked LNS uses 14-vessel neighborhoods, at most ten
  repair rounds. Both use one CP-SAT search worker. There is no claim of
  strictly identical consumed CPU time.
* Python 3.12.15; OR-Tools 9.15.6755; NumPy 2.5.4; SciPy 1.18.1; GitHub
  hosted Linux x86_64; AMD EPYC 7763, four logical CPUs.
* All 12 resulting pairs of schedules were validated with **both** the
  original LACE PSP evaluator and OpenPortBench's independently developed
  PSP verifier. Every input hash, measured wall/CPU duration and memory
  process high-water mark is present in the JSON artifact.

## Results

Lower PSP objective is better. Percentage is paired relative improvement
of LNS over warm full CP-SAT, averaged across the two files and two seeds
at each size; it is **not** a cross-size objective comparison.

| Vessels | Comparison pairs | Mean paired reduction | Range across pairs | Mean LNS refine wall | Mean full CP-SAT refine wall |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 80 | 4 | 13.95% | 10.12%–17.47% | 4.88 s | 5.18 s |
| 100 | 4 | 10.28% | 7.82%–12.93% | 4.26 s | 3.20 s |
| 150 | 4 | 4.40% | 3.61%–5.63% | 4.90 s | 5.41 s |

LNS improved the native objective in **12/12 paired runs**, across **6/6
distinct test instances**. Giving each instance equal weight after averaging
its two seeds, the mean relative reduction was **9.54%**. An exploratory
95% percentile bootstrap **clustered by instance** (2000 draws, seed 2026)
was **[6.15%, 12.88%]**. With only six selected synthetic instances,
this interval is descriptive and must not be interpreted as a general
population interval for operational port problems.

### Exact solver status matters

* 80 vessels: warm full CP-SAT returned `FEASIBLE` in 4/4 runs but did not
  improve the initial heuristic incumbent.
* 100 and 150 vessels: full CP-SAT returned **`UNKNOWN` in 8/8** runs
  and retained the independently verified heuristic incumbent via fallback.
  `UNKNOWN` is neither `INFEASIBLE` nor `OPTIMAL`.
* LNS's `HEURISTIC_FEASIBLE` status means an admissible solution, even
  when an individual conditional neighborhood has an exact proof. LNS
  provides **no global optimality bound or proof** for these instances.
* On the 100-vessel cases, full CP-SAT used somewhat **less** wall time,
  so the experiment establishes a quality advantage here, not a universal
  speedup. Actual time and fallback status must remain visible.

## Research conclusion and next required comparator

A restricted fix-and-optimize neighborhood reusing a valid incumbent appears
more effective than a single full warm CP-SAT solve at the short tested budgets.
But the finding is **relative to LACE heuristic_01 + CP-SAT**, not to LACE's
best-of-ten evolved **portfolio**. No new mathematical approximation bound,
theoretical improvement, or algorithmic novelty is claimed.

Next: run the frozen method against **all 10 original LACE portfolio
heuristics with actual enforced wall deadlines**, on previously unexamined
`_006` and `_007` test instances, while keeping budgets, CPU time,
infeasibility and resulting scores explicit. Do not use the exposed
`_004/_005` test samples for further parameter selection. Stop claiming
wins if the stronger portfolio baseline erases them.
