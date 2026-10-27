from openportbench.matrix_summary import summary


def test_summary_instances_not_seeds():
    doc={"rows":[]}
    for file,n,x,y in (("20_1_1_T12_001.txt",20,60.,80.),
                       ("20_1_1_T12_002.txt",20,80.,60.)):
        for seed in (1,2):
            doc["rows"].append({
                "file":file,"seed":seed,"source_status":"FEASIBLE",
                "source_objective":100.,
                "methods":{
                  "warm-cp-sat":{"objective":x,"wall_s":1,"status":"FEASIBLE","valid":True},
                  "restricted-highs-milp":{"objective":y,"wall_s":1,"status":"FEASIBLE","valid":True},
                },
            })
    s=summary(doc)
    assert s["total_records"]==4
    assert s["metrics"]["warm-cp-sat"]["distinct_instances"]==2
    assert s["metrics"]["warm-cp-sat"]["mean_improvement_pct_instance_weighted"]==30
    assert s["winner_counts_including_ties"]=={"warm-cp-sat":2,"restricted-highs-milp":2}


def test_source_failed_kept_but_excluded_from_stats():
    doc={"rows":[{"file":"20_1.txt","seed":1,"source_status":"TIMEOUT",
                   "source_objective":None,"methods":{
                   "warm-cp-sat":{"objective":20.,"wall_s":1,
                                  "status":"FEASIBLE","valid":True}}}]}
    s=summary(doc)
    assert s["source_failed"]==1
    assert s["metrics"]=={}
