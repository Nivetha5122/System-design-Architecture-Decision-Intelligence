from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, model_validator

ATTRIBUTES=["performance","scalability","security","reliability","availability","maintainability","extensibility","cost","complexity","observability","deployment_complexity","operational_risk"]

class QualityWeights(BaseModel):
    performance:int=15; scalability:int=15; security:int=15; reliability:int=15; availability:int=0; maintainability:int=10; extensibility:int=10; cost:int=5; complexity:int=5; observability:int=0; deployment_complexity:int=0; operational_risk:int=10
    @model_validator(mode="before")
    @classmethod
    def legacy_compat(cls,data):
        if data == {} or data is None:
            return {"performance":15,"scalability":15,"security":15,"reliability":15,"availability":0,"maintainability":10,"extensibility":10,"cost":5,"complexity":5,"observability":0,"deployment_complexity":0,"operational_risk":10}
        if isinstance(data,dict) and not any(k in data for k in ["availability","observability","deployment_complexity","operational_risk"]):
            data=dict(data); data.update({"availability":0,"observability":0,"deployment_complexity":0,"operational_risk":0})
            if sum(int(data.get(k,0)) for k in ["performance","scalability","security","reliability","maintainability","extensibility","cost","complexity"])==90: data["cost"]=int(data.get("cost",0))+10
        return data
    @model_validator(mode="after")
    def validate_total(self):
        vals=[getattr(self,a) for a in ATTRIBUTES]
        if sum(vals)==90 and self.availability==0 and self.observability==0 and self.deployment_complexity==0 and self.operational_risk==10:
            self.cost += 10; vals=[getattr(self,a) for a in ATTRIBUTES]
        if any(v<0 or v>100 for v in vals) or sum(vals)!=100: raise ValueError("quality_weights must be non-negative and sum to 100")
        return self
    def as_dict(self): return {a:getattr(self,a) for a in ATTRIBUTES}

class RequirementInput(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def empty_weights_mean_auto(cls, data):
        if isinstance(data, dict) and data.get("quality_weights") == {}:
            data = dict(data)
            data["quality_weights"] = None
        return data
    project_name:str=Field(min_length=2,max_length=160)
    description:str=""
    functional_requirements:List[str]=Field(default_factory=list)
    non_functional_requirements:List[str]=Field(default_factory=list)
    constraints:List[str]=Field(default_factory=list)
    technology_preferences:List[str]=Field(default_factory=list)
    expected_users:Optional[str]=None
    budget:Optional[str]=None
    quality_weights:Optional[QualityWeights]=None
    num_alternatives:int=Field(5,ge=2,le=8)
    max_iterations:int=Field(5,ge=1,le=10)
    @model_validator(mode="after")
    def has_requirements(self):
        if not (self.functional_requirements or self.non_functional_requirements or self.description): raise ValueError("Provide requirements or a system description")
        return self

class RequirementProfile(BaseModel):
    functional_requirements:List[str]; non_functional_requirements:List[str]; constraints:List[str]; technology_preferences:List[str]=[]; expected_users:Optional[str]=None; budget:Optional[str]=None; drivers:List[str]; tags:List[str]; assumptions:List[str]; ambiguities:List[str]; contradictions:List[Dict[str,Any]]; dependencies:List[str]; security_drivers:List[str]; scale_drivers:List[str]; priority_weights:Dict[str,int]; derived_weights:Dict[str,int]; completeness:float; specificity:float; consistency:float; ambiguity:float; architecture_readiness:float; clarification_questions:List[str]; requirement_records:List[Dict[str,Any]]=[]; driver_mapping:List[Dict[str,Any]]=[]

class Score(BaseModel):
    performance:float; scalability:float; security:float; reliability:float; availability:float; maintainability:float; extensibility:float; cost:float; complexity:float; observability:float; deployment_complexity:float; operational_risk:float; weighted_total:float

class Risk(BaseModel):
    severity:str; description:str; affected_requirements:List[str]=[]

class Candidate(BaseModel):
    candidate_id:str; pattern_key:str; name:str; description:str; components:List[str]; relations:List[str]; data_stores:List[str]=[]; communication_patterns:List[str]=[]; deployment_model:Dict[str,Any]={}; security_model:Dict[str,Any]={}; scaling_strategy:Dict[str,Any]={}; failure_strategy:Dict[str,Any]={}; observability:Dict[str,Any]={}; tech_stack:Dict[str,str]={}; advantages:List[str]=[]; disadvantages:List[str]=[]; assumptions:List[str]=[]; risks:List[Risk]=[]; scores:Score; objective_values:Dict[str,float]={}; is_pareto_optimal:bool=False; dominated:bool=False; verified:bool=False; verification_issues:List[str]=[]; critique_findings:List[Dict[str,Any]]=[]; requirement_coverage:Dict[str,bool]={}; refinement_iteration:int=0; refinement_notes:List[str]=[]; component_requirements:Dict[str,List[str]]={}; graph:Dict[str,Any]={}; plantuml_source:str=""; diagram_svg:str=""; uml:Dict[str,Any]={}; uml_plantuml:Dict[str,str]={}; uml_svg:Dict[str,str]={}; system_design_framework:Dict[str,Any]={}; requirement_mappings:Dict[str,List[str]]={}; technology_evidence:Dict[str,List[str]]={}; component_evidence:Dict[str,List[str]]={}; hard_constraint_violations:List[str]=[]; decision_evidence:List[str]=[]

class AgentEvent(BaseModel): stage:str; agent:str; status:str; message:str; duration_ms:int=0
class Explanation(BaseModel): candidate_id:str; rationale:str; strengths:List[str]; tradeoffs:List[str]; risks:List[str]; assumptions:List[str]; confidence:float; change_factors:List[str]; evidence:List[str]=[]
class PipelineResponse(BaseModel):
    project_name:str; requirement_profile:RequirementProfile; retrieved_knowledge:List[Dict[str,Any]]; candidates:List[Candidate]; optimization:Dict[str,Any]; verification:Dict[str,Any]; refinement_history:List[Dict[str,Any]]; explanations:List[Explanation]; recommendation:Candidate; traceability:List[Dict[str,Any]]; agent_trace:List[AgentEvent]; research_metrics:Dict[str,Any]; baseline:Dict[str,Any]; adrs:List[Dict[str,Any]]; audit_events:List[Dict[str,Any]]; convergence:Dict[str,Any]={}; agent_registry:List[Dict[str,Any]]=[]; research_framework:Dict[str,Any]={}
