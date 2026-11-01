"""Requirement-grounded architecture-pattern retrieval with explainable lexical ranking.

The default path stays offline-friendly. It combines normalized token/bigram similarity,
architecture-driver signals, explicit constraint matches and optional semantic reranking.
"""
import math
import os
import re
from collections import Counter
from ..knowledge_base import KNOWLEDGE, PATTERNS

TOKEN_ALIASES = {
    "high availability": "availability", "uptime": "availability", "fault tolerance": "resilience",
    "fault tolerant": "resilience", "disaster recovery": "recovery", "failover": "resilience",
    "event streaming": "event", "message queue": "async", "asynchronous": "async",
    "low latency": "performance", "response time": "performance", "throughput": "scalability",
    "traffic spike": "bursty", "traffic surge": "bursty", "flash sale": "bursty",
    "read heavy": "read_heavy", "read-heavy": "read_heavy", "audit trail": "auditability",
    "immutable history": "auditability", "independent deployment": "independent_deployment",
    "modular monolith": "modular_monolith", "micro services": "microservices",
    "server less": "serverless", "command query responsibility segregation": "cqrs",
    "clean architecture": "clean_hexagonal", "hexagonal architecture": "clean_hexagonal",
    "low cost": "cost_sensitive", "budget constrained": "cost_sensitive",
    "sensor data": "iot", "time series": "iot", "real time": "realtime",
}
STOP = {"the","and","for","with","from","into","that","this","must","should","shall","system","platform","application","service","using","use","provide","support","allow","enable","user","users","data","based","including","include","such","than","then","also","can","will","are","is","be","to","of","in","on","by","as","or","an","a"}

def _normalize(text):
    value = str(text or "").lower().replace("_", " ")
    for phrase, canonical in sorted(TOKEN_ALIASES.items(), key=lambda x: -len(x[0])):
        value = re.sub(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", " " + canonical.replace("_", " ") + " ", value)
    return value

def _tokens(text):
    words = [w for w in re.findall(r"[a-z][a-z0-9+#.-]{1,}", _normalize(text)) if w not in STOP]
    # Include adjacent bigrams to preserve phrases such as domain driven, event driven and low latency.
    return words + [words[i] + " " + words[i+1] for i in range(len(words)-1)]

def _lexical(text, entry, corpus_tokens=None):
    q = Counter(_tokens(text)); d = Counter(_tokens(entry))
    if not q or not d: return 0.0
    common = set(q) & set(d)
    # Dice-style weighted overlap; rare terms contribute more than generic words.
    denom = sum(q.values()) + sum(d.values())
    overlap = sum(2 * min(q[t], d[t]) * (1.0 + math.log1p(1.0 / max(1, (corpus_tokens or {}).get(t, 1)))) for t in common)
    weighted_denom = sum(v * (1.0 + math.log1p(1.0 / max(1, (corpus_tokens or {}).get(t, 1)))) for t,v in q.items()) + sum(v * (1.0 + math.log1p(1.0 / max(1, (corpus_tokens or {}).get(t, 1)))) for t,v in d.items())
    return min(1.0, overlap / max(1.0, weighted_denom))

def retrieve(profile, limit=8):
    text = " ".join((getattr(profile, "functional_requirements", []) or []) +
                    (getattr(profile, "non_functional_requirements", []) or []) +
                    (getattr(profile, "constraints", []) or []) +
                    (getattr(profile, "drivers", []) or []) +
                    (getattr(profile, "tags", []) or []) +
                    (getattr(profile, "technology_preferences", []) or []))
    normalized = _normalize(text)
    tags = set(getattr(profile, "tags", []) or [])
    pattern_docs = {k: p["description"] + " " + " ".join(p.get("tags", [])) + " " + " ".join(p.get("pros", [])) + " " + " ".join(p.get("cons", [])) for k,p in PATTERNS.items()}
    corpus_counts = Counter(t for doc in pattern_docs.values() for t in set(_tokens(doc)))
    ranked=[]
    for k,p in PATTERNS.items():
        doc=pattern_docs[k]
        lexical=_lexical(text,doc,corpus_counts)
        tag_hits=sum(1 for tag in p.get("tags",[]) if tag in tags or re.search(r"(?<![a-z0-9])"+re.escape(tag.replace("_"," "))+r"(?![a-z0-9])", normalized))
        # Explicit constraints are stronger evidence than generic vocabulary overlap.
        bonus=0.0
        low=normalized
        if k == "microservices" and any(x in low for x in ("independent deployment","independent scaling","service autonomy")): bonus += .12
        if k == "event_driven" and any(x in low for x in ("async","event stream","message queue","decouple")): bonus += .12
        if k == "cqrs" and any(x in low for x in ("read heavy","auditability","command query","separate read")): bonus += .12
        if k == "serverless" and any(x in low for x in ("bursty","pay per use","event invocation","low idle cost")): bonus += .12
        if k in ("modular_monolith","layered") and any(x in low for x in ("small team","simple deployment","low cost","transaction consistency")): bonus += .08
        if k == "clean_hexagonal" and any(x in low for x in ("testability","maintainability","replaceable infrastructure","domain rules")): bonus += .10
        if k == "hybrid" and sum(x in low for x in ("scalability","maintainability","async","incremental")) >= 2: bonus += .10
        score=lexical + min(.35,tag_hits*.045) + bonus
        ranked.append((score,k,p,lexical,tag_hits))
    method="lexical+driver evidence"
    if os.getenv("ENABLE_SEMANTIC_RETRIEVAL","false").lower()=="true":
        try:
            from sentence_transformers import SentenceTransformer,util
            model=SentenceTransformer(os.getenv("EMBEDDING_MODEL","all-MiniLM-L6-v2"))
            q=model.encode(text,normalize_embeddings=True)
            semantic=[]
            for score,k,p,lexical,hits in ranked:
                d=model.encode(pattern_docs[k],normalize_embeddings=True)
                sem=float(util.dot_score(q,d)[0][0])
                semantic.append((.55*score+.45*max(0.0,sem),k,p,lexical,hits))
            ranked=semantic; method="semantic+lexical+driver evidence"
        except Exception:
            method="lexical+driver evidence (semantic model unavailable)"
    ranked.sort(key=lambda x:(x[0],x[3],x[4]),reverse=True)
    return [{"pattern_key":k,"name":p["name"],"description":p["description"],"tags":p["tags"],
             "retrieval_score":round(float(score),4),"lexical_score":round(float(lexical),4),
             "matched_driver_count":hits,"method":method} for score,k,p,lexical,hits in ranked[:max(1,limit)]]
