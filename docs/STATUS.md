# Project handoff — 27 October 2026

**Disposition: usable research benchmark; current experiment complete.
No pending publish action or operational deployment is claimed.**

## What a new maintainer can do now

1. Install the open-source Python package on Python 3.12+ and Linux/Unix:
   `python -m pip install -e '.[dev]'`, then `pytest -q`.
2. Compare the four registered PSP refiners against one valid LACE-format
   input using `openportbench compare instance.txt --seconds 3 --seed 1`.
   The default starting schedule is all-unserved; a stronger one can be
   supplied with `--initial-json`.
3. Reproduce a pinned full LACE comparison using
   [the exact source checkout and command](reproduction.md).
4. Examine the canonical [multi-budget scorecard](../results/2026-10-27-budget-sweep.md)
   and checksum-verified [archived data](../results/raw/2026-10-27-budget-sweep.json)
   before reporting any result.

## Recorded evidence at handoff

| Area | State | Evidence |
| --- | --- | --- |
| Four PSP refinement strategies | Implemented and tested | [Benchmark protocol](benchmarking.md) |
| Six original test inputs, 80–500 vessels | Completed, 2 seeds each | [Canonical results](../results/2026-10-27-budget-sweep.md) |
| Strict 3 s and 10 s refinement deadlines | Enforced by separate subprocess | [Original run](https://github.com/mhatipog/openportbench/actions/runs/40576919339) |
| Independent objective/feasibility validation | Included, cross-checked with upstream LACE in archived experiments | [Model specification](methodology.md) |
| Raw JSON, SHA256, original software revision, packages | Archived | [Raw results](../results/raw/2026-10-27-budget-sweep.json) |
| CI | Successful at handoff | [CI workflow](../.github/workflows/ci.yml) |
| Academic published-ALNS reimplementation | **Not done** | [Research matrix](research-matrix.md) |
| Actual port dispatch and commercial comparisons | **Not done** | [Scope limitations](methodology.md) |

**Verified research finding:** among the four implementations tested on
this frozen synthetic LACE study, CP-SAT LNS had the best paired solution
quality in 12/12 attempts for both studied runtime deadlines. At 3 s / 10 s,
its instance-weighted mean objective improvements over the common incumbent
were 5.35% / 9.02%. Other approaches' timeout fallbacks remain
explicitly recorded. The confidence intervals are exploratory and cover
only six distinct instance files.

## Known limitations

The data are generated research problems, not vessel movement logs from an
operating port. Methods use different internal CPU workloads even under an
equal elapsed-time cap. Full CP-SAT may time out and a preserved incumbent
is not its returned optimal solution. The HiGHS finite-column master can be
optimal without solving the entire PSP. The ALNS-style baseline is a
standalone original implementation, not an academic-paper reproduction.
Benchmark outputs at different budgets or under older portfolio protocols
must not be pooled.

The scripts have no paid API or commercial solver dependency. The source
license is MIT, upstream datasets/code retain original licenses. Avoid
publishing customer data or implying deployment at the Port of
Antwerp-Bruges.

## Optional next experiments (not blockers)

A faithful published maritime ALNS/decomposition comparison on an
equivalent exact formulation; larger pre-registered unseen PSP cohorts;
representative operational delays and equipment outages; new separate
problem tracks for tidal berth or tug-routing formulations.

**Handoff rule:** the existing results and checksums are frozen. Any new
algorithm, modified parameters, or different input/compute should produce
a **new** experiment and report, not overwrite the historical evidence.
