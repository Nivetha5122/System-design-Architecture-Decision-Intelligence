import re
import uuid
from ..knowledge_base import PATTERNS

DB_ALIASES = {
    "postgresql": "PostgreSQL", "postgres": "PostgreSQL", "postgresql database": "PostgreSQL",
    "mysql": "MySQL", "mariadb": "MariaDB", "oracle": "Oracle Database",
    "sql server": "SQL Server", "mssql": "SQL Server", "sqlite": "SQLite",
    "mongodb": "MongoDB", "mongo": "MongoDB", "dynamodb": "DynamoDB",
    "cassandra": "Cassandra", "couchbase": "Couchbase", "firestore": "Firestore",
    "redis": "Redis", "elasticsearch": "Elasticsearch", "opensearch": "OpenSearch",
    "neo4j": "Neo4j", "hbase": "HBase", "influxdb": "InfluxDB", "timescaledb": "TimescaleDB",
}
FRAMEWORK_ALIASES = {
    "react": "React", "react.js": "React", "angular": "Angular", "vue": "Vue",
    "next.js": "Next.js", "nextjs": "Next.js", "svelte": "Svelte",
    "spring boot": "Spring Boot", "springboot": "Spring Boot", "fastapi": "FastAPI",
    "django": "Django", "flask": "Flask", "node.js": "Node.js", "nodejs": "Node.js",
    "express": "Express.js", "nestjs": "NestJS", "asp.net": "ASP.NET Core",
    ".net": ".NET", "dotnet": ".NET", "java": "Java", "python": "Python",
    "kotlin": "Kotlin", "go": "Go", "golang": "Go", "c#": "C#",
}
MESSAGE_ALIASES={"kafka":"Kafka","rabbitmq":"RabbitMQ","rabbit mq":"RabbitMQ","pulsar":"Apache Pulsar","nats":"NATS","sqs":"Amazon SQS","pubsub":"Pub/Sub"}


def _choose(profile,n):
    tags=set(profile.tags); ranked=[]
    workload=" ".join(profile.dependencies+profile.functional_requirements+profile.drivers+profile.non_functional_requirements).lower()
    simple_low=not ("scalability" in tags or "realtime" in tags or "availability" in tags) and any(x in workload for x in ("500","simple","small","low cost"))
    fit={k:0 for k in PATTERNS}
    for k,p in PATTERNS.items(): fit[k]+=sum(3 for t in p["tags"] if t in tags)
    if not tags: fit["modular_monolith"]+=8; fit["layered"]+=5
    if simple_low: fit["modular_monolith"]+=18; fit["layered"]+=10; fit["serverless"]-=10; fit["microservices"]-=12; fit["event_driven"]-=12
    if "scalability" in tags: fit["microservices"]+=10; fit["event_driven"]+=9; fit["hybrid"]+=8
    if "realtime" in tags or "async" in tags: fit["event_driven"]+=10; fit["hybrid"]+=7
    if "security" in tags or "auditability" in tags: fit["cqrs"]+=6; fit["microservices"]+=4; fit["hybrid"]+=4
    if "bursty" in tags or "cost_sensitive" in tags: fit["serverless"]+=7
    if "domain" in tags or "maintainability" in tags: fit["clean_hexagonal"]+=7; fit["modular_monolith"]+=5
    if "iot" in tags: fit["event_driven"]+=10
    if any("payment" in x.lower() or "transaction" in x.lower() for x in profile.functional_requirements):
        fit["microservices"]+=3; fit["modular_monolith"]+=2
    return [k for k,_ in sorted(fit.items(),key=lambda x:(x[1],-list(PATTERNS).index(x[0])),reverse=True)][:n]


def _all_text(profile):
    return " ".join(profile.technology_preferences+profile.functional_requirements+profile.non_functional_requirements+profile.constraints+[profile.budget or "",profile.expected_users or ""]).lower()


def _explicit_tokens(profile, aliases):
    text=_all_text(profile)
    found=[]
    # Longest first avoids matching 'sql' inside 'sql server'.
    for token,label in sorted(aliases.items(), key=lambda x:-len(x[0])):
        if re.search(r"(?<![a-z0-9])"+re.escape(token)+r"(?![a-z0-9])", text):
            if label not in found: found.append(label)
    return found


