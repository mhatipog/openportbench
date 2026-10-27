"""Common, instance-clustered, reproducible tournament summary. """
from collections import defaultdict
import statistics

def summary(doc):
    by_method=defaultdict(list)
    by_instance=defaultdict(dict)
    for row in doc["rows"]:
        for method, r in row["methods"].items():
            if row["source_status"]!="FEASIBLE":
                continue
            delta=(row["source_objective"]-r["objective"]) / row["source_objective"] *100
            by_method[method].append((row["file"],row["seed"],r,delta))
            by_instance[row["file"]].setdefault(method,[]).append(delta)
    table={}
    for method, records in sorted(by_method.items()):
        instance_averages=[
            statistics.mean(v[method]) for v in by_instance.values()
            if method in v
        ]
        table[method]={
            "observations":len(records),
            "distinct_instances":len(instance_averages),
            "mean_improvement_pct_instance_weighted":(
                statistics.mean(instance_averages) if instance_averages else None),
            "mean_observed_wall_s":statistics.mean(v[2]["wall_s"] for v in records),
            "hard_timeout_count":sum(v[2]["status"]=="TIMEOUT" for v in records),
            "invalid_count":sum(not v[2]["valid"] for v in records),
            "mean_final_objective_by_size":{},
        }
        for size in sorted({int(v[0].split("_")[0]) for v in records}):
            matching=[v[2]["objective"] for v in records if int(v[0].split("_")[0])==size]
            table[method]["mean_final_objective_by_size"][str(size)]=statistics.mean(matching)
    wins={}
    for row in doc["rows"]:
        if row["source_status"] != "FEASIBLE":
            continue  # A failed common incumbent makes all matched ranks invalid.
        eligible={k:v["objective"] for k,v in row["methods"].items() if v["valid"]
                  and v["status"]=="FEASIBLE"}
        if not eligible:
            continue
        minimum=min(eligible.values())
        for k,objective in eligible.items():
            if objective<=minimum+1e-6:
                wins[k]=wins.get(k,0)+1
    return {
        "metrics":table,"winner_counts_including_ties":wins,
        "total_records":len(doc["rows"]),
        "source_failed":sum(r["source_status"]!="FEASIBLE" for r in doc["rows"]),
        "caution":"Repeated seeds on one instance are correlated. Strict deadline includes"
                  " worker startup, solver and serialization. Different methods"
                  " may consume different CPU despite equal wall deadline. Objectives"
                  " are comparable only within the same input. Restricted HiGHS"
                  " MASTER_OPTIMAL does not certify full PSP optimality.",
    }


