
"""Deterministic specialist agents used by ARCHDS.

Each specialist performs an independently inspectable analysis and returns evidence.
The deterministic implementation is deliberately provider-neutral: an optional LLM
may enrich inputs, but it is never trusted as the source of truth.
"""
from __future__ import annotations
import re, hashlib, math
from collections import defaultdict
from typing import Any

ATTRS = ["performance","scalability","security","reliability","availability",
         "maintainability","extensibility","cost","complexity","observability",
         "deployment_complexity","operational_risk"]

def _all_reqs(profile):
    rows=[]
    for i,r in enumerate(profile.functional_requirements,1):
        rows.append((f"R{i}",r,"FUNCTIONAL"))
    off=len(profile.functional_requirements)
    for j,r in enumerate(profile.non_functional_requirements,1):
        rows.append((f"R{off+j}",r,"NON_FUNCTIONAL"))
    return rows

def requirement_records(profile):
    rows=[]
    for rid,text,typ in _all_reqs(profile):
        low=text.lower()
        priority="HIGH" if any(k in low for k in ["must","strict","99.99","10 million","sensitive","audit"]) else ("MEDIUM" if typ=="NON_FUNCTIONAL" else "MEDIUM")
        architectural_relevance=min(100, 55 + 10*sum(k in low for k in ["scale","security","latency","availability","audit","real-time","cost","reliable"]))
        conf=max(55, min(98, round(100-profile.ambiguity*0.25 - (10 if len(text.split())<4 else 0))))
        rows.append({"id":rid,"type":typ,"description":text,"priority":priority,"source_text":text,
                     "confidence":conf,"ambiguity":profile.ambiguity,"architectural_relevance":architectural_relevance,
                     "dependencies":[],"conflicts":[]})
    return rows

def clarification(profile):
    critical=[]
    for q in profile.clarification_questions:
        if any(k in q.lower() for k in ["concurrent","requests per second","availability/sla","sensitive","primary business"]):
            critical.append(q)
    return {"questions":critical, "decision":"PROCEED_WITH_ASSUMPTIONS" if critical else "READY",
            "reason":"Only questions with material architectural impact are surfaced."}

def drivers(profile):
    mapping=[]
    for rid,text,typ in _all_reqs(profile):
        low=text.lower(); ds=[]
        rules=[
            (["million","traffic","concurrent","throughput","scale"],"Scalable capacity"),
            (["real-time","realtime","latency","milliseconds","live"],"Low-latency responsiveness"),
            (["security","secure","privacy","encrypt","pci","hipaa","sensitive","auth"],"Security isolation"),
            (["audit","ledger","compliance","trace","history"],"Auditability"),
            (["availability","uptime","failover","99.9","99.99","recovery"],"High availability"),
            (["cost","budget","affordable","cheap"],"Cost efficiency"),
            (["maintain","test","extens"],"Maintainability"),
            (["iot","sensor","telemetry","device","stream"],"Event ingestion"),
        ]
        for words,d in rules:
            if any(w in low for w in words) and d not in ds: ds.append(d)
        if not ds: ds=["Business capability isolation"]
        mapping.append({"requirement_id":rid,"drivers":ds})
    unique=[]
    for m in mapping:
        for d in m["drivers"]:
            if d not in unique: unique.append(d)
    return {"drivers":unique[:20],"mapping":mapping}

def knowledge(profile,retrieved):
    return [{"pattern":x.get("title"),"relevance":round(50 + 8*sum(t in str(x).lower() for t in profile.tags),1),
             "matched_drivers":profile.drivers[:5],"source":x.get("text","")} for x in retrieved]

