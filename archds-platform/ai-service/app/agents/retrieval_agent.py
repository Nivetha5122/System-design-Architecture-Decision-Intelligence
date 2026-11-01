import os,math
from ..knowledge_base import KNOWLEDGE,PATTERNS

def _lexical(text,entry):
    q=set(text.lower().split());t=set(entry.lower().split());return len(q&t)/(len(q)+1)

def retrieve(profile,limit=6):
    text=" ".join(profile.functional_requirements+profile.non_functional_requirements+profile.constraints+profile.tags)
    ranked=[]
    for k,p in PATTERNS.items():
        score=sum(1 for tag in p["tags"] if tag in text.lower() or tag in profile.tags)+_lexical(text,p["description"])*5
        ranked.append((score,k,p))
    # Optional semantic reranking. It is disabled by default to avoid downloading a model during a demo.
    if os.getenv("ENABLE_SEMANTIC_RETRIEVAL","false").lower()=="true":
        try:
            from sentence_transformers import SentenceTransformer,util
            model=SentenceTransformer(os.getenv("EMBEDDING_MODEL","all-MiniLM-L6-v2"))
            q=model.encode(text,normalize_embeddings=True)
            semantic=[]
            for _,k,p in ranked:
                v=model.encode(p["description"]+" "+" ".join(p["tags"]),normalize_embeddings=True)
                semantic.append((float(util.dot_score(q,v)[0][0]),k,p))
            ranked=sorted(semantic,key=lambda x:x[0],reverse=True)
        except Exception: pass
    else: ranked.sort(key=lambda x:x[0],reverse=True)
    return [{"pattern_key":k,"name":p["name"],"description":p["description"],"tags":p["tags"],"retrieval_score":round(float(s),4),"method":"semantic+lexical" if os.getenv("ENABLE_SEMANTIC_RETRIEVAL","false").lower()=="true" else "lexical fallback"} for s,k,p in ranked[:limit]]
