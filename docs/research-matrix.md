# Research comparison and applicability audit — 27 October 2026

This is an evidence map, **not one leaderboard**. Scores or published optimality
bounds must not be compared across distinct objectives or feasible sets.
Status vocabulary: reproduced; source inspected; literature only; unverified.

## Maritime sources

| Source | Mathematical model and constraints | Data / published comparison | Code / license verified | PSP-equivalent? | Evidence and next step |
| --- | --- | --- | --- | --- | --- |
| [PJ-NTU/LACE](https://github.com/PJ-NTU/LACE), commit d772b746 | Integrated discrete PSP: berths, ETA/time windows, HP-qualified tug teams, inbound/outbound services and preparation; plus three different routing families | 128 generated train + 100 generated test each; ten complementary evolved heuristics | Python MIT, original evaluators and instances | **Yes within original problem**, not across LACE problem families | 40/40 portfolio smoke runs on four train instances; PSP independently rechecked. Held-out evaluator added. |
| [TU Delft OpenTNSim](https://github.com/TUDelft-CITG/OpenTNSim) | Vessel traffic and network-based discrete-event simulation | Movement/navigation scenarios; no common PSP objective | Public Python/notebooks; MIT | No | Model arrival/movement disturbance scenarios separately |
| [TU Delft OpenCLSim](https://github.com/TUDelft-CITG/OpenCLSim) | Infrastructure, operation and logistics event simulation | Scenario and strategy analysis | Public Python/notebooks; MIT | No | Simulate controlled replanning experiments, no solver leaderboard |
| [PySeidon](https://github.com/pyseidon-sim/pyseidon) | Simulates vessel arrivals, tug/pilot/berth agents, outages and policy changes | Rotterdam proof-of-concept, Skaisgiris et al. ICCMS 2021 | Python source; repository license metadata not independently verified | No | Scenario generation only after its license and inputs are audited |
| [CUT DICL cibapqcap](https://github.com/cut-dicl/cibapqcap) | Multi-quay berth + quay-crane allocation | MATLAB CSA, GA, PSO, MILP; random/real-labeled dataset folders | Public MATLAB, Apache-2.0 | No | Inspect reproducibility and data provenance; use Octave only if matching arithmetic/contracts |
| [MATHPROG ORlib BAP](https://github.com/andreas-ernst/Mathprog-ORlib/blob/master/info/readmeBAP.md) | Berth allocation under tides, geometry and arrival/processing times | Ernst et al. J Scheduling 2017; repository states 900 instances, 400 CSV-converted | Public data and OPL model; redistribution license unclear | No | Independent BAP validator and tidal model, distinct track |
| [QUT channel-restricted BAP](https://doi.org/10.4225/09/5B306F6511D7C) | Berth allocation and bidirectional narrow channel/no-wait flow-shop, tidal releases | Corry & Bierwirth Transp Science 2019, published workbooks including per-instance solution values/gaps | Published dataset open with attribution, code availability not verified | No | Excellent independent verification track with published reference values |
| [DTU/Pacino et al.](https://doi.org/10.1016/j.tre.2015.06.008) | Joint berth+crane assignment; set partitioning, discretization, crane counts | DTU research 2015; published model/bounds, publicly downloadable dataset not confirmed | Paper/manuscript, reuse rights separate | No | Obtain comparable datasets and legitimate redistribution permission before adapter |
| [DTU/Iris et al.](https://doi.org/10.1016/j.tre.2017.06.013) | Continuous berth sections, crane productivity, berth deviation, ALNS and bound improvements | DTU 2017 larger benchmark reported | Paper publicly indexed, runnable code not verified | No | Matheuristic architecture candidate, not apples-to-apples score |
| [Maritime laycan/berth/crane datasets](https://doi.org/10.17632/3cts6wkn4f.1) | Tide tables, laycan, berth/crane allocation | Bouzekri et al. 2020 published Excel instances+results | CC BY 4.0 dataset, no solver confirmed | No | Reproduce in separate berth+crane track |
| [Tug–berth–quay crane ALNS](https://doi.org/10.3390/jmse12091541) | Tug teams, arrival uncertainty, handling cranes, crane noncrossing | Chu et al. 2024, MILP and 5 destroy/repair operators | Paper public, runnable source not verified | No | Candidate for mathematically mapped LNS neighborhoods |
| [Integrated pilot/tug routing](https://doi.org/10.1016/j.cor.2026.107395) | Pilot/pilot-boat/tug synchronized routing over waypoints | 2026 set partitioning / ALNS-LP research | Public abstract, executable source not verified | No | Decomposition inspiration with faithful constraint matching |
| [Integrated two-channel tug scheduling](https://doi.org/10.3389/fmars.2026.1939678) | Dual one-way channel, heterogeneous tug services, fuel/wait tradeoffs | 2026 NSGA-II-AAMNS | Public article, source unverified | No | Separate multiobjective flow & schedule benchmark |

The distinction between a folder marked RealData and independently validated
port-operations records is important. OpenPortBench does **not** claim to have
Antwerp or Rotterdam operational logs.

## OpenAI mathematical results: reduction gate

Upstream: [openai/math](https://github.com/openai/math), repository Apache-2.0.
It includes preprints and formalizations, not maritime engineering tools.
[History](https://github.com/openai/math/blob/main/history.md) reports
three **unrelated** withdrawals and 14 revised manuscripts on 7 October 2026.
No published theorem may be translated into software guarantees without
checking its exact assumptions and revision. The 110/124/125 docs were read
at the public repository; we have not independently verified their proofs.

| Result | Actual assumptions / claim | Valid maritime subproblem? | Action taken or gate |
| --- | --- | --- | --- |
| [#110 online k-server](https://github.com/openai/math/blob/main/lean/docs/110.md) | Randomized competitive movement O(log²(k+1)), oblivious request sequences, arbitrary metrics; uniform rational-bit implementation but potentially large additive constant | Only identical mobile resources, one service at a time, movement-only requests, no cooperative horsepower, time windows or crew restrictions | Implement classical nearest/randomized/preview + exact offline DP on **separate synthetic metric**. These are NOT the #110 algorithm |
| [#124 three-machine scheduling](https://github.com/openai/math/blob/main/lean/docs/124.md) | Unit-time nonpreemptive precedence jobs on three identical parallel machines, exact makespan polytime | Only a strict toy subcase of 3 identical resources; PSP tasks and composite tug teams violate hypotheses | Reject applying it to PSP; faithful reproduction deferred |
| [#125 metric k-median](https://github.com/openai/math/blob/main/lean/docs/125.md) | Specified candidate centers, finite rational metric, no capacity; optimal polynomial-time approximation factor 1+2/e+epsilon under fixed epsilon | Resource-base placement with additive travel distances **if** no service-time interaction or capacity | Implement and benchmark classical greedy, 1-swap and small exact enumeration; NOT a reproduction of the new approximation |
| [#120 near-linear matching](https://github.com/openai/math/blob/main/overview.tex) | Randomized exact maximum-cardinality general-graph matching in (n+m)^(1+o(1)), success ≥2/3 | One-to-one compatible task-resource pairings only, not team tug assignment or dynamic routing | Prefer existing optimized conventional matching first; no convincing direct algorithm transplant yet |
| [#118 bin packing gap](https://github.com/openai/math/blob/main/lean/docs/118.md) | Unbounded **additive** configuration-LP gap, unrelated to CP-SAT lower bounds by itself | Capacity-packing abstractions only | Do not generalize gap to PSP; validate every reported best bound against integer objectives |

## Execution status

* PSP training smoke at commit 24637ff passed; one 20-vessel example CP-SAT
  objective 12736.2769343 and equal bound, independently rechecked vs original.
* Larger held-out benchmark must be kept disjoint from heuristic tuning.
* Online-dispatch and k-median prototypes use reproducible **synthetic**
  metrics, explicit exact small-instance oracles and no operational claims.
* Full no-fee reproducibility requires recorded seeds, source commits, input
  SHA256, package versions, wall/CPU time, and memory limits. In-progress
  experiments may fail; failures are part of the scientific record.
