# Reproducible multi-budget performance profiles

This workflow compares **four** algorithm families over original LACE test
instances with **3- and 10-second strict hard refinement deadlines**.
For every file/seed pair, it obtains **one and the same independently verified
source solution** once, then makes every solver optimize against it under both
budgets. This isolates the effect of runtime budget from source-schedule
variation. Source construction itself gets a separately accounted **2 s**
deadline. Methods cannot benefit from results returned after their deadline.

The LACE revision, source commit, unmodified file SHA256, platform, Python
package versions, method configurations and per-trial failures are recorded.

Configuration frozen on 27 October 2026 before this sweep:

- PSP **test** inputs indexed `012`; 80, 100, 150, 250, 300, 500 vessels.
- **Two random seeds** per input; 12 independent-run observations, six
  distinct original synthetic instances.
- Four fixed strategies: warm full CP-SAT, CP-SAT fix-and-optimize LNS,
  restricted pattern HiGHS MILP, and adaptive ruin/recreate.
- Complete original four-term PSP objective and feasibility, validated
  against both independent and original LACE checkers.
- No method-specific retuning across deadlines. Hard timeouts remain
  recorded as failures with common feasible incumbent fallback.
- A failed source-incumbent construction is preserved as negative evidence
  but excluded from matched improvements and rankings.

Source SHA: `d772b74690075f641be8077e69748ec482e9febf`.

Small-case configurations (`_004`–`_011`) were exposed earlier and must
not be rebranded as untouched held-out instances. `_012` is new to this
study at registration, but all results will be considered exploratory
once inspected. With only six distinct inputs, bootstrap intervals are
descriptive and likely wide; they are **not** publication-grade guarantees.

The experiment does not reproduce an external academic ALNS paper or
OpenAI theorem. Those remain separate planned comparator tracks.