def _data_plan(profile):
    text=_all_text(profile)
    explicit=_explicit_tokens(profile,DB_ALIASES)
    plan=list(explicit)
    evidence={db:[f"Explicit technology/data requirement detected: {db}."] for db in explicit}
    explicit_db=bool(explicit)
    relational_context = " ".join(profile.technology_preferences + profile.functional_requirements + profile.constraints).lower()
    if re.search(r"\bsql\b|relational|relational database", relational_context) and not any(x in plan for x in ["PostgreSQL","MySQL","MariaDB","Oracle Database","SQL Server","SQLite"]):
        plan.append("SQL Relational Database")
        evidence["SQL Relational Database"]=["The requirements specify SQL/relational storage without naming a vendor; the vendor remains a user decision."]
    if re.search(r"document|flexible schema|json document|catalog metadata", text) and not any(x in plan for x in ["MongoDB","DynamoDB","Couchbase","Firestore"]):
        plan.append("Document Database")
        evidence["Document Database"]=["Document-oriented metadata is indicated; a document store is an additional candidate, not a mandatory choice."]
    if re.search(r"video|image|file|media|object storage|blob|large file", text):
        plan.append("S3-compatible Object Storage")
        evidence["S3-compatible Object Storage"]=["File/media persistence is indicated; object storage is recommended for binary content rather than storing large files in relational rows."]
    if "iot" in profile.tags or re.search(r"telemetry|time[- ]series|sensor data", text):
        if not any(x in plan for x in ["InfluxDB","TimescaleDB"]): plan.append("TimescaleDB")
        evidence.setdefault("TimescaleDB",[]).append("Time-series telemetry is indicated; TimescaleDB is recommended for time-indexed measurements alongside relational entities.")
    if "read_heavy" in profile.tags and not any("search" in x.lower() for x in plan):
        if re.search(r"full[- ]text|fuzzy search|search across|product search|doctor search|catalog search", text):
            plan.append("OpenSearch")
            evidence["OpenSearch"]=["Full-text or catalogue search is indicated; OpenSearch is recommended as a search index, not as the transactional system of record."]
    # A concrete relational default for transactional/business entities, unless the user explicitly selected a database.
    if not explicit_db and not any(x in plan for x in ("SQL Relational Database", "Document Database", "PostgreSQL", "MySQL", "MariaDB", "Oracle Database", "SQL Server", "SQLite")):
        if any(re.search(r"\b"+re.escape(x)+r"\b", text) for x in ("store","save","persist","record","register","order","payment","data","user","account","patient","doctor","appointment","booking","inventory","product","student","application")):
            plan.insert(0,"PostgreSQL")
            evidence["PostgreSQL"]=["Recommended default system of record for structured business entities and transactional workflows; revise if workload or organizational constraints indicate otherwise."]
    if ("scalability" in profile.tags or "low_latency" in profile.tags or "read_heavy" in profile.tags or "bursty" in profile.tags) and "Redis" not in plan:
        plan.append("Redis")
        evidence["Redis"]=["Cache is recommended from detected scale, latency, read-heavy, or bursty-workload signals; use cache-aside with TTLs and invalidation safeguards."]
    return list(dict.fromkeys(plan)), evidence


def _framework_plan(profile):
    text=_all_text(profile)
    explicit=_explicit_tokens(profile,FRAMEWORK_ALIASES)
    out=[]; evidence={}
    for x in explicit:
        out.append(x); evidence[x]=[f"Explicit framework/language preference detected: {x}."]
    low=text.lower()
    if not any(x in out for x in ["React","Angular","Vue","Next.js","Svelte"]) and re.search(r"web|browser|portal|frontend|mobile|platform|application|system", low):
        out.append("React")
        evidence["React"]=["Recommended web UI default for an interactive browser-based application; replace if the team or deployment constraints require another frontend."]
    backend_frameworks=["Spring Boot","FastAPI","Django","Flask","Node.js","Express.js","NestJS","ASP.NET Core",".NET"]
    if not any(x in out for x in backend_frameworks):
        if any(x in low for x in ("machine learning","ml model","data science","prediction","fraud detection","analytics pipeline","ai-powered","recommendation engine")):
            out.append("FastAPI")
            evidence["FastAPI"]=["Recommended Python API framework because the domain description indicates analytics, ML, prediction, or AI integration."]
        elif any(x in low for x in ("healthcare","hospital","patient","doctor","appointment","banking","financial","payment","transaction","inventory","order management","enterprise")):
            out.append("Spring Boot")
            evidence["Spring Boot"]=["Recommended backend framework for transactional workflows, explicit service boundaries, validation, and security integration."]
        else:
            out.append("FastAPI")
            evidence["FastAPI"]=["Recommended lightweight API default for the short project brief; confirm against team skills and deployment constraints."]
    return list(dict.fromkeys(out)), evidence


