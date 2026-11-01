import copy
import uuid

def _improve_candidate(c, profile, iteration):
    """Apply evidence-driven architectural mutations to one candidate."""
    c.setdefault("refinement_notes", [])
    issues=c.get("verification_issues",[])+[f["description"] for f in c.get("critique_findings",[]) if f.get("severity")=="HIGH"]
    text=" ".join(issues).lower()
    changed=[]
    def add(name):
        if name not in c["components"]:
            c["components"].append(name); changed.append(name)
        c.setdefault("component_requirements", {})
        req_ids=[f"R{i}" for i in range(1, len(profile.functional_requirements)+len(profile.non_functional_requirements)+1)]
        c["component_requirements"].setdefault(name, req_ids[:])
    if "identity" in text: add("Security Policy / Secrets Boundary")
    if "scal" in text or "bottleneck" in text: add("Horizontal Scaling / Load Balancing")
    if "event" in text: add("Idempotency + Event Governance")
    if "recovery" in text or "failure" in text or "availability" in text:
        c["failure_strategy"]["strategy"]="timeouts, retries, health checks, backup, multi-zone recovery and tested disaster recovery"
        add("Multi-Zone / Disaster Recovery Boundary")
    if changed:
        c["refinement_iteration"]=iteration
        c["refinement_notes"].append(f"Iteration {iteration}: evidence-driven mutation added {', '.join(changed)}")
    return changed

def create_challenger(champion, profile, iteration):
    """Create a traceable challenger from the current champion instead of accepting a local optimum."""
    c=copy.deepcopy(champion)
    c["candidate_id"]=f"challenger-{uuid.uuid4().hex[:12]}"
    c["name"]=f"{champion['name']} — Iteration {iteration} Challenger"
    c["refinement_iteration"]=iteration
    c["is_pareto_optimal"]=False
    c["dominated"]=False
    c["verified"]=False
    c["critique_findings"]=[]
    c["verification_issues"]=[]
    c["requirement_coverage"]={}
    _improve_candidate(c,profile,iteration)
    if "Resilience Guardrails" not in c["components"]:
        c["components"].append("Resilience Guardrails")
        c["refinement_notes"].append(f"Iteration {iteration}: challenger generated from champion")
    return c

def refine(candidates,profile,max_iterations):
    # Kept for compatibility; orchestration now performs one evidence-driven mutation per round.
    history=[]
    for it in range(1,max_iterations+1):
        changed=[]
        for c in candidates: changed.extend([c["candidate_id"]] if _improve_candidate(c,profile,it) else [])
        history.append({"iteration":it,"action":"Adversarial critique → evidence-driven mutation → re-evaluation","affected_candidates":list(dict.fromkeys(changed))})
        if not changed: break
    return candidates,history