def _findings_for_candidate(c, profile):
    text=(c.get("name","")+" "+" ".join(c.get("components",[]))+" "+" ".join(c.get("communication_patterns",[]))).lower()
    tags=set(profile.tags); f=[]
    def add(sev,title,desc,reqs):
        f.append({"severity":sev,"title":title,"description":desc,"affected_requirements":reqs,"evidence":"deterministic reviewer rule"})
    ids=[rid for rid,_,_ in _all_reqs(profile)]
    if "security" in tags and not any(x in text for x in ["security","identity","secrets"]):
        add("HIGH","Security boundary missing","Security-sensitive requirements have no explicit trust or secrets boundary.",ids)
    if "scalability" in tags and c["pattern_key"] in {"layered","modular_monolith","clean_hexagonal"}:
        add("HIGH","Coarse scaling boundary","Projected scale is high but the candidate has one coarse deployment unit.",ids)
    if "realtime" in tags and not any(x in text for x in ["realtime","websocket","sse","event"]):
        add("HIGH","Real-time path not explicit","Real-time requirements are not represented by an explicit low-latency delivery path.",ids)
    if "availability" in tags and "multi-zone" not in text and "disaster" not in text:
        add("MEDIUM","Failure-domain strategy","Availability requirements require an explicit failure-domain and recovery strategy.",ids)
    if "auditability" in tags and "audit" not in text and "ledger" not in text:
        add("HIGH","Audit evidence path missing","Audit-sensitive requirements lack an explicit durable audit/ledger component.",ids)
    if "cost_sensitive" in tags and c["pattern_key"] in {"microservices","event_driven","cqrs"}:
        add("MEDIUM","Operational cost pressure","Distributed topology adds operational overhead under a cost-sensitive constraint.",ids)
    if c["pattern_key"] in {"microservices","event_driven","cqrs"} and "observability" not in text:
        add("MEDIUM","Observability dependency","Distributed communication requires correlated logs, metrics and traces.",ids)
    return f

def security_review(c,profile):
    fs=_findings_for_candidate(c,profile)
    return [f for f in fs if any(k in f["title"].lower()+f["description"].lower() for k in ["security","audit","secrets","trust"])]

def scalability_review(c,profile):
    fs=_findings_for_candidate(c,profile)
    return [f for f in fs if any(k in f["title"].lower() for k in ["scaling","scale","traffic"])]

def performance_review(c,profile):
    fs=_findings_for_candidate(c,profile)
    return [f for f in fs if any(k in f["title"].lower() for k in ["real-time","latency"])]

def reliability_review(c,profile):
    fs=_findings_for_candidate(c,profile)
    return [f for f in fs if any(k in f["title"].lower() for k in ["failure","availability","recovery"])]

def cost_review(c,profile):
    fs=_findings_for_candidate(c,profile)
    return [f for f in fs if any(k in f["title"].lower() for k in ["cost","operational"])]

def maintainability_review(c,profile):
    findings=[]
    if c["pattern_key"] in {"microservices","event_driven","cqrs"} and profile.priority_weights.get("maintainability",0)>15:
        findings.append({"severity":"MEDIUM","title":"Operational complexity","description":"The distributed topology increases deployment and debugging surface area relative to simpler candidates.","affected_requirements":[],"evidence":"maintainability objective"})
    return findings

def consistency_review(c,profile):
    issues=[]
    comps=set(c.get("components",[]))
    for rel in c.get("relations",[]):
        parts=[x.strip() for x in rel.split("->")]
        if len(parts)==2 and (parts[0] not in comps or parts[1] not in comps):
            issues.append(f"Relation references missing component: {rel}")
    if not c.get("components"): issues.append("Candidate has no components")
    return {"verified":not issues,"issues":issues}

def evaluate_constraints(c,profile):
    hard=[]
    text=" ".join(c.get("components",[])).lower()
    for rid,r,typ in _all_reqs(profile):
        low=r.lower()
        if "strict security" in low or ("sensitive" in low and "security" in low):
            if not any(k in text for k in ["security","identity"]): hard.append(rid)
        if "audit" in low and not any(k in text for k in ["audit","ledger"]): hard.append(rid)
    return list(dict.fromkeys(hard))