def _messaging_plan(profile):
    text=_all_text(profile); explicit=_explicit_tokens(profile,MESSAGE_ALIASES)
    ev={x:[f"Explicit messaging technology preference detected: {x}."] for x in explicit}
    if explicit: return explicit,ev
    low=text.lower()
    if "iot" in profile.tags or any(x in low for x in ("telemetry stream","event stream","millions of events","high-volume events","stream processing")):
        return ["Apache Kafka"],{"Apache Kafka":["Recommended for durable high-volume event streams or telemetry; operational overhead is higher than a lightweight task queue."]}
    if "async" in profile.tags or "realtime" in profile.tags or any(x in low for x in ("appointment","booking","order","payment","notification","email","sms","background job")):
        return ["RabbitMQ"],{"RabbitMQ":["Recommended for reliable asynchronous business workflows such as notifications and background tasks; use idempotent consumers and bounded retries."]}
    return [],{}

def _capability_from_requirement(req, idx):
    low=req.lower()
    patterns=[
        (r"\b(register|registration|onboard|enrol)\b.*\b(user|patient|student|customer|member|account)", "Identity & Registration"),
        (r"\b(auth|login|authorize|access control|role)\b", "Identity & Access"),
        (r"\b(search|filter|discover|browse)\b", "Search & Discovery"),
        (r"\b(payment|pay|billing|invoice|transaction)\b", "Payment & Transaction Processing"),
        (r"\b(order|purchase|checkout|cart)\b", "Order & Checkout"),
        (r"\b(recommend|personaliz|suggest)\b", "Recommendation & Personalization"),
        (r"\b(notif|alert|email|sms|message)\b", "Notification & Alerting"),
        (r"\b(track|tracking|dispatch|delivery|location)\b", "Tracking & Dispatch"),
        (r"\b(sensor|telemetry|iot|device|stream)\b", "Telemetry & Event Ingestion"),
        (r"\b(report|dashboard|analytics|metric|monitor)\b", "Analytics & Reporting"),
        (r"\b(file|document|image|video|media|upload)\b", "Media & File Processing"),
        (r"\b(audit|ledger|history|compliance)\b", "Audit & Compliance"),
        (r"\b(schedule|appointment|booking|reservation)\b", "Scheduling & Booking"),
        (r"\b(inventory|stock|warehouse)\b", "Inventory & Resource Management"),
        (r"\b(fraud|anomal|risk|detect)\b", "Risk & Anomaly Detection"),
    ]
    for pat,label in patterns:
        if re.search(pat,low): return label
    stop={"the","system","shall","should","must","will","provide","support","allow","enable","users","user","data","application","platform","service","process","incoming","current","based","using","with","from","into","and","for","to","of","a","an","be","is","are","can","able"}
    words=re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}",low); chosen=[]
    for w in words:
        if w not in stop and w not in chosen: chosen.append(w)
        if len(chosen)>=3: break
    return " ".join(x.title() for x in chosen) or f"Business Capability {idx}"


def _capabilities(profile):
    out=[]; seen=set()
    for i,r in enumerate(profile.functional_requirements,1):
        label=_capability_from_requirement(r,i)
        if label in seen:
            for item in out:
                if item["label"]==label and f"R{i}" not in item["requirements"]: item["requirements"].append(f"R{i}")
        else:
            out.append({"label":label,"requirements":[f"R{i}"],"requirement":r}); seen.add(label)
    return out


