---
name: Algorithm reproduction / benchmark request
about: Propose a rigorously comparable optimization algorithm or problem track
title: "Benchmark method: "
labels: ["research"]
---

### Scientific source
Paper title, DOI, publication date, implementation repository, exact commit and license:

### Which mathematical problem?
- [ ] Identical integrated LACE PSP formulation and objective
- [ ] Other mathematical formulation (specify full differences and create separate track)

### Claimed algorithm and available implementation
Specify the precise algorithm, not merely a generic family (e.g. ALNS):

### Validation plan
Independent feasibility, objective consistency, tiny exact oracle,
and known edge cases:

### Experimental protocol
Dataset source and split, full input hashes, strict time budget(s), seeds,
CPU/platform, comparator methods and baseline fairness:

### Expected benefit and risk
What could this benchmark teach, even if the algorithm loses?

### Submission requirements
- [ ] No customer/private port data or secrets
- [ ] Redistribution or reimplementation license checked
- [ ] No test-set tuning or premature "state of the art" claim