def judge(candidates, profile, pareto):
    # Human-auditable decision policy: hard-constraint violations first, then
    # critical findings, then Pareto membership, then requirement coverage, then score.
    eligible=[]
    for c in candidates:
        high=sum(1 for f in c.get("critique_findings",[]) if f.get("severity")=="HIGH")
        hard=len(c.get("hard_constraint_violations",[]))
        cov=sum(bool(x) for x in c.get("requirement_coverage",{}).values())
        pareto_bonus=1 if c.get("is_pareto_optimal") else 0
        key=(hard,high,-pareto_bonus,-cov,-float(c["scores"]["weighted_total"]))
        eligible.append((key,c))
    chosen=min(eligible,key=lambda x:x[0])[1]
    rationale=[]
    for rid,txt,_ in _all_reqs(profile):
        if chosen.get("requirement_coverage",{}).get(rid):
            rationale.append(f"{rid} is covered by {', '.join(chosen.get('requirement_mappings',{}).get(rid,[])[:3])}.")
    return chosen, {"policy":"hard constraints → critical findings → Pareto status → requirement coverage → weighted objectives",
                    "rationale":rationale[:20],
                    "tradeoffs":chosen.get("disadvantages",[])[:6]}

def confidence(profile,candidates,chosen, reviewer_disagreement):
    coverage=sum(chosen.get("requirement_coverage",{}).values())/max(1,len(chosen.get("requirement_coverage",{})))
    high=sum(1 for f in chosen.get("critique_findings",[]) if f.get("severity")=="HIGH")
    separation=sorted([c["scores"]["weighted_total"] for c in candidates],reverse=True)
    sep=(separation[0]-separation[1]) if len(separation)>1 else 0
    value=0.30*profile.completeness+0.20*profile.consistency+0.25*coverage*100+0.15*max(0,100-reviewer_disagreement)+0.10*min(100,sep*10)
    value-=min(20,high*6)
    reasons=[]
    if profile.completeness<80: reasons.append("Requirement completeness is below 80%.")
    if high: reasons.append(f"{high} unresolved high-severity finding(s) remain.")
    if reviewer_disagreement>20: reasons.append("Specialist reviewers disagree materially.")
    if not reasons: reasons.append("Coverage, reviewer agreement and candidate separation support the decision.")
    return round(max(0,min(99,value)),1), reasons

def diversity(candidates):
    signatures=[]
    for c in candidates:
        sig="|".join([c["pattern_key"],",".join(c.get("communication_patterns",[])),c.get("deployment_model",{}).get("topology",""),",".join(c.get("data_stores",[]))])
        signatures.append(sig)
    unique=len(set(signatures))
    return {"unique_signatures":unique,"candidate_count":len(candidates),
            "diversity_percent":round(unique/max(1,len(candidates))*100,1),"signatures":signatures}

def traceability(profile,chosen):
    result=[]
    dr=drivers(profile)["mapping"]
    driver_map=defaultdict(list)
    for x in dr:
        for d in x["drivers"]: driver_map[x["requirement_id"]].append(d)
    for rid,text,_ in _all_reqs(profile):
        comps=chosen.get("requirement_mappings",{}).get(rid,[])
        result.append({"requirement_id":rid,"requirement":text,
                       "architectural_driver":driver_map.get(rid,["Business capability isolation"])[0],
                       "decision":f"Retain {chosen['name']} with requirement-specific boundary for {rid}",
                       "components":comps,
                       "evidence":[f"Requirement text: {text}",f"Candidate score: {chosen['scores']['weighted_total']}"],
                       "evaluation":{"coverage":chosen.get("requirement_coverage",{}).get(rid,False),
                                     "weighted_score":chosen["scores"]["weighted_total"]},
                       "critique":[f["title"] for f in chosen.get("critique_findings",[]) if rid in f.get("affected_requirements",[])],
                       "candidate_links":[]})
    return result
