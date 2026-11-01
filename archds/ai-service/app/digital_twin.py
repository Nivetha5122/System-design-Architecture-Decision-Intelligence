import math
from typing import Any, Dict, List


def _low(text: str) -> str:
    return (text or '').lower()


def _match(name: str, terms: List[str]) -> bool:
    low=_low(name)
    return any(t in low for t in terms)


def _all_text(req: Dict[str, Any]) -> str:
    return ' '.join([
        req.get('description',''),
        *(req.get('functional_requirements') or []),
        *(req.get('non_functional_requirements') or []),
        *(req.get('constraints') or []),
        *(req.get('technology_preferences') or []),
    ])


def scenario_catalog(req: Dict[str, Any], candidate: Dict[str, Any]) -> List[Dict[str, Any]]:
    low=_low(_all_text(req))
    records=req.get('functional_requirements') or req.get('non_functional_requirements') or []
    anchor=records[0] if records else 'the submitted system requirements'
    try: users=float(str(req.get('expected_users','')).replace(',',''))
    except Exception: users=0
    large=users>10000
    def item(i,title,subtitle,change,why,tags):
        relevant=any(t in low for t in tags) or (i in ('traffic_surge','data_growth') and large)
        return {'id':i,'title':title,'subtitle':subtitle,'change':change,'why':why,'relevance':'HIGH' if relevant else 'CONTEXTUAL','requirement_anchor':anchor}
    scenarios=[
        item('traffic_surge','Traffic surge','Workload increases against the submitted scale target',f'Increase workload relative to the submitted baseline ({req.get("expected_users") or "configured scale"})','Tests capacity headroom, queueing and edge pressure against the actual scale and traffic requirements.', ['scale','traffic','load','burst','users','scalability']),
        item('component_failure','Critical component failure','A runtime component becomes unavailable','Fail a critical component selected from the generated topology','Tests failure isolation and recovery against the supplied reliability, availability and fault-tolerance requirements.', ['failure','fault','reliability','resilien','recovery','availability']),
        item('dependency_failure','Dependency outage','An external or internal dependency stops responding','Fail a dependency represented in the generated architecture','Tests timeout, fallback, retry and isolation where the submitted requirements contain integrations or dependency risks.', ['integration','external','dependency','payment','provider','recovery']),
        item('latency_pressure','Latency pressure','The response-time target becomes stricter','Tighten the submitted latency/performance target by 50%','Tests the actual generated request path and identifies latency-sensitive components.', ['latency','real-time','realtime','response time','performance','low latency']),
        item('regional_outage','Regional outage','One deployment region becomes unavailable','Remove one active region','Tests geographic redundancy only when the requirement profile indicates multi-region, availability or disaster-recovery needs.', ['global','region','multi-region','disaster','availability','uptime']),
        item('security_pressure','Security pressure','Security controls face increased demand','Increase authentication, policy and anomaly-detection pressure','Tests whether identity, security boundaries and audit controls remain adequate for the submitted security requirements.', ['security','secure','privacy','authentication','authorization','audit','compliance']),
        item('data_growth','Data growth','Stored and queried data volume expands','Increase relevant data volume relative to the submitted workload','Tests persistence, indexing, cache and analytics capacity using the selected architecture graph.', ['data','storage','records','analytics','search','database']),
        item('flash_sale','Peak workload window','A short business peak stresses the request path','Apply a high-intensity burst relative to the submitted workload','Tests burst absorption only when the requirement profile contains peak, burst, transaction, booking or similar workload behavior.', ['booking','order','transaction','peak','burst','traffic']),
        item('disaster_recovery','Disaster recovery drill','The primary runtime path becomes unavailable','Remove the primary path and evaluate recovery controls','Tests recovery behavior against explicit disaster-recovery, backup, failover and resilience requirements.', ['disaster','backup','recovery','fault','availability','resilience']),
        item('cost_pressure','Cost pressure','The available resource budget is reduced','Reduce infrastructure capacity while protecting critical requirements','Evaluates cost/quality trade-offs when the submitted requirements contain cost or budget pressure.', ['budget','cost','econom','efficient','price']),
        item('deployment_rollback','Deployment rollback','A newly deployed version introduces a fault','Rollback an independently deployable boundary','Tests deployment isolation and recovery when the requirements imply independent deployment or service evolution.', ['deployment','independent','release','maintainability','version','microservice']),
        item('observability_loss','Observability degradation','A monitoring or logging path becomes unavailable','Disable one observability capability','Tests operational diagnosis and auditability against the submitted monitoring, logging, tracing or audit requirements.', ['monitor','observability','logging','tracing','audit','operations']),
    ]
    # Keep a useful experiment suite available for every architecture. Requirement-matched
    # scenarios appear first; contextual scenarios remain selectable and are explicitly labelled.
    # This avoids the previous UX failure where a generic requirement set exposed only one card.
    relevant=[x for x in scenarios if x['relevance']=='HIGH']
    contextual=[x for x in scenarios if x['relevance']!='HIGH']
    required_ids=['component_failure','traffic_surge','dependency_failure','latency_pressure',
                  'security_pressure','data_growth','disaster_recovery','deployment_rollback']
    ordered=[]
    for sid in required_ids:
        hit=next((x for x in relevant if x['id']==sid),None) or next((x for x in contextual if x['id']==sid),None)
        if hit and hit not in ordered: ordered.append(hit)
    for x in relevant+contextual:
        if x not in ordered: ordered.append(x)
    return ordered[:10]


