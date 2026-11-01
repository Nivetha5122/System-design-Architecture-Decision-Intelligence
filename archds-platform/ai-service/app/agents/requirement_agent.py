import re
from ..models import RequirementInput,RequirementProfile,ATTRIBUTES

KEYWORDS={
 "scalability":["scale","scalable","concurrent","traffic","million","high volume","throughput"],
 "security":["secure","security","encrypt","pci","hipaa","privacy","auth","fraud","sensitive"],
 "realtime":["real-time","realtime","live","instant","tracking"],
 "async":["asynchronous","async","event","queue","notification","background","stream"],
 "availability":["availability","24/7","uptime","failover","disaster","99.9","99.99","resilient"],
 "auditability":["audit","trace","history","compliance","ledger","non-repudiation"],
 "read_heavy":["read-heavy","search","analytics","dashboard","reporting"],
 "bursty":["burst","spike","unpredictable","seasonal","weekend"],
 "domain":["complex business rules","domain","workflow","rules"],
 "low_latency":["low latency","latency","milliseconds","ms"],
 "cost_sensitive":["low budget","cheap","cost-effective","cost","budget"],
 "iot":["iot","sensor","device","telemetry"],
}

def _sentences(text): return [x.strip(" .") for x in re.split(r"\n|;|(?<=[.!?])\s+",text) if x.strip()]

def analyze(req:RequirementInput)->RequirementProfile:
    f=list(dict.fromkeys([x.strip() for x in req.functional_requirements if x.strip()]))
    nf=list(dict.fromkeys([x.strip() for x in req.non_functional_requirements if x.strip()]))
    cons=list(dict.fromkeys([x.strip() for x in req.constraints if x.strip()]))
    tech=list(dict.fromkeys([x.strip() for x in req.technology_preferences if x.strip()]))
    # Natural-language mode: derive a first structured requirement profile from the
    # user description when the structured fields were left empty. This keeps the
    # pipeline requirement-driven without forcing a user to understand architecture terminology.
    description_sentences=_sentences(req.description or '')
    quality_words={w for words in KEYWORDS.values() for w in words}
    if not f:
        derived_f=[]
        for sentence in description_sentences:
            low=sentence.lower()
            if any(w in low for w in quality_words) and not any(v in low for v in ('must','should','require','need','available','secure','scal')):
                continue
            if len(sentence.split())>=3:
                derived_f.append(sentence)
        f=list(dict.fromkeys(derived_f[:20]))
    if not nf:
        derived_nf=[]
        for sentence in description_sentences:
            low=sentence.lower()
            if any(w in low for w in quality_words) or any(v in low for v in ('must','should','require','available','secure','scal')):
                derived_nf.append(sentence)
        nf=list(dict.fromkeys(derived_nf[:20]))
    cons=list(dict.fromkeys(cons))
    text=" ".join(f+nf+cons+tech+[req.description or "",req.expected_users or "",req.budget or ""]).lower()
    def has_positive(words):
        for w in words:
            for m in re.finditer(re.escape(w), text):
                window=text[max(0,m.start()-28):m.start()]
                if re.search(r"\b(no|not|without|never|non)\s+(?:\w+\s+){0,2}$", window):
                    continue
                return True
        return False
    tags=[k for k,words in KEYWORDS.items() if has_positive(words)]
    if re.search(r"\b(normal|standard|ordinary|basic)\s+availability\b", text):
        tags=[t for t in tags if t!="availability"]
    drivers=[]
    for item in nf+cons:
        if item not in drivers: drivers.append(item)
    if "scalability" in tags: drivers.append("Capacity and independent scaling")
    if "security" in tags: drivers.append("Security and trust boundaries")
    if "realtime" in tags: drivers.append("Real-time responsiveness")
    if "availability" in tags: drivers.append("Availability and fault tolerance")
    if "auditability" in tags: drivers.append("Auditability and evidence retention")
    drivers=list(dict.fromkeys(drivers))[:16]
    assumptions=[]; ambiguities=[]; questions=[]
    if not req.expected_users: ambiguities.append("Expected workload/concurrency is not quantified"); questions.append("What peak concurrent users or requests per second should the architecture support?")
    if not req.budget: assumptions.append("No explicit budget was supplied; cost is evaluated relatively")
    if not tech: assumptions.append("No technology preference was supplied; technology is selected only when justified by the stated requirements")
    if not any(x in text for x in ["availability","uptime","99.","failover"]): questions.append("What availability/SLA target is required?")
    if "security" not in tags: assumptions.append("Baseline authentication, authorization and TLS are assumed"); questions.append("Does the system handle sensitive, regulated, or financial data?")
    if not f: questions.append("What are the primary business capabilities the system must provide?")
    if not nf: questions.append("Which quality attributes matter most: performance, security, reliability, cost, maintainability, or scalability?")
    contradictions=[]
    if ("cost_sensitive" in tags and "availability" in tags and any(x in text for x in ["five regions","5 regions","multi-region","active-active"])):
        contradictions.append({"left":"Low infrastructure cost","right":"Multi-region high availability","severity":"HIGH","resolution_options":["Prioritize availability","Prioritize cost","Keep both with an explicit budget ceiling"]})
    total=max(1,len(f)+len(nf)+len(cons)); completeness=min(100,round((len(f)*1.0+len(nf)*1.2+len(cons)*.7+(1 if req.expected_users else 0)+(1 if req.budget else 0))/max(1,total+3)*100,1))
    if f and nf: completeness=min(100,completeness+12)
    specificity=min(100,55+15*bool(req.expected_users)+15*bool(nf)+10*bool(req.budget)+5*bool(tech))
    consistency=100 if not contradictions else 65
    ambiguity=min(100,round((len(ambiguities)+len(questions))*8,1)); readiness=round(max(0,min(100,0.35*completeness+0.25*specificity+0.25*consistency+0.15*(100-ambiguity))),1)
    derived={a:5 for a in ATTRIBUTES}
    boosts={"scalability":"scalability","security":"security","availability":"availability","realtime":"performance","low_latency":"performance","auditability":"reliability","read_heavy":"performance","maintainability":"maintainability","domain":"maintainability","cost_sensitive":"cost","bursty":"scalability","async":"reliability","iot":"scalability"}
    for t in tags:
        a=boosts.get(t)
        if a: derived[a]+=30
    s=sum(derived.values()); derived={a:round(v*100/s) for a,v in derived.items()}; diff=100-sum(derived.values()); derived["performance"]+=diff
    user_w=req.quality_weights.as_dict()
    final_w={a:round(user_w[a]*0.6+derived[a]*0.4) for a in ATTRIBUTES}
    delta=100-sum(final_w.values()); final_w["performance"]+=delta
    return RequirementProfile(functional_requirements=f,non_functional_requirements=nf,constraints=cons,technology_preferences=tech,expected_users=req.expected_users,budget=req.budget,drivers=drivers,tags=tags,assumptions=assumptions,ambiguities=ambiguities,contradictions=contradictions,dependencies=[f"Expected workload: {req.expected_users}"] if req.expected_users else [],security_drivers=[x for x in nf+cons if any(k in x.lower() for k in ["security","privacy","encrypt","compliance","auth","pci","hipaa"])],scale_drivers=[x for x in f+nf if any(k in x.lower() for k in ["scale","concurrent","traffic","throughput","million"])],priority_weights=final_w,derived_weights=derived,completeness=completeness,specificity=specificity,consistency=consistency,ambiguity=ambiguity,architecture_readiness=readiness,clarification_questions=list(dict.fromkeys(questions)))
