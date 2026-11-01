def explain(candidates,profile,optimization):
    out=[]
    best=max(candidates,key=lambda c:c["scores"]["weighted_total"])
    records=getattr(profile,"requirement_records",[]) or []
    descriptions={r.get("id"):r.get("description","") for r in records}
    for c in candidates:
        reasons=[]
        for a,w in profile.priority_weights.items():
            if w>=8: reasons.append(f"{a.replace('_',' ')} priority is {w}% and this candidate scores {c['scores'][a]:.0f}/100")
        evidence=[]
        for rid,comps in c.get("requirement_mappings",{}).items():
            if comps:
                evidence.append(f"{rid} is addressed by {', '.join(comps[:3])} because the requirement is: {descriptions.get(rid,'the supplied requirement')}")
        lead=(f"Selected because it provides the strongest evidence-backed fit for the supplied requirements. " if c["candidate_id"]==best["candidate_id"] else "Retained as an alternative because it offers a different trade-off against the same supplied requirements. ")
        rationale=lead+" ".join(reasons[:3])+" "+" ".join(evidence[:3])
        unresolved=sum(1 for f in c.get("critique_findings",[]) if f.get("severity")=="HIGH")
        conf=max(0.45,min(0.98,0.55+profile.architecture_readiness/250+c["scores"]["weighted_total"]/500+(.06 if c.get("verified") else 0)-.05*unresolved))
        strengths=[f"{x} — justified by the supplied requirement profile" for x in c.get("advantages",[])[:4]]
        tradeoffs=[f"{x} — accepted because it is the cost of satisfying the competing priorities" for x in c.get("disadvantages",[])[:4]]
        risks=[x.get("description",x.get("title","Unspecified review finding")) for x in c.get("critique_findings",[])[:4]]
        out.append({"candidate_id":c["candidate_id"],"rationale":rationale.strip(),"strengths":strengths,"tradeoffs":tradeoffs,"risks":risks,"assumptions":c.get("assumptions",[]),"confidence":round(conf,2),"change_factors":profile.drivers[:6],"evidence":evidence[:8]})
    return out