def _baseline(candidate: Dict[str,Any], expected_users: Any) -> Dict[str,float]:
    s=candidate.get('scores') or {}
    score=float(s.get('weighted_total') or 0)
    scale=float(s.get('scalability') or 70); perf=float(s.get('performance') or 70)
    rel=float(s.get('reliability') or 70); avail=float(s.get('availability') or 70)
    try: users=float(str(expected_users).replace(',','')) if expected_users else 1
    except Exception: users=1
    return {
        'architecture_score':round(score,1),
        'capacity_index':round(min(100,55+scale*.42),1),
        'latency_index':round(min(100,45+perf*.52),1),
        'availability_index':round(min(100,45+avail*.55),1),
        'resilience_index':round(min(100,45+rel*.55),1),
        'utilization_index':round(min(92,25+math.log10(max(users,1))*8+max(0,80-scale)*.15),1),
        'active_components':len(candidate.get('components') or []),
    }


def _clamp(v): return round(max(5,min(100,float(v))),1)


def simulate(req: Dict[str,Any], candidate: Dict[str,Any], scenario_id: str, intensity: float=1.0) -> Dict[str,Any]:
    catalog=scenario_catalog(req,candidate)
    scenario=next((x for x in catalog if x['id']==scenario_id),catalog[0])
    intensity=max(.5,min(2.0,float(intensity or 1)))
    base=_baseline(candidate,req.get('expected_users'))
    nodes=candidate.get('graph',{}).get('nodes',[]) or []
    components=[x for x in (candidate.get('components') or [n.get('label') for n in nodes]) if x]
    states={c:{'status':'HEALTHY','load':base['utilization_index'],'latency':max(1,100-base['latency_index'])} for c in components}
    affected=[]; added=[]; removed=[]; assumptions=[]
    cap=base['capacity_index']; lat=base['latency_index']; avail=base['availability_index']; resil=base['resilience_index']
    sid=scenario['id']

    if sid in ('traffic_surge','flash_sale'):
        factor=10 if sid=='traffic_surge' else 20
        raw_util=base['utilization_index'] + max(0,(factor*intensity)-1)*3.5
        util=min(100,raw_util)
        for c in components:
            multiplier=.62 if _match(c,['cache','load balancer','gateway','queue','broker','cdn','edge','autoscal']) else 1.0
            states[c]['load']=_clamp(raw_util*multiplier)
        overload=max(0,raw_util-70)
        cap=_clamp(base['capacity_index']-overload*.42)
        lat=_clamp(base['latency_index']-max(0,raw_util-62)*.38)
        avail=_clamp(base['availability_index']-max(0,raw_util-88)*.28)
        affected=[c for c in components if states[c]['load']>=85]
        if util>78: added += ['Horizontal autoscaling policy','Queue-based load smoothing']
        if not any(_match(c,['cache']) for c in components): added.append('Distributed cache for hot reads')
        impact=f'Incoming workload reaches {factor*intensity:.1f}× baseline. {sum(1 for c in components if states[c]["load"]>85)} modeled components cross the high-load threshold.'
    elif sid=='component_failure':
        target=next((c for c in components if _match(c,['gateway','api','domain','service','notification','database','storage'])),components[0] if components else 'Primary component')
        states[target]['status']='FAILED'; states[target]['load']=0; affected=[target]
        # Propagate only through relationships present in the generated candidate graph.
        graph=candidate.get('graph',{}) or {}; byid={n.get('id'):n.get('label') for n in graph.get('nodes',[]) }
        downstream={target}; changed=True
        while changed:
            changed=False
            for e in graph.get('edges',[]) or []:
                src=byid.get(e.get('source')); dst=byid.get(e.get('target'))
                if src in downstream and dst and dst not in downstream:
                    downstream.add(dst); changed=True
        for c in components:
            if c in downstream and c!=target:
                states[c]['status']='DEGRADED'; states[c]['load']=_clamp(states[c]['load']*1.18); affected.append(c)
        cap-=18*intensity; lat-=10*intensity; avail-=22*intensity; resil-=28*intensity
        added=['Health-check driven failover','Circuit breaker / graceful degradation']
        impact=f'{target} is marked failed at T+5s. The twin propagates the fault only across relationships present in the generated candidate graph; {max(0,len(affected)-1)} downstream component(s) are marked degraded.'
    elif sid=='dependency_failure':
        target=next((c for c in components if _match(c,['external','integration','payment','shipping','provider','database','storage'])),components[-1] if components else 'Downstream dependency')
        states[target]['status']='FAILED'; affected=[target]
        cap-=10*intensity; lat-=9*intensity; avail-=18*intensity; resil-=20*intensity
        added=['Timeout + circuit breaker','Fallback / retry policy with bounded backoff']
        impact=f'{target} is unavailable. The twin tests isolation so the failure does not cascade through the rest of the architecture.'
    elif sid=='latency_pressure':
        lat-=22*intensity
        for c in components:
            states[c]['latency']=_clamp((100-base['latency_index'])+(14 if _match(c,['database','storage','queue','broker']) else 3)*intensity)
        affected=[c for c in components if states[c]['latency']>=20]
        added=['Latency-aware cache policy','Request-path profiling and budget enforcement']
        if not any(_match(c,['cache']) for c in components): added.append('Read-through distributed cache')
        impact=f'Latency sensitivity increases to {50*intensity:.0f}% beyond the baseline stress factor. Components with the highest modeled latency are surfaced for optimization.'
    elif sid=='regional_outage':
        cap-=24*intensity; lat-=11*intensity; avail-=34*intensity; resil-=36*intensity
        added=['Multi-region traffic failover','Replicated state / cross-region recovery plan']
        removed=['One deployment region']
        impact='One deployment region is removed from the topology. The twin checks whether the remaining architecture can serve the critical request path.'
    elif sid=='security_pressure':
        cap-=5*intensity; lat-=8*intensity; resil-=4*intensity
        added=['Centralized policy enforcement','Rate limiting + anomaly detection','Audit trail hardening']
        impact='Security-control demand is increased. The twin evaluates whether identity, policy, audit and sensitive-data boundaries remain explicit.'
    elif sid=='data_growth':
        util=min(100,base['utilization_index']+35*intensity)
        for c in components:
            if _match(c,['database','storage','cache','search','index','warehouse']): states[c]['load']=_clamp(util*1.05)
        cap-=18*intensity; lat-=12*intensity
        affected=[c for c in components if states[c]['load']>=85]
        added=['Partitioning / indexing strategy','Storage tiering or archival policy']
        impact=f'Data volume grows to {5*intensity:.1f}×. Persistence and query-heavy components receive the largest simulated pressure.'
    elif sid=='disaster_recovery':
        avail-=32*intensity; resil-=38*intensity; cap-=18*intensity
        added=['Warm standby or multi-zone recovery','Automated backup restore validation','Recovery runbook with RTO/RPO checks']
        removed=['Primary runtime path']
        impact='The primary runtime path is removed. The twin measures survivability and identifies the minimum recovery controls required by the submitted requirements.'
    elif sid=='cost_pressure':
        cap-=8*intensity; avail-=10*intensity; resil-=8*intensity
        added=['Right-size low-criticality replicas','Use asynchronous processing for non-critical work','Tier storage and observability retention']
        assumptions=['Cost is reduced only where the requirement priority model allows it; security and critical availability controls are protected.']
        impact=f'Available infrastructure budget is reduced by {25*intensity:.0f}%. The twin proposes cost reductions while protecting critical requirements.'
    elif sid=='deployment_rollback':
        resil-=18*intensity; avail-=10*intensity
        added=['Blue/green or canary deployment','Automated health-gated rollback']
        impact='A faulty deployment is introduced and rolled back. The twin evaluates whether the architecture has sufficiently isolated deployment boundaries.'
    else:  # observability
        resil-=10*intensity
        added=['Redundant telemetry path','Minimum audit/event retention policy']
        impact='One observability capability is disabled. The twin tests whether operators still have enough evidence to diagnose and audit the system.'

    affected_requirements=[]
    for rid, comps in (candidate.get('requirement_mappings') or {}).items():
        if any(a in comps for a in affected): affected_requirements.append(rid)
    overall=_clamp((cap+lat+avail+resil)/4)
    delta={
        'architecture_score':round(overall-base['architecture_score'],1),
        'capacity_index':round(cap-base['capacity_index'],1),
        'latency_index':round(lat-base['latency_index'],1),
        'availability_index':round(avail-base['availability_index'],1),
        'resilience_index':round(resil-base['resilience_index'],1),
    }
    severity='CRITICAL' if overall<50 else ('WARNING' if overall<75 else 'CONTROLLED')
    timeline=[
        {'t':'T+0s','event':'Baseline snapshot','state':f'Baseline architecture score {base["architecture_score"]}; {base["active_components"]} modeled components.','severity':'INFO'},
        {'t':'T+5s','event':scenario['change'],'state':impact,'severity':severity},
        {'t':'T+15s','event':'Propagation analysis','state':f'{len(affected)} component(s) directly affected; {len(affected_requirements)} requirement mapping(s) exposed.','severity':'WARNING' if affected else 'INFO'},
        {'t':'T+30s','event':'Agentic adaptation proposal','state':f'{len(added)} mitigation action(s) proposed; target post-stress score {overall}.','severity':'ACTION'},
    ]
    return {
        'scenario':scenario,'baseline':base,
        'twin':{
            'candidate_id':candidate.get('candidate_id'),'architecture':candidate.get('name'),
            'nodes':[{'id':n.get('id'),'label':n.get('label'),'layer':n.get('layer'),'status':states.get(n.get('label'),{}).get('status','HEALTHY'),'load':states.get(n.get('label'),{}).get('load',base['utilization_index'])} for n in nodes],
            'components':states,
        },
        'metrics':{'architecture_score':overall,'capacity_index':_clamp(cap),'latency_index':_clamp(lat),'availability_index':_clamp(avail),'resilience_index':_clamp(resil),'utilization_index':base['utilization_index']},
        'delta':delta,'severity':severity,'affected_components':affected,'affected_requirements':affected_requirements,
        'proposed_adaptations':list(dict.fromkeys(added)),'removed_components':removed,'assumptions':assumptions,
        'recommended_solution':{
            'title':'Requirement-preserving adaptive response',
            'actions':list(dict.fromkeys(added)),
            'expected_effect':f'Protect the highest-priority requirements while recovering the modeled score toward the baseline of {base["architecture_score"]}.',
            'human_gate':'Approve the mitigation only after checking cost, operational ownership and requirement priority weights.',
        },
        'timeline':timeline,
        'simulation_note':'Analytical architecture simulation driven by the submitted requirements and selected candidate graph. It is deterministic for a given scenario and intensity and is not a substitute for production load or chaos testing.',
    }


