import re
from ..models import RequirementInput, RequirementProfile, ATTRIBUTES

KEYWORDS = {
    "scalability": ["scale", "scalable", "scalability", "scaling", "concurrent", "traffic", "million", "high volume", "throughput", "peak load", "peak", "future growth", "traffic surge", "flash sale"],
    "security": ["secure", "security", "encrypt", "encryption", "pci", "hipaa", "privacy", "auth", "authentication", "authorization", "authenticate", "authorized", "fraud", "sensitive", "patient data", "personal data"],
    "realtime": ["real-time", "realtime", "live", "instant", "tracking", "low latency"],
    "async": ["asynchronous", "async", "event", "queue", "notification", "background", "stream", "email", "sms"],
    "availability": ["availability", "24/7", "uptime", "failover", "disaster", "99.9", "99.99", "resilient", "reliable", "recover"],
    "auditability": ["audit", "trace", "history", "compliance", "ledger", "non-repudiation", "audit log"],
    "read_heavy": ["read-heavy", "search", "analytics", "dashboard", "reporting", "browse", "catalog"],
    "bursty": ["burst", "spike", "unpredictable", "seasonal", "weekend", "flash sale", "traffic surge"],
    "domain": ["complex business rules", "domain", "workflow", "rules"],
    "low_latency": ["low latency", "latency", "milliseconds", "ms", "fast response"],
    "cost_sensitive": ["low budget", "cheap", "cost-effective", "cost", "budget", "affordable"],
    "iot": ["iot", "sensor", "device", "telemetry", "time-series"],
}

NFR_MARKERS = (
    "secure", "security", "privacy", "encrypt", "compliance", "audit", "available", "availability",
    "reliable", "reliability", "resilient", "scal", "traffic", "throughput", "latency", "performance",
    "fast", "concurrent", "cost", "budget", "maintain", "recover", "uptime", "99.9", "sensitive",
    "peak", "load", "response time", "fault tolerant", "high volume"
)
ACTION_MARKERS = (
    "register", "registration", "sign up", "login", "authenticate", "search", "browse", "book", "cancel", "schedule",
    "manage", "create", "update", "delete", "view", "track", "notify", "notification", "notifications", "send", "receive", "submit", "allow", "enable",
    "process", "pay", "payment", "order", "purchase", "upload", "download", "assign", "approve",
    "record", "store", "retrieve", "report", "detect", "recommend", "calculate", "monitor", "analyze",
    "analyse", "match", "apply", "review", "dispatch", "reserve", "check", "enrol", "enroll"
)


def _sentences(text):
    return [x.strip(" .\t-") for x in re.split(r"\n|;|(?<=[.!?])\s+", text or "") if x.strip(" .\t-")]


def _contains(text, words):
    low = text.lower()
    for word in words:
        if re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", low):
            return True
    return False


def _is_quality_sentence(sentence):
    low = sentence.lower()
    strong = ("secure", "security", "privacy", "encrypt", "compliance", "audit",
              "reliable", "reliability", "resilient", "scal", "traffic", "throughput", "latency", "performance",
              "fast", "concurrent", "cost", "budget", "maintain", "recover", "uptime", "99.9", "sensitive",
              "peak", "load", "response time", "requests per second", "fault tolerant", "high volume", "protect", "transactional consistency")
    if any(word in low for word in strong):
        return True
    # Bare domain terms such as "doctor availability" are not NFRs without a quality target.
    return bool(re.search(r"\b(high|low|target|minimum|99\.9[0-9]?|99\.99)\s+availability\b|\bavailability\s+(target|sla|of at least)\b", low))


