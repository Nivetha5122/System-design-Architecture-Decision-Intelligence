"""Requirement-derived Digital Twin simulation for ARCHDS.

The twin is not a generic dashboard: its topology, components, dependency
propagation and affected requirements are derived from the selected candidate
returned by the architecture pipeline.
"""
from typing import Any, Dict, List
import math

SCENARIO_LIBRARY = {
    "baseline": {"label":"Baseline runtime", "traffic":1.0, "latency_ms":1.0, "failure_rate":0.0, "db_load":1.0},
    "traffic_10x": {"label":"10× traffic surge", "traffic":10.0, "latency_ms":1.7, "failure_rate":0.02, "db_load":8.5},
    "regional_failure": {"label":"Regional failure", "traffic":1.0, "latency_ms":2.1, "failure_rate":0.35, "db_load":1.2},
    "database_degraded": {"label":"Database degradation", "traffic":1.0, "latency_ms":2.6, "failure_rate":0.12, "db_load":9.2},
    "latency_injection": {"label":"Injected network latency", "traffic":1.0, "latency_ms":3.2, "failure_rate":0.04, "db_load":1.1},
    "cache_loss": {"label":"Cache loss", "traffic":1.0, "latency_ms":1.9, "failure_rate":0.08, "db_load":5.5},
    "security_event": {"label":"Security control stress", "traffic":1.0, "latency_ms":1.25, "failure_rate":0.05, "db_load":1.0},
}


def _norm(x: str) -> str:
    return str(x or "").lower()


def _node_type(name: str) -> str:
    n=_norm(name)
    if any(k in n for k in ["database","postgres","mysql","mongo","sql server","oracle","dynamodb","cassandra","store","storage","warehouse"]): return "data"
    if any(k in n for k in ["cache","redis"]): return "cache"
    if any(k in n for k in ["queue","kafka","broker","event"]): return "messaging"
    if any(k in n for k in ["gateway","load balancer","proxy","identity","auth","security"]): return "edge"
    if any(k in n for k in ["client","web","mobile","portal","app"]): return "experience"
    return "service"


