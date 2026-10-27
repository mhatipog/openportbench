"""Independent, classical ALNS-style heuristic for the integrated LACE PSP.

Adaptive destroy/repair with feasibility-preserving insertion, regret-based
ordering, randomized neighborhoods and simulated-annealing acceptance.
No CP-SAT or MILP optimizer is called. This is *not* a reproduction of any
specific published maritime ALNS manuscript and has no claimed bound.
Uses the same independently validated full-vessel candidate patterns as
the restricted-master MILP so search strategy can be compared directly.
"""
from __future__ import annotations

import math
import random
import time

from .pattern_milp import columns_for_vessel
from .psp import empty_solution, evaluate


def _decode(a, columns, assigned):
    result=empty_solution(a)
    for i,idx in enumerate(assigned):
        description=columns[i][idx][0]
        if description is None:
            continue
        berth,t_berth,t_in,t_out,inbound,outbound=description
        result["vessel_assignments"][i]=[berth,t_berth]
        result["inbound_tugboats"][i]=[[k,t_in] for k in inbound]
        result["outbound_tugboats"][i]=[[k,t_out] for k in outbound]
    return result


def _roulette(weights: dict, rng: random.Random) -> str:
    total=sum(weights.values())
    r=rng.random()*total
    for name,w in weights.items():
        r-=w
        if r<=0:
            return name
    return next(reversed(weights))


def alns_psp(instance: dict, incumbent: dict, *, seconds: float=3.,
             seed: int=1, max_columns: int=24, max_steps: int=1200,
             min_ruin: int=4, max_ruin: int=14) -> dict:
    """Anytime, wall-aware heuristic. External process deadline is authoritative."""
    if seconds<=0 or max_steps<1 or min_ruin<1 or max_ruin<min_ruin:
        raise ValueError("Invalid budget or ALNS parameters")
    started=time.perf_counter()
    initial=evaluate(instance,incumbent)
    n=instance["vessel_num"]
    if n<=0:
        raise ValueError("PSP needs at least one vessel")
    rng=random.Random(seed)
    columns=[]
    occupancy=[]
    for i in range(n):
        options=columns_for_vessel(instance,i,incumbent,max_columns=max_columns)
        # Intrinsic tug overlap invalidates a single-vessel pattern; exclude it
        # before checking conflict with other vessels.
        options=[p for p in options if len(p[1])==len(set(p[1]))]
        if not options:
            raise AssertionError("Verified incumbent pattern disappeared")
        columns.append(options)
        occupancy.append([frozenset(p[1]) for p in options])
    best=[0]*n
    best_objective=sum(columns[i][0][2] for i in range(n))
    if abs(initial-best_objective)>1e-5:
        raise AssertionError("Pattern cost disagrees with independent PSP objective")
    current=best[:]
    current_cost=initial
    destroy_weights={"random":1.,"time-near":1.,"expensive":1.}
    repair_weights={"priority":1.,"regret":1.}
    temperature=max(1.,abs(initial)*.005)
    improvements=0
    accepted=0
    steps=0
    for iteration in range(max_steps):
        if time.perf_counter()-started >= seconds-.012:
            break
        steps+=1
        d=_roulette(destroy_weights,rng)
        repair=_roulette(repair_weights,rng)
        k=rng.randint(min(n,min_ruin), min(n,max_ruin))
        if d=="random":
            removed=set(rng.sample(range(n),k))
        elif d=="time-near":
            anchor=rng.randrange(n)
            eta=instance["vessel_etas"][anchor]
            removed=set(sorted(range(n),key=lambda i:(
                abs(instance["vessel_etas"][i]-eta),i!=anchor,i))[:k])
        else:
            ranks=sorted(range(n),key=lambda i:(
                -(columns[i][current[i]][2]-min(p[2] for p in columns[i])),
                rng.random()))
            removed=set(ranks[:k])
        tentative=current[:]
        busy=set()
        for i in range(n):
            if i not in removed:
                busy.update(occupancy[i][tentative[i]])
        pending=set(removed)
        feasible=True
        while pending:
            # Recompute admissible patterns after each insertion; regret
            # depends on resource occupancy and cannot be cached globally.
            choices={}
            for i in pending:
                options=[j for j,p in enumerate(columns[i])
                         if not occupancy[i][j].intersection(busy)]
                if not options:
                    feasible=False
                    break
                options.sort(key=lambda j:(columns[i][j][2],j))
                choices[i]=options
            if not feasible:
                break
            if repair=="priority":
                i=max(pending,key=lambda i:(instance["vessel_priority_weights"][i],-i))
            else:
                i=max(pending,key=lambda i:(
                    (columns[i][choices[i][1]][2]-columns[i][choices[i][0]][2])
                    if len(choices[i])>1 else 1e8,
                    instance["vessel_priority_weights"][i],-i))
            # Mostly cheapest valid insertion, with occasional randomized
            # second-best move to escape cycling in deterministic repair.
            pool=choices[i]
            selected=pool[1] if len(pool)>1 and rng.random()<.08 else pool[0]
            tentative[i]=selected
            busy.update(occupancy[i][selected])
            pending.remove(i)
        if not feasible:
            continue
        candidate_cost=sum(columns[i][tentative[i]][2] for i in range(n))
        # Best-improvement candidates are validated against the original full
        # checker before being reported, never merely trusted to column sums.
        better=candidate_cost<best_objective-1e-6
        if better:
            candidate=_decode(instance,columns,tentative)
            checked=evaluate(instance,candidate)
            if abs(checked-candidate_cost)>1e-5:
                raise AssertionError("ALNS candidate and independent objective differ")
            best=tentative[:]
            best_objective=checked
            improvements+=1
        accept=(candidate_cost<=current_cost+1e-9 or
                rng.random()<math.exp(-min(700.,max(0.,candidate_cost-current_cost)/temperature)))
        if accept:
            current=tentative
            current_cost=candidate_cost
            accepted+=1
        destroy_weights[d]=max(.15,.99*destroy_weights[d]+(.5 if better else .005))
        repair_weights[repair]=max(.15,.99*repair_weights[repair]+(.5 if better else .005))
        temperature=max(.01,temperature*.996)
    returned=_decode(instance,columns,best)
    score=evaluate(instance,returned)
    if score>initial+1e-6:
        raise AssertionError("ALNS may not deteriorate verified incumbent")
    return {
        "status":"HEURISTIC_FEASIBLE",
        "solution":returned,"objective":score,
        "initial_objective":initial,
        "steps":steps,"accepted_steps":accepted,"improvements":improvements,
        "column_count":sum(len(x) for x in columns),
        "wall_s":time.perf_counter()-started,
        "algorithm":"adaptive destroy/repair, feasible patterns and SA acceptance",
    }
