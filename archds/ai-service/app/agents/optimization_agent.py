import numpy as np

def _dom(a,b): return np.all(a>=b) and np.any(a>b)
def _pareto(m): return [i for i,a in enumerate(m) if not any(_dom(b,a) for j,b in enumerate(m) if i!=j)]
def optimize(candidates,profile):
    objs=["performance","scalability","security","reliability","availability","cost","maintainability"]
    m=np.array([[c["scores"][a] for a in objs] for c in candidates],float); pi=_pareto(m)
    for i,c in enumerate(candidates): c["is_pareto_optimal"]=i in pi;c["dominated"]=i not in pi;c["objective_values"]={a:c["scores"][a] for a in objs}
    return sorted(candidates,key=lambda c:(not c["is_pareto_optimal"],-c["scores"]["weighted_total"])),{"algorithm":"Discrete non-dominated Pareto optimization","objectives":objs,"pareto_candidate_ids":[candidates[i]["candidate_id"] for i in pi],"pareto_frontier_size":len(pi),"tradeoffs":[f"{c['name']}: {c['scores']['weighted_total']:.2f} | Pareto={c['is_pareto_optimal']}" for c in candidates]}