def simulate(candidate: Dict[str, Any], requirement_profile: Dict[str, Any], scenario_key: str = "baseline", custom: str = "") -> Dict[str, Any]:
    base=SCENARIO_LIBRARY.get(scenario_key, SCENARIO_LIBRARY["baseline"]).copy()
    if custom.strip():
        base["label"]=custom.strip()
        text=_norm(custom)
        if any(k in text for k in ["traffic","users","load"]): base["traffic"]=10.0
        if any(k in text for k in ["latency","slow","delay"]): base["latency_ms"]=2.8
        if any(k in text for k in ["database","db"]): base["db_load"]=8.0
        if any(k in text for k in ["failure","outage","down"]): base["failure_rate"]=.30

    components=list(dict.fromkeys(candidate.get("components",[])))
    relations=[]
    for rel in candidate.get("relations",[]):
        if "->" in rel:
            a,b=[x.strip() for x in rel.split("->",1)]
            if a in components and b in components: relations.append((a,b))
    indegree={c:0 for c in components}; adjacency={c:[] for c in components}
    for a,b in relations:
        adjacency[a].append(b); indegree[b]+=1

    scores=candidate.get("scores",{}) or {}
    resilience=float(scores.get("reliability",70)); availability=float(scores.get("availability",75)); performance=float(scores.get("performance",75))
    reqs=requirement_profile.get("requirement_records",[]) or []
    req_by_component=candidate.get("component_requirements",{}) or {}

    states=[]
    affected=set()
    for c in components:
        typ=_node_type(c)
        load=base["traffic"]
        if typ=="data": load*=base["db_load"]
        elif typ=="cache": load*=max(1.0,base["traffic"]*.55)
        elif typ=="messaging": load*=max(1.0,base["traffic"]*.7)
        elif typ=="edge": load*=max(1.0,base["traffic"]*.85)
        health=max(0.0,100.0-base["failure_rate"]*100.0-(load-1)*2.1)
        if typ=="cache" and scenario_key=="cache_loss": health-=22
        if typ=="data" and scenario_key=="database_degraded": health-=30
        health=max(0,min(100,health))
        state="HEALTHY" if health>=82 else "DEGRADED" if health>=55 else "AT RISK"
        if state!="HEALTHY":
            affected.update(req_by_component.get(c,[]))
        states.append({"id":c,"type":typ,"health":round(health,1),"state":state,"load":round(load,2),"dependencies_in":indegree.get(c,0),"dependencies_out":len(adjacency.get(c,[])),"requirements":req_by_component.get(c,[])[:6]})

    # Propagate severe failures along the actual dependency graph.
    if base["failure_rate"]>=.25 or base["db_load"]>=8:
        frontier=[s["id"] for s in states if s["state"]=="AT RISK"]
        seen=set(frontier)
        for _ in range(3):
            nxt=[]
            for a in frontier:
                for b in adjacency.get(a,[]):
                    if b not in seen:
                        seen.add(b); nxt.append(b)
            frontier=nxt
        for s in states:
            if s["id"] in seen and s["state"]=="HEALTHY":
                s["state"]="DEGRADED"; s["health"]=round(max(35,s["health"]-18),1); affected.update(s["requirements"])

    degraded=sum(s["state"]=="DEGRADED" for s in states); risk=sum(s["state"]=="AT RISK" for s in states)
    coverage=len(set(affected))
    latency=round(110*base["latency_ms"]*(1+degraded*.035+risk*.08),1)
    availability_out=max(0,round(availability-base["failure_rate"]*18-risk*1.4-degraded*.25,2))
    throughput=round(max(5,100/(1+base["traffic"]*.055+degraded*.04+risk*.1)),1)
    twin_score=round(max(0,min(100,performance*.35+resilience*.35+availability_out*.2+(100-min(100,latency/4))*.1)),1)

    events=[]
    if base["traffic"]>1: events.append({"time":"T+00:10","event":"Workload surge injected","impact":f"{base['traffic']}× traffic pressure applied to the generated topology."})
    if base["failure_rate"]>0: events.append({"time":"T+00:25","event":"Failure/impairment injected","impact":f"Estimated failure pressure {base['failure_rate']*100:.0f}% on vulnerable components."})
    if degraded or risk: events.append({"time":"T+00:40","event":"Dependency propagation observed","impact":f"{degraded+risk} component(s) moved out of healthy state through the actual dependency graph."})
    events.append({"time":"T+01:00","event":"Recovery assessment","impact":"Resilience and requirement impact recalculated from candidate evidence."})

    recommendations=[]
    if risk: recommendations.append("Add or strengthen isolation, health checks and recovery around the affected component path.")
    if degraded: recommendations.append("Review capacity or redundancy for degraded components before accepting the scenario.")
    if base["traffic"]>1: recommendations.append("Validate horizontal scaling and queue/backpressure behavior against the requested workload.")
    if base["db_load"]>5: recommendations.append("Validate database partitioning, replicas, caching or workload separation against the generated data path.")
    if base["latency_ms"]>2: recommendations.append("Measure end-to-end latency budgets at the generated edge-to-service-to-data path.")
    if not recommendations: recommendations.append("No material degradation detected under this scenario; retain the current architecture and monitor the highlighted metrics.")

    return {
        "scenario_key":scenario_key,"scenario":base,"candidate":candidate.get("name"),"pattern_key":candidate.get("pattern_key"),
        "topology":{"components":components,"relations":[{"from":a,"to":b} for a,b in relations]},
        "nodes":states,"events":events,
        "metrics":{"twin_score":twin_score,"latency_ms":latency,"availability_pct":availability_out,"throughput_index":throughput,"degraded_components":degraded,"at_risk_components":risk,"affected_requirements":coverage},
        "affected_requirements":sorted(affected),"recommendations":recommendations,
        "requirement_drivers":requirement_profile.get("drivers",[])[:12],
    }
