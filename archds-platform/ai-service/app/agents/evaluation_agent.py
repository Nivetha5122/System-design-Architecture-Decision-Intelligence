from ..models import ATTRIBUTES

def evaluate(candidates,profile):
    tags=set(profile.tags); w=profile.priority_weights
    base={
    "modular_monolith":[78,60,84,82,86,92,78,94,90,74,92,86],"microservices":[88,95,88,91,88,70,93,58,52,92,52,48],"event_driven":[94,97,87,95,89,66,94,60,44,94,48,45],"clean_hexagonal":[77,65,93,87,95,88,96,84,86,82,86,65],"serverless":[87,94,84,82,88,93,91,92,65,85,94,58],"layered":[72,58,84,76,86,94,76,95,92,72,91,82],"cqrs":[90,95,90,94,88,62,95,56,42,94,50,47],"hybrid":[89,92,91,94,93,74,96,72,65,95,62,52]}
    for c in candidates:
        vals=base[c["pattern_key"]].copy()
        if "scalability" in tags: vals[1]+=6
        if "security" in tags: vals[2]+=5
        if "availability" in tags: vals[3]+=5; vals[4]+=5
        if "realtime" in tags: vals[0]+=5; vals[1]+=4
        if "auditability" in tags: vals[2]+=3; vals[3]+=4
        if "cost_sensitive" in tags: vals[7]+=7; vals[8]+=4
        if "cost_sensitive" in tags and not any(t in tags for t in ("scalability","realtime","availability")) and c["pattern_key"] in ("modular_monolith","layered","clean_hexagonal"):
            vals[7]+=8; vals[8]+=6; vals[5]+=4
        if "cost_sensitive" in tags and not any(t in tags for t in ("scalability","realtime","availability")) and c["pattern_key"] in ("serverless","microservices","event_driven","cqrs","hybrid"):
            vals[7]-=10; vals[8]-=5
        if "cost_sensitive" in tags and not any(t in tags for t in ("scalability","realtime","availability")) and c["pattern_key"] in ("modular_monolith","layered","clean_hexagonal"):
            vals[7]+=12; vals[8]+=8; vals[5]+=5
        if "cost_sensitive" in tags and not any(t in tags for t in ("scalability","realtime","availability")) and c["pattern_key"]=="modular_monolith":
            vals[0]+=5; vals[3]+=4; vals[4]+=3
        if "maintainability" in tags: vals[5]+=5
        if "bursty" in tags and c["pattern_key"]=="serverless": vals[7]+=5
        # Requirement-shape evidence: high-scale + real-time + availability favors
        # durable asynchronous/event-driven processing and independently scalable domains.
        if {"scalability","realtime","availability"}.issubset(tags):
            if c["pattern_key"]=="event_driven": vals[0]+=10; vals[1]+=10; vals[3]+=8
            if c["pattern_key"]=="hybrid": vals[1]+=7; vals[3]+=6
            if c["pattern_key"]=="serverless": vals[1]-=7; vals[3]-=5; vals[9]-=3
        # Financial/audit workloads explicitly reward durable transaction/audit structures.
        if "auditability" in tags and "security" in tags:
            if c["pattern_key"]=="cqrs": vals[2]+=5; vals[3]+=4; vals[1]+=3
            if c["pattern_key"]=="hybrid": vals[2]+=4; vals[3]+=3
            if c["pattern_key"]=="serverless": vals[2]-=3
        # Evidence-driven refinement bonuses: improvements are earned only when the
        # architecture explicitly contains the control introduced by critique.
        comp=set(c.get("components",[]))
        if "Security Policy / Secrets Boundary" in comp: vals[2]+=3
        if "Horizontal Scaling / Load Balancing" in comp: vals[1]+=3; vals[0]+=2
        if "Idempotency + Event Governance" in comp: vals[3]+=2; vals[9]+=2
        if "Multi-Zone / Disaster Recovery Boundary" in comp: vals[3]+=3; vals[4]+=4
        if "Resilience Guardrails" in comp: vals[3]+=1; vals[4]+=1
        vals=[max(0,min(100,v)) for v in vals]
        total=round(sum(vals[i]*w[a]/100 for i,a in enumerate(ATTRIBUTES)),2)
        c["scores"]={a:vals[i] for i,a in enumerate(ATTRIBUTES)}; c["scores"]["weighted_total"]=total
        c["score_reasons"]={a:f"{a.replace('_',' ').title()} reflects {c['pattern_key'].replace('_',' ')} fit against detected drivers {', '.join(profile.tags) or 'baseline'}." for a in ATTRIBUTES}
    return candidates
