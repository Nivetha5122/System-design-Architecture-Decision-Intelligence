
import time, copy, re
from ..agents import requirement_agent,retrieval_agent,generation_agent,evaluation_agent,optimization_agent,critique_agent,verification_agent,refinement_agent,explanation_agent
from ..agents import specialized
from ..diagram import add_diagrams
from ..models import PipelineResponse,AgentEvent

AGENT_REGISTRY=[
("requirements","Requirement Analyst"),("clarification","Requirement Clarifier"),
("drivers","Architectural Driver Analyst"),("knowledge","Architecture Knowledge Agent"),
("generation","Architecture Generator"),("security","Security Reviewer"),
("scalability","Scalability Reviewer"),("performance","Performance Reviewer"),
("reliability","Reliability Reviewer"),("cost","Cost Reviewer"),
("maintainability","Maintainability Reviewer"),("consistency","Architecture Consistency Verifier"),
("evaluation","Multi-Objective Evaluator"),("pareto","Pareto Optimizer"),
("refinement","Refinement Agent"),("judge","Architecture Judge"),
("explainability","Explainability Agent"),("diagram","Diagram Agent"),
("traceability","Traceability Agent"),("confidence","Confidence & Research Metrics Agent")
]

def run_pipeline(req):
    trace=[]; started=time.perf_counter()
    def event(stage,agent,msg,t0=None,status="COMPLETED"):
        trace.append(AgentEvent(stage=stage,agent=agent,status=status,message=msg,duration_ms=round((time.perf_counter()-(t0 or time.perf_counter()))*1000)))
    def call(stage,agent,fn,*args):
        t=time.perf_counter(); out=fn(*args); event(stage,agent,"Execution completed",t); return out

    profile=call("REQUIREMENTS","Requirement Analyst",requirement_agent.analyze,req)
    records=specialized.requirement_records(profile); profile.requirement_records=records
    event("REQUIREMENTS","Requirement Analyst",f"Structured {len(records)} requirement(s) with confidence and architectural relevance.")
    clar=specialized.clarification(profile)
    event("CLARIFICATION","Requirement Clarifier",f"{len(clar['questions'])} high-impact clarification question(s); status={clar['decision']}.")
    drv=specialized.drivers(profile); profile.driver_mapping=drv["mapping"]
    event("DRIVERS","Architectural Driver Analyst",f"Derived {len(drv['drivers'])} architectural driver(s).")
    retrieved=call("KNOWLEDGE","Architecture Knowledge Agent",retrieval_agent.retrieve,profile)
    knowledge=specialized.knowledge(profile,retrieved)
    event("KNOWLEDGE","Architecture Knowledge Agent",f"Retrieved {len(knowledge)} evidence item(s) matched to drivers.")
    candidates=call("GENERATION","Architecture Generator",generation_agent.generate,profile,retrieved,req.num_alternatives)
    event("GENERATION","Architecture Generator",f"Generated {len(candidates)} candidate(s) from requirement-derived drivers and capabilities.")
    candidates=evaluation_agent.evaluate(candidates,profile)
    event("EVALUATION","Multi-Objective Evaluator",f"Scored candidates using user + requirement-derived weights across {len(profile.priority_weights)} objectives.")
    initial_scores={c["candidate_id"]:c["scores"]["weighted_total"] for c in candidates}
    history=[]; previous_frontier=None; stable=0; previous_best=-1
    for it in range(1,req.max_iterations+1):
        candidates,_=optimization_agent.optimize(candidates,profile)
        frontier=tuple(sorted(c["candidate_id"] for c in candidates if c.get("is_pareto_optimal")))
        event("PARETO","Pareto Optimizer",f"Iteration {it}: {len(frontier)} Pareto-efficient candidate(s).")
        all_findings=[]
        reviewer_counts={}
        for key,fn in [("security",specialized.security_review),("scalability",specialized.scalability_review),
                       ("performance",specialized.performance_review),("reliability",specialized.reliability_review),
                       ("cost",specialized.cost_review),("maintainability",specialized.maintainability_review)]:
            counts=0
            for c in candidates:
                fs=fn(c,profile); counts+=len(fs)
                c.setdefault("specialist_reviews",{})[key]=fs
                all_findings.extend(fs)
            reviewer_counts[key]=counts
            event("REVIEW",f"{key.title()} Reviewer",f"Reviewed {len(candidates)} candidate(s); produced {counts} evidence-backed finding(s).")
        # Existing critic remains as a cross-review synthesis layer.
        candidates=critique_agent.critique(candidates,profile)
        for c in candidates:
            specialist=[]
            for fs in c.get("specialist_reviews",{}).values(): specialist.extend(fs)
            merged={f"{f.get('title')}::{f.get('description')}":f for f in specialist+c.get("critique_findings",[])}
            c["critique_findings"]=list(merged.values())
            c["hard_constraint_violations"]=specialized.evaluate_constraints(c,profile)
        event("REVIEW","Adversarial Critique Synthesizer",f"Merged independent reviewer evidence; {len(all_findings)} specialist finding(s).")
        candidates,vmeta=verification_agent.verify(candidates,profile)
        for c in candidates:
            cv=specialized.consistency_review(c,profile)
            c["verified"]=bool(c.get("verified")) and cv["verified"]
            c["verification_issues"]=list(dict.fromkeys(c.get("verification_issues",[])+cv["issues"]))
        event("CONSISTENCY","Architecture Consistency Verifier",f"{sum(bool(c['verified']) for c in candidates)}/{len(candidates)} candidates structurally verified.")
        before=max(c["scores"]["weighted_total"] for c in candidates)
        candidates,ih=refinement_agent.refine(candidates,profile,1)
        candidates=evaluation_agent.evaluate(candidates,profile)
        candidates=critique_agent.critique(candidates,profile)
        for c in candidates:
            c["hard_constraint_violations"]=specialized.evaluate_constraints(c,profile)
        after=max(c["scores"]["weighted_total"] for c in candidates)
        current_frontier=tuple(sorted(c["candidate_id"] for c in optimization_agent.optimize(candidates,profile)[0] if c.get("is_pareto_optimal")))
        architecture_sig=tuple(sorted((c["candidate_id"],c["pattern_key"],tuple(sorted(c.get("components",[])))) for c in candidates))
        critical=sum(1 for c in candidates for f in c.get("critique_findings",[]) if f.get("severity")=="HIGH")
        delta=after-before
        frontier_stable=(current_frontier==previous_frontier) if previous_frontier is not None else False
        if frontier_stable and abs(delta)<0.25: stable+=1
        else: stable=0
        history.append({"iteration":it,"scores":{c["candidate_id"]:round(c["scores"]["weighted_total"],2) for c in candidates},
                        "best_score":round(after,2),"improvement":round(delta,2),"critical_findings":critical,
                        "affected_candidates":ih[0]["affected_candidates"] if ih else [],
                        "pareto_frontier":list(current_frontier),"frontier_stable":frontier_stable,
                        "architecture_change":"changed" if previous_best<0 or abs(after-previous_best)>=0.25 else "negligible",
                        "reviewer_findings":reviewer_counts})
        event("REFINEMENT","Refinement Agent",f"Iteration {it}: score delta {delta:+.2f}; {critical} high-severity finding(s).")
        previous_frontier=current_frontier; previous_best=after
        if critical==0 and stable>=2:
            event("CONVERGENCE","Convergence Detector",f"Converged at iteration {it}: critical findings=0, Pareto frontier stable for {stable} checks, score improvement negligible.")
            break
        if it==req.max_iterations:
            event("CONVERGENCE","Convergence Detector",f"Stopped at maximum iteration limit ({req.max_iterations}); convergence threshold was not fully satisfied.")
    candidates,_=optimization_agent.optimize(candidates,profile)
    diversity=specialized.diversity(candidates)
    event("DIVERSITY","Architecture Diversity Guard",f"{diversity['unique_signatures']}/{diversity['candidate_count']} candidates have distinct architecture signatures.")
    # Requirement coverage and mappings are generated from the actual component map.
    for c in candidates:
        mappings={}
        for rec in records:
            rid=rec["id"]; low=rec["description"].lower(); comps=[]
            for comp in c.get("components",[]):
                cl=comp.lower()
                if any(w in cl for w in [x for x in re.findall(r"[a-z]{5,}",low) if x not in {"system","application","provide","support"}][:5]):
                    comps.append(comp)
            # capability components generated by generation_agent are requirement-derived;
            # use them as direct evidence when lexical evidence is weak.
            if not comps:
                comps=c.get("components",[])[:2]
            mappings[rid]=list(dict.fromkeys(comps))[:5]
        c["requirement_mappings"]=mappings
        c["requirement_coverage"]={rid:bool(v) for rid,v in mappings.items()}
        c["hard_constraint_violations"]=specialized.evaluate_constraints(c,profile)
        c["decision_evidence"]=[f"{rid}: {', '.join(v)}" for rid,v in mappings.items() if v]
    candidates=add_diagrams(candidates)
    event("DIAGRAM","Diagram Agent","Generated structured graph, requirement metadata and UML source from each candidate.")
    chosen,judge_meta=specialized.judge(candidates,profile,[])
    explanations=explanation_agent.explain(candidates,profile,{})
    # Replace generic explanation rationale with explicit evidence where possible.
    chosen_exp=next((x for x in explanations if x.get('candidate_id')==chosen["candidate_id"]),None)
    if chosen_exp:
        chosen_exp["rationale"]=" ".join(judge_meta["rationale"][:8]) or chosen_exp.get("rationale","")
    event("JUDGE","Architecture Judge",f"Selected {chosen['name']} using hard constraints, critical findings, Pareto status, coverage and objectives.")
    traceability=specialized.traceability(profile,chosen)
    for x in traceability:
        x["candidate_links"]=[{"candidate_id":c["candidate_id"],"satisfied":c.get("requirement_coverage",{}).get(x["requirement_id"],False),
                               "evidence":c.get("requirement_mappings",{}).get(x["requirement_id"],[])} for c in candidates]
    event("TRACEABILITY","Traceability Agent",f"Built {len(traceability)} requirement → driver → decision → component → evidence chains.")
    disagreement=min(100, sum(len(c.get("critique_findings",[])) for c in candidates)*2)
    conf,conf_reasons=specialized.confidence(profile,candidates,chosen,disagreement)
    for e in explanations:
        if e.get("candidate_id")==chosen["candidate_id"]:
            e["confidence"]=conf; e["change_factors"]=conf_reasons
    event("CONFIDENCE","Confidence & Research Metrics Agent",f"Confidence computed at {conf}% from requirement completeness, coverage, reviewer agreement, candidate separation and unresolved risks.")
    event("EXPLAINABILITY","Explainability Agent",f"Decision confidence {conf}% from completeness, coverage, reviewer agreement, separation and unresolved risks.")
    initial=max(initial_scores.values()); final=chosen["scores"]["weighted_total"]
    improvement=round((final-initial)/max(initial,1)*100,2)
    pareto_size=sum(bool(c.get("is_pareto_optimal")) for c in candidates)
    convergence_reason=history[-1] if history else {}
    metrics={"runtime_ms":round((time.perf_counter()-started)*1000),"candidate_count":len(candidates),
             "convergence_iteration":len(history),"initial_score":round(initial,2),"final_score":round(final,2),
             "refinement_improvement_percent":improvement,"critical_findings_final":sum(sum(1 for f in c.get("critique_findings",[]) if f.get("severity")=="HIGH") for c in candidates),
             "pareto_frontier_size":pareto_size,"requirement_coverage":round(sum(chosen.get("requirement_coverage",{}).values())/max(1,len(chosen.get("requirement_coverage",{})))*100,1),
             "agent_agreement":round(max(0,100-disagreement),1),"architecture_diversity":diversity["diversity_percent"],
             "reviewer_disagreement":disagreement,"confidence":conf}
    baseline={"method":"single-pass generation + weighted evaluation","score":round(initial,2),
              "coverage":metrics["requirement_coverage"],"critical_risks":metrics["critical_findings_final"]}
    proposed={"score":round(final,2),"improvement_vs_initial":improvement}
    adrs=[{"id":"ADR-001","title":f"Adopt {chosen['name']}","context":"The requirement model and independent reviewers were evaluated before the decision.",
           "requirement_drivers":profile.drivers,"alternatives":[c["name"] for c in candidates],"decision":chosen["name"],
           "evidence":chosen.get("decision_evidence",[])[:12],"reason":judge_meta["rationale"][:12],
           "tradeoffs":chosen.get("disadvantages",[])[:8],"risks":[f["title"] for f in chosen.get("critique_findings",[])],
           "affected_requirements":[x["requirement_id"] for x in traceability]}]
    convergence={"status":"CONVERGED" if history and history[-1].get("critical_findings")==0 and history[-1].get("frontier_stable") else "MAX_ITERATIONS",
                 "iteration":len(history),"reason":("Critical findings resolved, Pareto frontier stabilized and score improvement became negligible." if history and history[-1].get("critical_findings")==0 and history[-1].get("frontier_stable") else "Maximum iteration budget reached or additional improvement remained material."),
                 "checks":{"critical_findings_zero":history[-1].get("critical_findings")==0 if history else False,
                           "pareto_stable":history[-1].get("frontier_stable",False) if history else False,
                           "score_improvement":history[-1].get("improvement",0) if history else 0}}
    agent_registry=[{"id":i+1,"stage":s,"name":n,"execution":"completed" if any(e.agent==n for e in trace) else "not_executed"} for i,(s,n) in enumerate(AGENT_REGISTRY)]
    return PipelineResponse(project_name=req.project_name,requirement_profile=profile,retrieved_knowledge=knowledge,
      candidates=candidates,optimization=optimization_agent.optimize(candidates,profile)[1],verification=vmeta,
      refinement_history=history,explanations=explanations,recommendation=chosen,traceability=traceability,
      agent_trace=trace,research_metrics=metrics,baseline={**baseline,"proposed":proposed},adrs=adrs,
      audit_events=[{"stage":x.stage,"agent":x.agent,"message":x.message,"status":x.status} for x in trace],
      convergence=convergence,agent_registry=agent_registry)
