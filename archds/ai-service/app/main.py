from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import PipelineResponse,RequirementInput
from .workflow.orchestrator import run_pipeline
from .agents.requirement_agent import analyze
from .knowledge_base import PATTERNS
from .report import pdf_response
from .digital_twin import scenario_catalog, simulate, evolve
from .devops_lab import generate_delivery
app=FastAPI(title="ARCHDS Adaptive Architecture Decision System",version="3.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
@app.get("/health")
def health(): return {"status":"UP","release":"AUTO-REQUIREMENTS","agents":20,"optimization":"Discrete non-dominated Pareto analysis","objective_weights":"requirement-derived by default","llm_fallback":True}
@app.get("/api/v1/patterns")
def patterns(): return PATTERNS
@app.post("/api/v1/requirements/analyze")
def requirements_analyze(req:RequirementInput):
    p=analyze(req); return {"profile":p.model_dump(),"ready":p.architecture_readiness>=70 and not p.contradictions,"questions":p.clarification_questions}
@app.post("/api/v1/pipeline",response_model=PipelineResponse)
def pipeline(req:RequirementInput): return run_pipeline(req)
@app.post("/api/v1/what-if")
def what_if(req:RequirementInput,users:str="10x",availability:str="unchanged"):
    baseline=run_pipeline(req)
    scenario_text=f"{req.description} WHAT-IF CHANGE: traffic/workload becomes {users}. Availability target becomes {availability}." if availability!="unchanged" else f"{req.description} WHAT-IF CHANGE: traffic/workload becomes {users}."
    changed=req.model_copy(update={"description":scenario_text})
    scenario=run_pipeline(changed)
    before=set(baseline.recommendation.components); after=set(scenario.recommendation.components)
    return {"scenario":{"users":users,"availability":availability},
            "current_score":baseline.recommendation.scores.weighted_total,
            "scenario_score":scenario.recommendation.scores.weighted_total,
            "score_change":round(scenario.recommendation.scores.weighted_total-baseline.recommendation.scores.weighted_total,2),
            "impact":{"added_components":sorted(after-before),"removed_components":sorted(before-after),
                      "architecture_changed":baseline.recommendation.pattern_key!=scenario.recommendation.pattern_key},
            "recommended_changes":scenario.recommendation.decision_evidence[:8],
            "architecture":scenario.recommendation.model_dump()}

@app.post("/api/v1/stress-test")
def stress(req:RequirementInput,scenario:str="10x traffic"):
    baseline=run_pipeline(req)
    changed=req.model_copy(update={"description":f"{req.description} STRESS TEST: {scenario}. Analyze failure propagation and recovery requirements."})
    stressed=run_pipeline(changed)
    before=set(baseline.recommendation.components); after=set(stressed.recommendation.components)
    return {"scenario":scenario,"status":"RESILIENCE_REVIEWED",
            "weaknesses":[f["title"] for f in stressed.recommendation.critique_findings if f["severity"] in ("HIGH","MEDIUM")][:10],
            "affected_components":sorted(before|after)[:20],
            "score_change":round(stressed.recommendation.scores.reliability-baseline.recommendation.scores.reliability,2),
            "recommended_changes":stressed.recommendation.decision_evidence[:8],
            "architecture_changed":baseline.recommendation.pattern_key!=stressed.recommendation.pattern_key}

@app.post("/api/v1/digital-twin/scenarios")
def digital_twin_scenarios(payload:dict):
    return {"scenarios": scenario_catalog(payload.get("requirements", payload), payload.get("candidate", {}))}

@app.post("/api/v1/digital-twin/simulate")
def digital_twin_simulate(payload:dict):
    return simulate(payload.get("requirements", {}), payload.get("candidate", {}), payload.get("scenario_id", "traffic_surge"), float(payload.get("intensity", 1.0)))

@app.post("/api/v1/digital-twin/evolve")
def digital_twin_evolve(payload:dict):
    return evolve(payload.get("requirements", {}), payload.get("candidate", {}), payload.get("scenario_id", "traffic_surge"), float(payload.get("intensity", 1.0)))

@app.post("/api/v1/delivery/generate")
def delivery_generate(payload:dict):
    return generate_delivery(payload, payload.get("candidate") or {})

@app.post("/api/v1/report/pdf")
def report_pdf(payload:dict): return pdf_response(payload)

def _advisor_deterministic(question, result):
    q=question.lower()
    rec=result.get('recommendation') or {}
    profile=result.get('requirement_profile') or {}
    candidates=result.get('candidates') or []
    reqs=profile.get('requirement_records') or []
    req_text=[str(r.get('description') or '').strip() for r in reqs if r.get('description')]
    mappings=rec.get('requirement_mappings') or {}
    coverage=rec.get('requirement_coverage') or {}
    findings=rec.get('critique_findings') or []
    evidence=rec.get('decision_evidence') or []
    drivers=profile.get('drivers') or []
    def names(items,limit=4): return '; '.join(str(x) for x in items[:limit] if x)
    if not rec:
        return {'answer':'No completed architecture analysis is available for this project yet. Run the analysis first so ARCHDS can answer from the submitted requirements.','issues':[],'suggestions':[]}
    issues=[]; suggestions=[]
    if any(k in q for k in ('risk','problem','issue','weak','failure','vulnerab','danger')):
        for f in findings[:6]: issues.append({'severity':f.get('severity','REVIEW'),'title':f.get('title','Architecture finding'),'detail':f.get('description','')})
        if issues:
            answer='The selected architecture has these evidence-backed risk findings: ' + ' '.join(f"{x['title']} ({x['severity']}): {x['detail']}" for x in issues[:4])
        else:
            answer='No reviewer finding was stored for the selected architecture. That does not prove the architecture is risk-free; validate the highest-priority requirements with Digital Twin scenarios and deployment checks before approval.'
    elif any(k in q for k in ('requirement','functional','nfr','quality attribute','least protected','covered','coverage')):
        uncovered=[r for r in reqs if coverage.get(r.get('id')) is False]
        if uncovered:
            answer='The least-protected submitted requirements are: ' + '; '.join(str(r.get('description')) for r in uncovered[:4]) + '. Their candidate coverage is marked as a gap in the stored evidence.'
        else:
            answer=f"The selected architecture reports coverage for {sum(1 for v in coverage.values() if v)}/{len(coverage)} mapped requirements. The strongest architectural drivers are {names(drivers,6) or 'those derived during requirement analysis'}."
        for r in reqs[:6]:
            rid=r.get('id'); comps=mappings.get(rid,[]) or mappings.get(str(rid),[])
            if comps: suggestions.append(f"{rid}: {r.get('description')} → {', '.join(comps[:4])}")
    elif any(k in q for k in ('traffic','load','scale','scalab','10 times','ten times','users','throughput')):
        scale=profile.get('expected_users') or 'the submitted scale target'
        comps=rec.get('components') or []
        scale_comps=[c for c in comps if any(k in str(c).lower() for k in ('load','scale','cache','queue','broker','gateway','service','replica'))]
        answer=f"For the submitted scale ({scale}), the selected {rec.get('name','architecture')} has these modeled components: {names(scale_comps,6) or names(comps,6)}. The stored scalability score is {rec.get('scores',{}).get('scalability','not available')}. A useful next step is to run a Digital Twin traffic-surge scenario rather than assume a fixed capacity limit."
        suggestions=['Run the requirement-grounded Digital Twin traffic scenario at increasing intensity.','Re-run the Pareto comparison after changing the scale requirement.']
    elif any(k in q for k in ('security','secure','auth','encrypt','privacy','audit')):
        sec=[r for r in reqs if any(k in str(r.get('description','')).lower() for k in ('security','auth','encrypt','privacy','audit'))]
        sec_comps=[]
        for r in sec:
            sec_comps += mappings.get(r.get('id'),[]) or []
        answer=f"Security-related submitted requirements include: {names([r.get('description') for r in sec],5) or 'none explicitly classified'}. The selected architecture maps them to {names(list(dict.fromkeys(sec_comps)),6) or 'no explicit component mapping'}. Review the security reviewer findings before approval."
    elif any(k in q for k in ('cost','budget','price','expensive','cheap')):
        answer=f"The architecture was evaluated with the submitted cost/budget priorities. Its cost score is {rec.get('scores',{}).get('cost','not available')}, while the weighted total is {rec.get('scores',{}).get('weighted_total','not available')}. Any cost reduction should preserve higher-priority requirements rather than apply a generic optimization."
        suggestions=['Run the Digital Twin cost-pressure scenario if it is available for this requirement profile.','Compare the selected candidate with the strongest Pareto alternative before changing components.']
    elif any(k in q for k in ('why','selected','choose','alternative','better','compare')):
        ranked=sorted(candidates,key=lambda c:float((c.get('scores') or {}).get('weighted_total') or 0),reverse=True)
        alternatives=[f"{c.get('name')} ({(c.get('scores') or {}).get('weighted_total','—')})" for c in ranked[:5]]
        answer=f"ARCHDS selected {rec.get('name')} because it achieved a weighted score of {(rec.get('scores') or {}).get('weighted_total','—')} with {sum(1 for v in coverage.values() if v)}/{len(coverage)} requirement mappings covered. The candidate evidence says: {names(evidence,4) or rec.get('description','No additional rationale was stored.')}. Compared candidates: {', '.join(alternatives)}."
    elif any(k in q for k in ('deploy','production','release','validate','ready')):
        answer=f"Before production acceptance of {rec.get('name')}, validate the requirements most exposed by the reviewer evidence, then run Digital Twin failure/load scenarios and generate the Delivery Lab artifacts. The current analysis has {len(findings)} stored reviewer finding(s) and {sum(1 for v in coverage.values() if v)}/{len(coverage)} mapped requirements covered."
        suggestions=['Review all HIGH severity findings.','Run at least one requirement-grounded failure or workload scenario.','Validate Terraform/Kubernetes/Compose artifacts in the Delivery Lab.']
    else:
        # Arbitrary questions still receive a useful, evidence-grounded synthesis instead of a generic fallback.
        answer=(f"I interpreted your question against the submitted requirement profile and selected architecture {rec.get('name')}. "
                f"The analysis contains {len(req_text)} requirement records, {len(candidates)} competing candidates, "
                f"{len(findings)} reviewer findings and {len(evidence)} decision-evidence items. "
                f"The main architectural drivers are {names(drivers,6) or 'derived from the submitted requirements'}. "
                "If your question depends on a change to a requirement, state the exact change and ARCHDS can evaluate the corresponding counterfactual rather than invent an answer.")
    return {'answer':answer,'issues':issues[:8],'suggestions':suggestions[:8]}


@app.post("/api/v1/advisor")
def architecture_advisor(payload:dict):
    """Answer architecture questions from the current analysis; optionally enrich with a configured LLM."""
    from .providers.llm_provider import provider
    question=str(payload.get('question') or '').strip()
    result=payload.get('result') or {}
    if not question:
        return {'mode':'deterministic','answer':'Ask a question about the submitted requirements, candidate, trade-offs, risks, Digital Twin or delivery artifacts.','issues':[],'suggestions':[]}
    deterministic=_advisor_deterministic(question,result)
    rec=result.get('recommendation') or {}; profile=result.get('requirement_profile') or {}; candidates=result.get('candidates') or []
    context={'question':question,'recommendation':rec,'drivers':profile.get('drivers',[])[:12],'requirements':profile.get('requirement_records',[])[:20],
             'review_findings':rec.get('critique_findings',[])[:12],'decision_evidence':rec.get('decision_evidence',[])[:12],
             'alternatives':[{'name':c.get('name'),'score':c.get('scores',{}).get('weighted_total')} for c in candidates[:8]]}
    enriched=provider().enrich('You are the senior architecture advisor inside ARCHDS. Answer only from the supplied evidence. Directly answer the user question, cite requirement descriptions or architecture components when relevant, distinguish facts from recommendations, and never invent missing data.',context)
    if enriched.get('mode')=='llm' and enriched.get('content'):
        return {'mode':'llm','answer':enriched['content'],'issues':deterministic['issues'],'suggestions':deterministic['suggestions'],
                'evidence':{'architecture':rec.get('name'),'drivers':profile.get('drivers',[])[:8],'candidate_count':len(candidates)}}
    return {'mode':'deterministic','answer':deterministic['answer'],'issues':deterministic['issues'],'suggestions':deterministic['suggestions'],
            'evidence':{'architecture':rec.get('name'),'drivers':profile.get('drivers',[])[:8],'candidate_count':len(candidates)}}