def _domain_defaults(text):
    """Conservative domain-informed requirements; explicitly labelled as inferred."""
    low = text.lower()
    fr, nfr = [], []
    if any(x in low for x in ("healthcare", "hospital", "patient", "doctor", "medical", "appointment")):
        fr += ["Users can register and manage their profiles.", "Patients can search for providers and create, view, or cancel appointments.", "Providers can manage availability and review scheduled appointments.", "The system can send appointment notifications."]
        nfr += ["Protect personal and health information with authentication, authorization, and encryption.", "Maintain transactional consistency when booking or cancelling appointments.", "Record security-relevant and appointment changes for auditability.", "Remain reliable during peak booking periods and recover from service failures."]
    elif any(x in low for x in ("e-commerce", "ecommerce", "shopping", "online store", "product catalog", "retail")):
        fr += ["Customers can browse products and manage a shopping cart.", "Customers can place orders and view order status.", "The system can process payments and update inventory.", "The system can send order and delivery notifications."]
        nfr += ["Protect customer and payment-related information.", "Maintain consistency between orders, payments, and inventory updates.", "Handle traffic spikes during promotions without uncontrolled overload.", "Record order and payment events for support and audit purposes."]
    elif any(x in low for x in ("banking", "financial", "payment", "fraud", "transaction", "wallet")):
        fr += ["Users can submit and review authorized financial transactions.", "The system can maintain transaction records and status.", "The system can flag suspicious transactions for review."]
        nfr += ["Enforce strong authentication, authorization, and protection of sensitive data.", "Preserve transaction integrity and prevent duplicate processing.", "Maintain tamper-evident audit records for critical operations.", "Handle failures without silently losing or duplicating transactions."]
    elif any(x in low for x in ("recruitment", "hiring", "resume", "job portal", "applicant")):
        fr += ["Applicants can create profiles and submit applications.", "Recruiters can manage job openings and review applicants.", "The system can track application status and communicate updates."]
        nfr += ["Protect applicant personal information and restrict access by role.", "Keep application decisions traceable and reviewable.", "Provide maintainable workflows as recruitment stages change."]
    elif any(x in low for x in ("student", "campus", "attendance", "examination", "exam platform", "learning management")):
        fr += ["Users can authenticate and access role-appropriate functions.", "Students can access the relevant academic records or activities.", "Authorized staff can manage records and review reports."]
        nfr += ["Protect student records with role-based access control.", "Maintain data consistency for submitted academic records.", "Provide maintainable and observable application services."]
    elif any(x in low for x in ("iot", "sensor", "telemetry", "device monitoring")):
        fr += ["The system can ingest measurements from connected devices.", "The system can store and query device observations.", "The system can identify and report abnormal readings."]
        nfr += ["Process incoming telemetry reliably under changing event rates.", "Support time-series retrieval and monitoring of ingestion failures.", "Protect device identity and data transmission."]
    return fr, nfr


def _derived_weights(tags, f, nf, constraints, description):
    """Produce normalized objective priorities from requirement evidence, not user scoring."""
    weights = {a: 5.0 for a in ATTRIBUTES}
    text = " ".join(f + nf + constraints + [description or ""]).lower()
    mapping = {
        "scalability": "scalability", "security": "security", "availability": "availability",
        "realtime": "performance", "low_latency": "performance", "auditability": "reliability",
        "read_heavy": "performance", "cost_sensitive": "cost", "bursty": "scalability",
        "async": "reliability", "iot": "scalability", "domain": "maintainability"
    }
    for tag in tags:
        attr = mapping.get(tag)
        if attr: weights[attr] += 8.0
    # Business-domain and workload signals carry explicit, explainable priority boosts.
    if any(x in text for x in ("payment", "financial", "banking", "fraud", "patient", "healthcare", "sensitive data")):
        weights["security"] += 9
        weights["reliability"] += 5
    if any(x in text for x in ("booking", "appointment", "inventory", "payment", "order", "transaction")):
        weights["reliability"] += 5
        weights["availability"] += 3
    if any(x in text for x in ("traffic spike", "traffic surge", "peak", "flash sale", "million", "high traffic", "concurrent")):
        weights["scalability"] += 9
        weights["performance"] += 5
    if any(x in text for x in ("low cost", "low budget", "affordable", "cost-sensitive")):
        weights["cost"] += 10
        weights["complexity"] += 4
    total = sum(weights.values())
    result = {a: int(round(v * 100 / total)) for a, v in weights.items()}
    diff = 100 - sum(result.values())
    result["performance"] += diff
    return result