def evolve(req: Dict[str,Any], candidate: Dict[str,Any], scenario_id: str, intensity: float=1.0) -> Dict[str,Any]:
    """Run a counterfactual architecture-evolution pass over the Digital Twin.

    This is an analytical architecture mutation, not real infrastructure self-healing.
    It projects how requirement-preserving mitigations could recover the stressed state.
    """
    sim = simulate(req, candidate, scenario_id, intensity)
    base = sim['baseline']
    stressed = sim['metrics']
    actions = list(dict.fromkeys(sim.get('proposed_adaptations') or []))
    # Recovery factors are deliberately conservative and deterministic.
    recovery = 0.72 if sim['severity'] != 'CRITICAL' else 0.62
    projected = {}
    for key in ('architecture_score','capacity_index','latency_index','availability_index','resilience_index'):
        b=float(base.get(key,0)); d=float(stressed.get(key,b))-b
        projected[key]=_clamp(b + d*(1.0-recovery))
    # Derive a small, explicit architecture patch from the simulation actions.
    existing=[str(x) for x in (candidate.get('components') or [])]
    additions=[]
    for action in actions:
        low=action.lower()
        if 'cache' in low and not any('cache' in x.lower() for x in existing): additions.append('Distributed Cache')
        elif 'queue' in low or 'broker' in low:
            if not any(any(k in x.lower() for k in ('broker','queue','event')) for x in existing): additions.append('Durable Event Broker')
        elif 'failover' in low or 'standby' in low or 'multi-zone' in low:
            if not any('failover' in x.lower() or 'replica' in x.lower() or 'region' in x.lower() for x in existing): additions.append('Redundant Failover Boundary')
        elif 'circuit breaker' in low and not any('circuit' in x.lower() for x in existing): additions.append('Circuit Breaker / Resilience Policy')
        elif 'observability' in low or 'telemetry' in low:
            if not any('observ' in x.lower() or 'monitor' in x.lower() for x in existing): additions.append('Redundant Observability Path')
        elif 'autoscaling' in low and not any('scal' in x.lower() or 'load' in x.lower() for x in existing): additions.append('Autoscaling Policy')
    additions=list(dict.fromkeys(additions))[:5]
    patch=[{'action':'ADD','component':x,'reason':'Directly derived from the simulated failure/stress response.'} for x in additions]
    return {
        'status':'PROPOSED_EVOLUTION',
        'scenario':sim['scenario'],
        'baseline':base,
        'stressed':stressed,
        'projected_after_mitigation':projected,
        'recovery_ratio':round((1.0-recovery)*100,0),
        'blast_radius':{'components':sim.get('affected_components',[]),'requirements':sim.get('affected_requirements',[]),'count':len(sim.get('affected_components',[]))},
        'architecture_patch':patch,
        'mitigation_actions':actions,
        'decision_gate':{
            'recommended':'REVIEW_AND_VALIDATE',
            'message':'The proposed mutation should be re-evaluated by the architecture competition, Pareto analysis and Delivery Lab before adoption.',
            'not_production_self_healing':True
        },
        'explanation':f"The twin detected {len(sim.get('affected_components',[]))} directly affected component(s). ARCHDS proposes {len(patch)} architecture mutation(s) and projects recovery toward the baseline without claiming that a real deployment was changed."
    }