def generate(profile,retrieved,n):
    keys=_choose(profile,n); out=[]; tags=set(profile.tags); capabilities=_capabilities(profile)
    data_plan,data_evidence=_data_plan(profile); frameworks,framework_evidence=_framework_plan(profile); messaging,messaging_evidence=_messaging_plan(profile)
    for i,k in enumerate(keys,1):
        p=PATTERNS[k]; comps=["Web / Mobile Client"] if any(x.lower().startswith(("web","mobile","react","angular","vue")) for x in frameworks) or any(x in _all_text(profile) for x in ("web","mobile","browser","portal")) else ["Client / Consumer"]
        if k in ("microservices","event_driven","cqrs","hybrid"): comps += ["API Gateway / Edge","Identity & Access","Domain Services","Observability"]
        elif k=="serverless": comps += ["API Gateway","Functions","Identity Provider","Monitoring"]
        else: comps += ["Application Modules","Identity & Access"]
        if "realtime" in tags: comps += ["Realtime Gateway"]
        if messaging: comps += [messaging[0]]
        if messaging and messaging[0] in ("RabbitMQ", "Apache Kafka", "NATS", "Amazon SQS", "Pub/Sub", "Apache Pulsar"):
            comps += ["Idempotency + Event Governance", "Dead-Letter Queue / Bounded Retry Policy"]
        if "Redis" in data_plan: comps += ["Redis Cache / Cache-Aside"]
        if "scalability" in tags or "bursty" in tags:
            comps += ["Rate Limiting / Admission Control", "Horizontal Scaling / Load Balancing"]
        if "auditability" in tags: comps += ["Audit & Compliance"]
        if "security" in tags: comps += ["Security Policy / Secrets Boundary"]
        if "availability" in tags: comps += ["Resilience Guardrails", "Disaster Recovery Boundary"]
        if "read_heavy" in tags: comps += ["Search / Read Optimization"]
        if "iot" in tags: comps += ["Telemetry Ingestion"]
        comps += [x["label"] for x in capabilities]
        comm=["HTTPS/REST"]
        if messaging: comm.append(f"{messaging[0]} asynchronous events")
        if "realtime" in tags: comm.append("WebSocket / SSE")
        if k=="serverless": compute="Managed Functions"; api="API Gateway"
        elif any(x in frameworks for x in ["Spring Boot","FastAPI","Django","Flask","Node.js","Express.js","NestJS","ASP.NET Core",".NET"]): compute=next(x for x in frameworks if x in ["Spring Boot","FastAPI","Django","Flask","Node.js","Express.js","NestJS","ASP.NET Core",".NET"]); api="REST/HTTPS"
        else: compute="FastAPI"; api="REST/HTTPS"
        tech={"frontend":next((x for x in frameworks if x in ["React","Angular","Vue","Next.js","Svelte"]),"React"),"api":api,"compute":compute}
        if data_plan: tech["data"]=", ".join(data_plan)
        if messaging: tech["messaging"]=", ".join(messaging)
        deployment={"topology":"single deployment" if k in ("layered","modular_monolith","clean_hexagonal") else "distributed services","regions":"single region unless availability/disaster requirements require more","scaling":"horizontal only where justified by stated workload drivers"}
        security={"identity":"centralized authentication and authorization","transport":"TLS","boundaries":"trust boundaries are derived from security requirements"}
        scaling={"strategy":"coarse-grained vertical/horizontal" if k in ("layered","modular_monolith","clean_hexagonal") else "independent horizontal scaling","triggered_by":profile.scale_drivers}
        failure={"strategy":"timeouts, retries and health checks","isolation":"module/service boundaries"}
        obs={"logs":"structured","metrics":"latency, throughput, errors","traces":"distributed tracing"}
        edge_name="API Gateway / Edge" if k in ("microservices","event_driven","cqrs","hybrid") else ("API Gateway" if k=="serverless" else "Application Modules")
        identity_name="Identity & Access" if k in ("microservices","event_driven","cqrs","hybrid") else ("Identity Provider" if k=="serverless" else "Identity & Access")
        domain_name="Domain Services" if k in ("microservices","event_driven","cqrs","hybrid") else ("Functions" if k=="serverless" else "Application Modules")
        relations=[f"{comps[0]} -> {edge_name}", f"{edge_name} -> {identity_name}"]
        if "Rate Limiting / Admission Control" in comps:
            relations.extend([f"{edge_name} -> Rate Limiting / Admission Control", f"Rate Limiting / Admission Control -> {domain_name}"])
        else:
            relations.append(f"{edge_name} -> {domain_name}")
        from collections import defaultdict
        component_requirements=defaultdict(list); component_evidence=defaultdict(list)
        for cap in capabilities:
            component_requirements[cap["label"]].extend(cap["requirements"]); component_evidence[cap["label"]].append(cap["requirement"]); relations.append(f"{domain_name} -> {cap['label']}")
        for d in data_plan:
            comps.append(d); component_requirements[d].extend([f"R{j}" for j in range(1,len(profile.functional_requirements)+1)])
            component_evidence[d].extend(data_evidence.get(d,[])); relations.append(f"{domain_name} -> {d}")
        if "Redis Cache / Cache-Aside" in comps:
            relations.extend([f"{domain_name} -> Redis Cache / Cache-Aside", "Redis Cache / Cache-Aside -> Redis"])
        if "Rate Limiting / Admission Control" in comps:
            relations.append(f"Rate Limiting / Admission Control -> Horizontal Scaling / Load Balancing")
        if messaging:
            component_requirements[messaging[0]].extend([f"R{j}" for j in range(1,len(profile.functional_requirements)+1)]); component_evidence[messaging[0]].extend(messaging_evidence.get(messaging[0],[])); relations.append(f"{domain_name} -> {messaging[0]}")
            if "Idempotency + Event Governance" in comps:
                relations.extend([f"{messaging[0]} -> Idempotency + Event Governance", f"{messaging[0]} -> Dead-Letter Queue / Bounded Retry Policy"])
            notification_component=next((x for x in comps if "Notification" in x or "Alerting" in x),None)
            if notification_component: relations.append(f"{messaging[0]} -> {notification_component}")
        if "read_heavy" in tags: relations.append(f"{domain_name} -> Search / Read Optimization")
        if "iot" in tags and "Telemetry Ingestion" in comps: relations.append(f"{domain_name} -> Telemetry Ingestion")
        if "realtime" in tags and "Realtime Gateway" in comps: relations.append(f"{domain_name} -> Realtime Gateway")
        if "Observability" in comps: relations.append(f"{domain_name} -> Observability")
        elif "Monitoring" in comps: relations.append(f"{domain_name} -> Monitoring")
        if "Audit & Compliance" in comps: relations.append(f"{domain_name} -> Audit & Compliance")
        if "Security Policy / Secrets Boundary" in comps: relations.append(f"{identity_name} -> Security Policy / Secrets Boundary")
        if "Resilience Guardrails" in comps: relations.append(f"{domain_name} -> Resilience Guardrails")
        nf_count=len(profile.non_functional_requirements); all_req_ids=[f"R{len(profile.functional_requirements)+j}" for j in range(1,nf_count+1)]
        for infra in ("Security Policy / Secrets Boundary","Resilience Guardrails","Disaster Recovery Boundary","Observability","Monitoring"):
            if infra in comps and all_req_ids: component_requirements[infra].extend(all_req_ids)
        functional_ids=[f"R{j}" for j in range(1,len(profile.functional_requirements)+1)]
        component_requirements[edge_name].extend(functional_ids); component_requirements[domain_name].extend(functional_ids)
        for fw in frameworks:
            comps.append(fw); component_requirements[fw].extend(functional_ids); component_evidence[fw].extend(framework_evidence.get(fw,[])); relations.append(f"{comps[0]} -> {fw}")
        component_requirements={k:list(dict.fromkeys(v)) for k,v in component_requirements.items()}
        component_evidence={k:list(dict.fromkeys(v)) for k,v in component_evidence.items()}
        tech_evidence={}
        for k2,v2 in data_evidence.items(): tech_evidence[k2]=list(dict.fromkeys(v2))
        for k2,v2 in framework_evidence.items(): tech_evidence[k2]=list(dict.fromkeys(v2))
        for k2,v2 in messaging_evidence.items(): tech_evidence[k2]=list(dict.fromkeys(v2))
        if "Redis Cache / Cache-Aside" in comps:
            tech_evidence["Redis Cache / Cache-Aside"]=["Cache-aside with TTL and explicit invalidation is recommended because the inferred workload contains scale, latency, burst, or read-heavy signals."]
        if "Rate Limiting / Admission Control" in comps:
            tech_evidence["Rate Limiting / Admission Control"]=["Admission control protects downstream services when request rates exceed the assumed safe operating envelope; thresholds must be load-tested."]
        if "Horizontal Scaling / Load Balancing" in comps:
            tech_evidence["Horizontal Scaling / Load Balancing"]=["Horizontal replicas and load balancing are recommended for inferred scale or burst drivers; actual capacity requires workload testing."]
        if "Dead-Letter Queue / Bounded Retry Policy" in comps:
            tech_evidence["Dead-Letter Queue / Bounded Retry Policy"]=["Bounded retries and a dead-letter path prevent repeatedly failing messages from blocking normal processing."]
        out.append({"candidate_id":f"cand-{uuid.uuid4().hex[:12]}","pattern_key":k,"name":p["name"],"description":f"Requirement-adapted {p['description']} The capability map is derived from {len(capabilities)} functional requirement(s) and tuned for drivers: {', '.join(profile.drivers[:5]) or 'the supplied business intent' }.","components":list(dict.fromkeys(comps)),"relations":list(dict.fromkeys(relations)),"data_stores":data_plan,"communication_patterns":comm,"deployment_model":deployment,"security_model":security,"scaling_strategy":scaling,"failure_strategy":failure,"observability":obs,"tech_stack":tech,"technology_evidence":tech_evidence,"advantages":p["pros"],"disadvantages":p["cons"],"assumptions":profile.assumptions,"component_requirements":component_requirements,"component_evidence":component_evidence})
    return out