def analyze(req: RequirementInput) -> RequirementProfile:
    description = (req.description or "").strip()
    context = f"{req.project_name}. {description}"
    sentences = _sentences(description)
    f = list(dict.fromkeys(x.strip() for x in req.functional_requirements if x.strip()))
    nf = list(dict.fromkeys(x.strip() for x in req.non_functional_requirements if x.strip()))
    cons = list(dict.fromkeys(x.strip() for x in req.constraints if x.strip()))
    tech = list(dict.fromkeys(x.strip() for x in req.technology_preferences if x.strip()))
    assumptions = []
    ambiguities = []
    questions = []

    # Classify each natural-language sentence by signals instead of discarding mixed sentences.
    if not f:
        for sentence in sentences:
            if _contains(sentence, ACTION_MARKERS):
                f.append(sentence)
    if not nf:
        for sentence in sentences:
            if _is_quality_sentence(sentence):
                nf.append(sentence)
    inferred_f, inferred_nf = _domain_defaults(context)
    if not f and inferred_f:
        f = inferred_f[:]
        assumptions.append("Functional capabilities were inferred from the project domain because the description did not state them explicitly.")
    elif inferred_f:
        # Add only domain capabilities not already represented by the supplied description.
        existing = " ".join(f).lower()
        for item in inferred_f:
            key_terms = [w for w in re.findall(r"[a-z]{4,}", item.lower()) if w not in {"users", "system", "their", "from", "with", "when", "create", "view"}]
            if key_terms and not any(term in existing for term in key_terms[:2]):
                f.append(item)
    if not nf and inferred_nf:
        nf = inferred_nf[:]
        assumptions.append("Domain-appropriate quality requirements were inferred and should be reviewed by the project owner.")
    elif inferred_nf:
        existing = " ".join(nf).lower()
        for item in inferred_nf:
            key_terms = [w for w in re.findall(r"[a-z]{4,}", item.lower()) if w not in {"system", "with", "from", "when", "should", "appropriate"}]
            if key_terms and not any(term in existing for term in key_terms[:2]):
                nf.append(item)
        assumptions.append("Additional domain-specific quality safeguards were inferred and should be reviewed by the project owner.")
    if not f and description:
        f = [description]
        assumptions.append("The short description was retained as a provisional functional requirement because no clearer business action could be extracted.")
    # Every system gets a modest engineering baseline; domain-specific safeguards are added above.
    baseline = ["Keep modules maintainable and testable.", "Record operational errors and key service health metrics.", "Validate user input and handle failures explicitly."]
    for item in baseline:
        if not any(item.split()[1].lower() in x.lower() for x in nf):
            nf.append(item)
    if not req.expected_users:
        assumptions.append("Peak workload was not supplied; capacity recommendations use qualitative workload signals rather than a fabricated user count.")
    if not req.budget:
        assumptions.append("No budget was supplied; cost and operational complexity are compared qualitatively.")
    if not tech:
        assumptions.append("Technology choices are recommendations inferred from the domain and quality drivers, not user-mandated choices.")

    raw_text = " ".join([context] + f + nf + cons + tech + [req.expected_users or "", req.budget or ""]).lower()
    tags = []
    for tag, words in KEYWORDS.items():
        if _contains(raw_text, words): tags.append(tag)
    if re.search(r"\b(no|not|without|never)\s+(real-time|realtime|live)\b", raw_text):
        tags = [t for t in tags if t != "realtime"]
    if re.search(r"\b(normal|standard|ordinary|basic)\s+availability\b", raw_text):
        tags = [t for t in tags if t != "availability"]
    # Domain-specific risk signals are inferred, but explicitly disclosed.
    low = context.lower()
    if any(x in low for x in ("healthcare", "hospital", "patient", "doctor", "medical")):
        for t in ("security", "auditability", "availability"):
            if t not in tags: tags.append(t)
        if not any("health information" in x.lower() or "personal and health" in x.lower() for x in nf):
            nf.append("Protect personal and health information with appropriate access control.")
            assumptions.append("Healthcare privacy protection was inferred from the domain.")
    if any(x in low for x in ("payment", "financial", "banking", "fraud", "transaction")):
        for t in ("security", "auditability"):
            if t not in tags: tags.append(t)
    if any(x in low for x in ("booking", "appointment", "reservation", "order", "inventory")) and "availability" not in tags:
        tags.append("availability")

    drivers = []
    for item in nf + cons:
        if item not in drivers: drivers.append(item)
    for tag, label in (("scalability", "Capacity and independent scaling"), ("security", "Security and trust boundaries"),
                       ("realtime", "Real-time responsiveness"), ("availability", "Availability and fault tolerance"),
                       ("auditability", "Auditability and evidence retention"), ("read_heavy", "Read efficiency and search"),
                       ("async", "Asynchronous workload decoupling"), ("cost_sensitive", "Cost and operational simplicity")):
        if tag in tags: drivers.append(label)
    drivers = list(dict.fromkeys(drivers))[:20]

    contradictions = []
    if "cost_sensitive" in tags and "availability" in tags and any(x in raw_text for x in ("five regions", "5 regions", "multi-region", "active-active")):
        contradictions.append({"left": "Low infrastructure cost", "right": "Multi-region high availability", "severity": "HIGH", "resolution_options": ["Prioritize availability", "Prioritize cost", "Keep both with an explicit budget ceiling"]})

    total = max(1, len(f) + len(nf) + len(cons))
    completeness = min(100, round((len(f) + 1.2 * len(nf) + 0.7 * len(cons)) / max(1, total + 3) * 100, 1))
    specificity = min(100, 55 + 10 * bool(req.expected_users) + 10 * bool(cons) + 10 * bool(tech) + 10 * bool(req.budget))
    consistency = 100 if not contradictions else 65
    # Missing numeric workload/SLA are assumptions, not blockers for initial architecture synthesis.
    if not req.expected_users: ambiguities.append("Peak workload is qualitative because no user or request-rate measure was supplied")
    if not any(x in raw_text for x in ("99.9", "uptime", "sla", "availability target")):
        ambiguities.append("No numeric availability target was supplied")
    ambiguity = min(100, round((len(ambiguities) + len(contradictions) * 2) * 8, 1))
    readiness = round(max(0, min(100, 0.35 * completeness + 0.25 * specificity + 0.25 * consistency + 0.15 * (100 - ambiguity))), 1)

    derived = _derived_weights(tags, f, nf, cons, context)
    # The agents determine weights by default. Explicit custom weights are an optional override only.
    if req.quality_weights is not None:
        user_w = req.quality_weights.as_dict()
        final_w = {a: int(round(0.75 * derived[a] + 0.25 * user_w[a])) for a in ATTRIBUTES}
        final_w["performance"] += 100 - sum(final_w.values())
        assumptions.append("Custom objective priorities were supplied; they influence the requirement-derived weights by 25%.")
        weight_source = "requirement-derived with optional 25% user priority influence"
    else:
        final_w = dict(derived)
        weight_source = "requirement-derived"
    assumptions.append(f"Objective weights source: {weight_source}.")

    return RequirementProfile(
        functional_requirements=list(dict.fromkeys(f)), non_functional_requirements=list(dict.fromkeys(nf)),
        constraints=cons, technology_preferences=tech, expected_users=req.expected_users, budget=req.budget,
        drivers=drivers, tags=list(dict.fromkeys(tags)), assumptions=list(dict.fromkeys(assumptions)),
        ambiguities=ambiguities, contradictions=contradictions,
        dependencies=[f"Expected workload: {req.expected_users}"] if req.expected_users else [],
        security_drivers=[x for x in nf + cons if any(k in x.lower() for k in ("security", "privacy", "encrypt", "compliance", "auth", "pci", "hipaa", "patient"))],
        scale_drivers=[x for x in f + nf if any(k in x.lower() for k in ("scale", "concurrent", "traffic", "throughput", "million", "peak"))],
        priority_weights=final_w, derived_weights=derived, completeness=completeness, specificity=specificity,
        consistency=consistency, ambiguity=ambiguity, architecture_readiness=readiness,
        clarification_questions=list(dict.fromkeys(questions))
    )
