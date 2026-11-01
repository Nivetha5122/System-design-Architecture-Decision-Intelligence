import re
from typing import Any, Dict, List

def _safe_name(value: str) -> str:
    x=re.sub(r"[^a-z0-9-]+","-",str(value or "archds-service").lower()).strip("-")
    return x[:45] or "archds-service"

def _components(candidate: Dict[str,Any]) -> List[str]:
    return [str(x) for x in (candidate.get("components") or []) if str(x).strip()]

def _deployable(c: str) -> bool:
    low=c.lower()
    return not any(k in low for k in ("database","postgres","mysql","mongodb","storage","object storage","cache","broker","queue","kafka","rabbitmq","cdn","waf","load balancer","monitoring","observability","audit","backup","disaster recovery"))

def _terraform(name:str, comps:List[str], prefs:List[str], users:Any, budget:Any) -> str:
    system=_safe_name(name); lines=['terraform {','  required_version = ">= 1.5.0"','}','',f'locals {{','  system_name = "{system}"',f'  expected_users = "{users or "not specified"}"',f'  budget = "{budget or "not specified"}"','}', '', '# ARCHDS requirement-derived deployment starting point.','// Components are derived from the selected architecture candidate and must be reviewed before production use.']
    if any("multi-region" in str(x).lower() or "multiple region" in str(x).lower() for x in prefs): lines += ['','// Multi-region preference detected: provide provider/region modules per target cloud.']
    for c in comps:
        key=_safe_name(c).replace('-','_')
        lines += ['',f'# {c}',f'module "{key}" {{','  source = "./modules/service"','  name   = "'+_safe_name(c)+'"','}']
    return '\n'.join(lines)+'\n'

def _kubernetes(name:str, comps:List[str], prefs:List[str], users:Any) -> str:
    docs=[]
    for c in comps:
        svc=_safe_name(c)
        docs.append('\n'.join(['apiVersion: apps/v1','kind: Deployment','metadata:',f'  name: {svc}','  labels:',f'    app: {svc}','spec:','  replicas: 2','  selector:','    matchLabels:',f'      app: {svc}','  template:','    metadata:','      labels:',f'        app: {svc}','    spec:','      containers:',f'        - name: {svc}',f'          image: {svc}:REPLACE_ME','          ports:','            - containerPort: 8080','          readinessProbe:','            httpGet:','              path: /health','              port: 8080','---','apiVersion: v1','kind: Service','metadata:',f'  name: {svc}','spec:','  selector:',f'    app: {svc}','  ports:','    - port: 80','      targetPort: 8080']))
    return '\n---\n'.join(docs)+'\n' if docs else '# No independently deployable application services were identified from this candidate.\n'

def _compose(comps:List[str]) -> str:
    services=[c for c in comps if _deployable(c)][:10]
    lines=['services:']
    if not services: return 'services: {}\n'
    for c in services:
        s=_safe_name(c); lines += [f'  {s}:','    image: '+s+':REPLACE_ME','    ports:','      - "8080"','    restart: unless-stopped','    healthcheck:','      test: ["CMD", "wget", "-qO-", "http://localhost:8080/health"]','      interval: 15s','      timeout: 3s','      retries: 3']
    return '\n'.join(lines)+'\n'

def _requirements_manifest(req:Dict[str,Any], candidate:Dict[str,Any]) -> str:
    lines=['# ARCHDS DELIVERY MANIFEST','# Generated from the current project requirement profile and selected candidate.','',f'project: {req.get("project_name") or "ARCHDS project"}',f'architecture: {candidate.get("name") or "selected candidate"}',f'expected_users: {req.get("expected_users") or "not specified"}',f'budget: {req.get("budget") or "not specified"}','', 'functional_requirements:']
    lines += [f'  - {x}' for x in req.get('functional_requirements',[])[:50]] or ['  - none supplied']
    lines += ['quality_attributes:']+[f'  - {x}' for x in req.get('non_functional_requirements',[])[:50]] or ['  - none supplied']
    lines += ['constraints:']+[f'  - {x}' for x in req.get('constraints',[])[:50]] or ['  - none supplied']
    lines += ['technology_preferences:']+[f'  - {x}' for x in req.get('technology_preferences',[])[:50]] or ['  - none supplied']
    return '\n'.join(lines)+'\n'

def _validate(terraform:str,kubernetes:str,compose:str) -> Dict[str,Any]:
    checks=[
      ('terraform',terraform.count('{')==terraform.count('}'),'Balanced Terraform blocks'),
      ('terraform','required_version' in terraform,'Terraform version constraint present'),
      ('kubernetes','apiVersion:' in kubernetes and 'kind:' in kubernetes or kubernetes.startswith('# No '),'Kubernetes output is structurally present'),
      ('kubernetes','readinessProbe:' in kubernetes or kubernetes.startswith('# No '),'Readiness probe included for generated services'),
      ('compose','services:' in compose,'Docker Compose service root present'),
    ]
    results=[{'artifact':a,'passed':bool(ok),'message':m} for a,ok,m in checks]
    return {'passed':all(x['passed'] for x in results),'checks':results}

def generate_delivery(req:Dict[str,Any],candidate:Dict[str,Any]) -> Dict[str,Any]:
    comps=_components(candidate); prefs=req.get('technology_preferences') or []
    terraform=_terraform(req.get('project_name') or 'ARCHDS Architecture',comps,prefs,req.get('expected_users'),req.get('budget'))
    kubernetes=_kubernetes(req.get('project_name') or 'ARCHDS Architecture',[c for c in comps if _deployable(c)],prefs,req.get('expected_users'))
    compose=_compose(comps); manifest=_requirements_manifest(req,candidate); validation=_validate(terraform,kubernetes,compose)
    return {'status':'VALIDATED' if validation['passed'] else 'NEEDS_REVIEW','architecture':candidate.get('name'),'candidate_id':candidate.get('candidate_id'),'derived_components':comps,'deployable_components':[c for c in comps if _deployable(c)],'artifacts':{'terraform':terraform,'kubernetes':kubernetes,'docker_compose':compose,'requirements_manifest':manifest},'validation':validation,'iterations':[{'iteration':1,'status':'GENERATED','action':'Generated artifacts from the selected requirement-derived candidate.'},{'iteration':2,'status':'VALIDATED' if validation['passed'] else 'NEEDS_REVIEW','action':'Validated structural invariants without claiming cloud provisioning.'}],'research_note':'Artifacts are requirement-derived starting points. They do not provision infrastructure, contain real credentials, or claim production readiness.'}
