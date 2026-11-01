def critique(candidates,profile):
    tags=set(profile.tags)
    for c in candidates:
        findings=[]; text=" ".join(c["components"]+c["relations"]+list(c["tech_stack"].values())).lower()
        def add(sev,title,desc,reqs): findings.append({"severity":sev,"title":title,"description":desc,"affected_requirements":reqs})
        if "security" in tags and "identity" not in text: add("HIGH","Missing explicit identity boundary","Security is a driver but the candidate does not expose a clear identity boundary.",[])
        if "scalability" in tags and c["pattern_key"] in ("layered","modular_monolith") and "Horizontal Scaling / Load Balancing" not in c["components"]: add("HIGH","Coarse scaling boundary","The primary deployment unit may become a bottleneck at the stated workload.",[])
        if "realtime" in tags and "realtime gateway" not in text: add("MEDIUM","Real-time path underspecified","The design should expose a dedicated low-latency delivery path.",[])
        if c["pattern_key"] in ("event_driven","cqrs","hybrid") and "broker" not in text: add("HIGH","Event durability unspecified","Event-oriented communication needs durable delivery, ordering and idempotency controls.",[])
        if "availability" in tags and c["deployment_model"].get("regions")=="single region unless availability driver requires multi-region": add("MEDIUM","Recovery topology needs explicit target","Availability requirements need a tested failure domain and recovery strategy.",[])
        if c["scores"]["complexity"]<50: add("MEDIUM","Operational complexity","Distributed coordination increases operational burden and requires strong observability.",[])
        c["critique_findings"]=findings
    return candidates
