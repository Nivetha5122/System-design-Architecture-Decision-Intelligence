from fastapi import FastAPI, Response
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from .models import PipelineResponse,RequirementInput
from .workflow.orchestrator import run_pipeline
from .agents.requirement_agent import analyze
from .knowledge_base import PATTERNS
from .report_pdf import build_pdf
from .digital_twin import simulate
app=FastAPI(title="ARCHDS Adaptive Architecture Decision System",version="5.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
@app.get("/health")
def health(): return {"status":"UP","agents":20,"optimization":"NSGA-II-compatible Pareto","llm_fallback":True}
@app.get("/api/v1/patterns")
def patterns(): return PATTERNS
@app.post("/api/v1/requirements/analyze")
def requirements_analyze(req:RequirementInput):
    p=analyze(req); return {"profile":p.model_dump(),"ready":p.architecture_readiness>=70 and not p.contradictions,"questions":p.clarification_questions}
@app.post("/api/v1/pipeline",response_model=PipelineResponse)
def pipeline(req:RequirementInput): return run_pipeline(req)
@app.post("/api/v1/what-if")
def what_if(req:RequirementInput,users:str="10x",availability:str="unchanged",scenario:str=""):
    baseline=run_pipeline(req)
    change_parts=[]
    if users not in ("unchanged", "1x", ""):
        change_parts.append(f"traffic/workload becomes {users}")
    if availability!="unchanged":
        change_parts.append(f"availability target becomes {availability}")
    if scenario:
        change_parts.append(scenario)
    change="; ".join(change_parts) or "no explicit numeric change; challenge the current architecture assumptions"
    scenario_text=f"{req.description} WHAT-IF CHANGE: {change}."
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



class DigitalTwinRequest(BaseModel):
    candidate: dict
    requirement_profile: dict = {}
    scenario_key: str = "baseline"
    custom_scenario: str = ""

@app.post("/api/v1/digital-twin")
def digital_twin(req: DigitalTwinRequest):
    return simulate(req.candidate, req.requirement_profile, req.scenario_key, req.custom_scenario)

@app.post("/api/v1/report/pdf")
def report_pdf(result: PipelineResponse):
    pdf = build_pdf(result.model_dump())
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=ARCHDS_Architecture_Report.pdf"})
