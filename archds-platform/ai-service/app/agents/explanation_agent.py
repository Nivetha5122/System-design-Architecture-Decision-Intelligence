def explain(candidates,profile,optimization):
    out=[]; best=max(candidates,key=lambda c:c["scores"]["weighted_total"])
    for c in candidates:
        reasons=[]
        for a,w in profile.priority_weights.items():
            if w>=8: reasons.append(f"{a.replace('_',' ')} priority {w}% is supported by a score of {c['scores'][a]:.0f}")
        rationale=(f"Selected because it best matches the requirement-derived drivers ({', '.join(profile.tags) or 'baseline'}) and the final objective weights. " if c["candidate_id"]==best["candidate_id"] else "Retained as a meaningful trade-off alternative. ")+"; ".join(reasons[:4])+"."
        unresolved=sum(1 for f in c.get("critique_findings",[]) if f["severity"]=="HIGH")
        conf=max(0.45,min(0.98,0.55+profile.architecture_readiness/250+c["scores"]["weighted_total"]/500+(.06 if c["verified"] else 0)-.05*unresolved))
        out.append({"candidate_id":c["candidate_id"],"rationale":rationale,"strengths":c["advantages"][:4],"tradeoffs":c["disadvantages"][:4],"risks":[x["description"] for x in c.get("critique_findings",[])[:4]],"assumptions":c["assumptions"],"confidence":round(conf,2),"change_factors":profile.drivers[:6]})
    return out
