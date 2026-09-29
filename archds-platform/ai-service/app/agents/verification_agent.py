def verify(candidates,profile):
    reqs=profile.functional_requirements+profile.non_functional_requirements
    passed=0
    for c in candidates:
        issues=[f["description"] for f in c.get("critique_findings",[])]
        coverage={}
        text=(c["description"]+" "+" ".join(c["components"]+c["relations"]+c["communication_patterns"]+list(c["tech_stack"].values()))).lower()
        for i,r in enumerate(reqs,1):
            words=[w for w in r.lower().replace(","," ").split() if len(w)>=5][:7]
            semantic_hit=any(w in text or w.rstrip("s") in text for w in words) if words else True
            low=r.lower()
            driver_hit=("scale" in low and c["pattern_key"] in ("microservices","event_driven","cqrs","hybrid","serverless")) or ("security" in low and "identity" in text) or ("real-time" in low and "realtime" in text) or ("availability" in low and c["scores"]["availability"]>=80) or ("audit" in low and c["pattern_key"] in ("cqrs","event_driven","hybrid"))
            coverage[f"R{i}"]=bool(semantic_hit or driver_hit)
            if not coverage[f"R{i}"]: issues.append(f"Requirement R{i} is not clearly traceable to a design element.")
        if c["pattern_key"] in ("event_driven","cqrs","hybrid") and "Message Broker / Event Log" not in c["components"]: issues.append("Event architecture lacks an explicit broker/event log.")
        c["requirement_coverage"]=coverage; c["verification_issues"]=list(dict.fromkeys(issues)); c["verified"]=not any("HIGH" in str(x) for x in c.get("critique_findings",[])) and len(c["verification_issues"])<=2
        if c["verified"]: passed+=1
    return candidates,{"verified_candidates":passed,"total_candidates":len(candidates),"all_candidates_verified":passed==len(candidates),"critical_findings":sum(sum(1 for f in c.get("critique_findings",[]) if f["severity"]=="HIGH") for c in candidates)}
