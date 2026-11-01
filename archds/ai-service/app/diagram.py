import html
import re

NODE_WIDTH = 250
NODE_HEIGHT = 96
LAYER_TITLES = {"experience":"Experience", "edge":"Edge, Identity & Integration", "domain":"Business Capabilities", "data":"Data & Platform"}


def _layer(name):
    n = name.lower()
    if any(x in n for x in ("client", "mobile", "web", "portal", "app", "frontend", "ui")): return "experience"
    if any(x in n for x in ("gateway", "identity", "provider", "edge", "auth", "security", "load balanc", "reverse proxy", "cdn", "waf", "realtime")): return "edge"
    if any(x in n for x in ("postgres", "mysql", "mariadb", "oracle", "sql server", "sql relational", "mongodb", "mongo", "dynamodb", "cassandra", "couchbase", "firestore", "database", "store", "storage", "blob", "object storage", "cache", "replica", "warehouse", "index", "broker", "event log", "queue", "kafka", "rabbit", "pulsar", "nats", "search", "telemetry", "time-series", "observability", "monitoring", "audit", "compliance", "resilience", "disaster recovery")): return "data"
    return "domain"


def _relations(c):
    known = set(c.get("components", [])); out = []
    for rel in c.get("relations", []):
        if "->" not in rel: continue
        a, b = [x.strip() for x in rel.split("->", 1)]
        if a in known and b in known and a != b: out.append((a, b))
    return list(dict.fromkeys(out))


def graph_for(c):
    components = list(dict.fromkeys(c.get("components", [])))
    layers = {k: [] for k in LAYER_TITLES}
    for name in components: layers[_layer(name)].append(name)
    width_total, left, lane_width = 1360, 42, 1276
    node_w, node_h, gap_x, gap_y = 250, 96, 24, 24
    lane_pad_top, lane_pad_bottom, lane_gap = 54, 28, 34
    nodes, groups, current_y = [], [], 28
    for layer in ("experience", "edge", "domain", "data"):
        members = layers[layer]
        if not members: continue
        cols = min(4, max(1, len(members))); rows = (len(members) + cols - 1) // cols
        inner_width = lane_width - 40
        cell_w = (inner_width - gap_x * (cols - 1)) / cols
        node_width = min(node_w, cell_w)
        lane_height = lane_pad_top + rows * node_h + max(0, rows - 1) * gap_y + lane_pad_bottom
        group_y = current_y
        for i, name in enumerate(members):
            col, row = i % cols, i // cols
            x, y = left + 20 + col * (node_width + gap_x), group_y + lane_pad_top + row * (node_h + gap_y)
            nodes.append({"id": f"n{len(nodes)}", "label": name, "type": "component", "layer": layer,
                          "x": round(x, 1), "y": round(y, 1), "width": round(node_width, 1), "height": node_h,
                          "requirements": c.get("component_requirements", {}).get(name, [])})
        groups.append({"id": layer, "title": LAYER_TITLES[layer], "x": left, "y": group_y, "width": lane_width, "height": lane_height})
        current_y += lane_height + lane_gap
    by_name = {n["label"]: n for n in nodes}
    edges = []
    for i, (a, b) in enumerate(_relations(c)):
        if a in by_name and b in by_name:
            edges.append({"id": f"e{i}", "source": by_name[a]["id"], "target": by_name[b]["id"], "label": "", "kind": "dependency"})
    # Deterministic orthogonal routing: edges use the vertical gaps between layer lanes
    # and dedicated side channels for same-layer dependencies, keeping connectors away from cards.
    by_id={n["id"]:n for n in nodes}
    layer_order={name:i for i,name in enumerate(("experience","edge","domain","data"))}
    gap_counters={}
    for idx,e in enumerate(edges):
        a,b=by_id[e["source"]],by_id[e["target"]]
        ax,ay=a["x"]+a["width"]/2,a["y"]+a["height"]/2
        bx,by=b["x"]+b["width"]/2,b["y"]+b["height"]/2
        if a["layer"]!=b["layer"]:
            downward=layer_order.get(b["layer"],0)>layer_order.get(a["layer"],0)
            sy=a["y"]+a["height"] if downward else a["y"]
            ty=b["y"] if downward else b["y"]+b["height"]
            gap_key=(min(a["y"]+a["height"],b["y"]+b["height"]),max(a["y"],b["y"]))
            lane=gap_counters.get(gap_key,0); gap_counters[gap_key]=lane+1
            mid=(sy+ty)/2 + (lane%7-3)*8
            e["points"]=[{"x":round(ax,1),"y":round(sy,1)},{"x":round(ax,1),"y":round(mid,1)},{"x":round(bx,1),"y":round(mid,1)},{"x":round(bx,1),"y":round(ty,1)}]
        else:
            right=bx>=ax; x1=a["x"]+a["width"] if right else a["x"]; x2=b["x"] if right else b["x"]+b["width"]
            if abs(ay-by)<12: e["points"]=[{"x":round(x1,1),"y":round(ay,1)},{"x":round(x2,1),"y":round(by,1)}]
            else:
                lane=(idx%7)*10; channel=(max(a["x"]+a["width"],b["x"]+b["width"])+30+lane) if right else (min(a["x"],b["x"])-30-lane)
                e["points"]=[{"x":round(x1,1),"y":round(ay,1)},{"x":round(channel,1),"y":round(ay,1)},{"x":round(channel,1),"y":round(by,1)},{"x":round(x2,1),"y":round(by,1)}]
    return {"nodes": nodes, "edges": edges, "groups": groups, "legend": LAYER_TITLES,
            "canvas_width": width_total, "canvas_height": max(650, current_y + 18)}


def _safe_id(text, prefix="X"):
    return prefix + re.sub(r"[^A-Za-z0-9]", "", text)[:28] or prefix + "Item"


def _short(text, limit=72):
    text = re.sub(r"\s+", " ", str(text).strip())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


ACTION_PATTERNS = [
    (r'authenticate(?:s|d|ing|ion)?', 'authenticate'),
    (r'login(?:s|ed|ing)?', 'login'), (r'logout(?:s|ed|ing)?', 'logout'),
    (r'register(?:s|ed|ing|ation)?', 'register'),
    (r'upload(?:s|ed|ing)?', 'upload'), (r'download(?:s|ed|ing)?', 'download'),
    (r'screen(?:s|ed|ing)?', 'screen'), (r'rank(?:s|ed|ing)?', 'rank'),
    (r'shortlist(?:s|ed|ing)?', 'shortlist'), (r'assess(?:es|ed|ing|ment)?', 'assess'),
    (r'evaluat(?:e|es|ed|ing)', 'evaluate'), (r'match(?:es|ed|ing)?', 'match'),
    (r'recommend(?:s|ed|ing|ation)?', 'recommend'), (r'detect(?:s|ed|ing|ion)?', 'detect'),
    (r'analyz(?:e|es|ed|ing)', 'analyze'), (r'explain(?:s|ed|ing|able)?', 'explain'),
    (r'review(?:s|ed|ing)?', 'review'), (r'generate(?:s|d|ing)?', 'generate'),
    (r'create(?:s|d|ing)?', 'create'), (r'update(?:s|d|ing)?', 'update'),
    (r'delete(?:s|d|ing)?', 'delete'), (r'remove(?:s|d|ing)?', 'remove'),
    (r'manage(?:s|d|ing|ment)?', 'manage'), (r'maintain(?:s|ed|ing)?', 'maintain'),
    (r'search(?:es|ed|ing)?', 'search'), (r'browse(?:s|d|ing)?', 'browse'),
    (r'filter(?:s|ed|ing)?', 'filter'), (r'view(?:s|ed|ing)?', 'view'),
    (r'retrieve(?:s|d|ing)?', 'retrieve'), (r'place(?:s|d|ing)?', 'place'),
    (r'book(?:s|ed|ing)?', 'book'), (r'cancel(?:s|ed|ing|lation)?', 'cancel'),
    (r'pay(?:s|ed|ing|ment)?', 'pay'), (r'process(?:es|ed|ing)?', 'process'),
    (r'track(?:s|ed|ing)?', 'track'), (r'send(?:s|ing)?', 'send'),
    (r'receive(?:s|d|ing)?', 'receive'), (r'notify(?:s|ied|ing)?', 'notify'),
    (r'submit(?:s|ted|ting)?', 'submit'), (r'approve(?:s|d|ing)?', 'approve'),
    (r'verify(?:s|ied|ing)?', 'verify'), (r'check(?:s|ed|ing)?', 'check'),
    (r'assign(?:s|ed|ing)?', 'assign'), (r'schedule(?:s|d|ing)?', 'schedule'),
    (r'deliver(?:s|ed|ing)?', 'deliver'), (r'dispatch(?:es|ed|ing)?', 'dispatch'),
    (r'consult(?:s|ed|ing)?', 'consult'), (r'prescribe(?:s|d|ing)?', 'prescribe'),
    (r'apply(?:s|ied|ing)?', 'apply'), (r'request(?:s|ed|ing)?', 'request'),
    (r'configure(?:s|d|ing)?', 'configure'), (r'deploy(?:s|ed|ing)?', 'deploy'),
    (r'backup(?:s|ed|ing)?', 'backup'), (r'restore(?:s|d|ing)?', 'restore'),
    (r'validate(?:s|d|ing)?', 'validate'), (r'calculate(?:s|d|ing)?', 'calculate'),
    (r'predict(?:s|ed|ing|ion)?', 'predict'), (r'classif(?:y|ies|ied|ying)', 'classify'),
]
_ACTION_RE = re.compile(r'\b(?:' + '|'.join(p for p,_ in ACTION_PATTERNS) + r')\b', re.I)
_ACTION_CANON = {re.compile(r'\b'+p+r'\b', re.I): v for p,v in ACTION_PATTERNS}
_STOPWORDS = {'the','a','an','and','or','with','for','to','from','into','using','through','that','which','must','should','shall','can','could','would','may','will','be','able','allow','allows','enable','enables','system','platform','application','service','users','user'}
_ACTOR_TERMS = [
    ('patient','Patient'),('doctor','Doctor'),('clinician','Clinician'),('nurse','Nurse'),
    ('administrator','Administrator'),('admin','Administrator'),('staff','Staff'),
    ('customer','Customer'),('student','Student'),('employee','Employee'),('manager','Manager'),
    ('operator','Operator'),('member','Member'),('supplier','Supplier'),('partner','Partner'),
    ('driver','Driver'),('recruiter','Recruiter'),('candidate','Candidate'),('applicant','Applicant'),
    ('auditor','Auditor'),('analyst','Analyst'),('hr manager','HR Manager'),('human resources','HR Manager'),
]
_DOMAIN_EXPLICIT = [
    ('customer','Customer'),('patient','Patient'),('doctor','Doctor'),('clinician','Clinician'),('nurse','Nurse'),
    ('student','Student'),('employee','Employee'),('manager','Manager'),('administrator','Administrator'),
    ('order','Order'),('payment','Payment'),('transaction','Transaction'),('account','Account'),('product','Product'),
    ('inventory','Inventory'),('shipment','Shipment'),('appointment','Appointment'),('prescription','Prescription'),
    ('invoice','Invoice'),('beneficiary','Beneficiary'),('statement','Statement'),('transfer','Transfer'),
    ('booking','Booking'),('profile','Profile'),('claim','Claim'),('ticket','Ticket'),('message','Message'),
    ('application status','Application Status'),('report','Report'),('resume','Resume'),('cv','Resume'),('candidate','Candidate'),('applicant','Applicant'),
    ('job requirements','Job Requirement'),('job requirement','Job Requirement'),('job roles','Job Role'),('job role','Job Role'),('job','Job'),('vacancy','Job Vacancy'),('skill','Skill'),('interview','Interview'),
    ('assessment','Assessment'),('score','Assessment Score'),('recommendation','Recommendation'),
    ('decision','Decision'),('bias','Bias Assessment'),('fairness','Fairness Assessment'),('application','Application'),
    ('course','Course'),('record','Record'),('document','Document'),('file','File'),('notification','Notification'),
]

def _canonical_action(token):
    low=token.lower()
    for pat,canon in ACTION_PATTERNS:
        if re.fullmatch(pat,low,re.I): return canon
    return low

def _clean_object(text):
    text=re.sub(r'\s+',' ',text).strip(' ,;:.')
    text=re.sub(r'^(the|a|an|their|its|this|that)\s+','',text,flags=re.I)
    text=re.split(r'\b(?:so that|in order to|where|when|while|if|using|through)\b',text,maxsplit=1,flags=re.I)[0]
    text=re.split(r'\s+(?:and|or)\s+(?:the|a|an|their|its)\s+',text,maxsplit=1,flags=re.I)[0]
    text=re.sub(r'\s+(?:and|or|then)$','',text,flags=re.I)
    return text.strip(' ,;:.')

def _extract_actions(text):
    """Return atomic (canonical verb, object phrase, source span) tuples in requirement order."""
    text=re.sub(r'\s+',' ',str(text)).strip()
    matches=list(_ACTION_RE.finditer(text))
    out=[]
    for i,m in enumerate(matches):
        verb=_canonical_action(m.group(0))
        end=matches[i+1].start() if i+1<len(matches) else len(text)
        obj=_clean_object(text[m.end():end])
        # Trim coordination residue before the next action.
        obj=re.sub(r'^(?:and|or|then)\s+','',obj,flags=re.I)
        # If the action has no object, infer a domain object from nearby nouns.
        if not obj:
            before=text[max(0,m.start()-42):m.start()]
            candidates=re.findall(r'\b([A-Za-z][A-Za-z0-9-]{2,24})\b',before)
            candidates=[x for x in candidates if x.lower() not in _STOPWORDS and x.lower() not in {v for _,v in _ACTOR_TERMS}]
            if candidates: obj=candidates[-1]
        if verb in {'authenticate','login','logout'} and not obj: obj='user'
        if verb in {'pay','process'} and not obj: obj='transaction'
        if verb in {'notify','send'} and not obj: obj='notification'
        if obj: out.append((verb,obj,m.start(),m.end()))
    return out

def _phrase_nouns(phrase):
    low=phrase.lower(); found=[]; matched_tokens=[]
    for token,label in sorted(_DOMAIN_EXPLICIT,key=lambda x:-len(x[0])):
        if any(re.search(r'\b'+re.escape(token)+r'\b', mt) for mt in matched_tokens):
            continue
        if re.search(r'\b'+re.escape(token)+r's?\b',low):
            if label not in found: found.append(label)
            matched_tokens.append(token)
    # If an explicit domain noun was found, do not manufacture extra one-word classes from its modifiers.
    if found: return found[:4]
    clean=re.sub(r'[^A-Za-z0-9 -]',' ',low)
    words=[w for w in clean.split() if len(w)>2 and w not in _STOPWORDS and not _ACTION_RE.fullmatch(w)]
    quality={'high','low','secure','sensitive','global','automatic','automated','appropriate','strong','necessary','independently','related','operational','important','new','unrelated','time','based','driven','digital','fair','explainable','bias'}
    words=[w for w in words if w not in quality]
    if words:
        candidate=words[-1].rstrip('s')
        label=candidate.replace('-',' ').title()
        if label not in found: found.append(label)
    return found[:4]

def _subject_before_action(text):
    low=text.lower().strip()
    first=_ACTION_RE.search(low)
    if not first: return ''
    prefix=low[:first.start()].strip(' ,:')
    prefix=re.sub(r'^(?:the|a|an)\s+','',prefix).strip()
    # Remove requirement framing such as "users must be able to" while preserving the subject.
    prefix=re.sub(r'\b(?:must|should|shall|can|may|will|needs to|is able to|are able to|allows?)\b.*$','',prefix).strip()
    return prefix

def _infer_actors(requirements):
    found=[]
    for req in requirements:
        low=req.lower()
        subject=_subject_before_action(low)
        if subject:
            for token,label in _ACTOR_TERMS:
                if re.search(r'\b'+re.escape(token)+r's?\b',subject) and label not in found: found.append(label)
            if re.search(r'\b(?:system|platform|application|service)\b',subject) and 'System' not in found:
                found.append('System')
        for token,label in _ACTOR_TERMS:
            if re.search(r'\b'+re.escape(token)+r's?\b',low) and label not in found:
                # Mentioned domain actors are useful only when they are not merely objects of a system action.
                if not subject or re.search(r'\b'+re.escape(token)+r's?\b',subject): found.append(label)
    if not found: found=['System User']
    return found[:8]

def _actor_for(req, actors):
    low=req.lower(); subject=_subject_before_action(low)
    for token,label in _ACTOR_TERMS:
        if re.search(r'\b'+re.escape(token)+r's?\b',subject) and label in actors: return label
    if re.search(r'\b(?:system|platform|application|service)\b',subject) and 'System' in actors: return 'System'
    if any(x in low for x in ('administrator','admin','dashboard','manage users')) and 'Administrator' in actors: return 'Administrator'
    if any(x in low for x in ('external system','external provider','payment gateway','shipping provider')) and 'External System' in actors: return 'External System'
    return actors[0] if actors else 'System User'

def _is_quality_requirement(text):
    low=re.sub(r"\s+"," ",str(text).lower()).strip()
    quality_terms=("availability","uptime","latency","performance","scalab","throughput","reliab","fault toler",
                   "disaster recovery","backup","recovery time","rto","rpo","security","encryption","audit",
                   "logging","monitoring","tracing","observability","maintainab","extensib","cost","budget",
                   "multi-region","horizontal scaling","high performance","low latency","remain available",
                   "global deployment","globally deploy","response time","concurrent","million users")
    action=bool(_ACTION_RE.search(low))
    quality=any(t in low for t in quality_terms)
    if quality and not action: return True
    if quality and re.match(r"^(the |a |an )?(system|platform|application|service)\s+(must|should|shall|needs to|is required to)\b",low):
        return True
    return False

def _split_functional_requirements(records):
    """Convert submitted functional requirements into atomic user-goal clauses while retaining source IDs."""
    out=[]
    for r in records:
        text=re.sub(r'\s+',' ',str(r.get('description') or '').strip()).strip()
        if not text or _is_quality_requirement(text): continue
        # Sentence boundaries are only used to preserve requirement order; actions are extracted within each sentence.
        sentences=[x.strip(' .') for x in re.split(r'(?<=[.!?])\s+|\s*;\s*',text) if x.strip()]
        for sent in sentences:
            actions=_extract_actions(sent)
            if not actions: continue
            for verb,obj,_,_ in actions:
                clause=f'{verb} {obj}'.strip()
                # Preserve actor context and original requirement in metadata.
                out.append((r,clause,sent,verb,obj))
    return out

def _use_case_name(text):
    actions=_extract_actions(text)
    if actions:
        verb,obj,*_=actions[0]
        label={'authenticate':'Authenticate user','login':'Log in','logout':'Log out','register':'Register user',
               'upload':'Upload','download':'Download','screen':'Screen','rank':'Rank','shortlist':'Shortlist',
               'assess':'Assess','evaluate':'Evaluate','match':'Match','recommend':'Recommend','detect':'Detect',
               'analyze':'Analyze','explain':'Explain','review':'Review','generate':'Generate','create':'Create',
               'update':'Update','delete':'Delete','remove':'Remove','manage':'Manage','maintain':'Maintain',
               'search':'Search','browse':'Browse','filter':'Filter','view':'View','retrieve':'Retrieve',
               'place':'Place','book':'Book','cancel':'Cancel','pay':'Process payment','process':'Process',
               'track':'Track','send':'Send','receive':'Receive','notify':'Notify','submit':'Submit','approve':'Approve',
               'verify':'Verify','check':'Check','assign':'Assign','schedule':'Schedule','deliver':'Deliver',
               'dispatch':'Dispatch','consult':'Consult','prescribe':'Prescribe','apply':'Apply','request':'Request',
               'configure':'Configure','deploy':'Deploy','backup':'Back up','restore':'Restore','validate':'Validate',
               'calculate':'Calculate','predict':'Predict','classify':'Classify'}.get(verb,verb.title())
        # Object phrase is cleaned to a concise goal, preserving important domain nouns.
        obj=_clean_object(obj)
        if obj: return f'{label} {obj}'.strip().title()
        return label
    return None

def _split_entities(text):
    found=[]
    for e in _phrase_nouns(text):
        if e not in found: found.append(e)
    return found

def _operation_names(text):
    ops=[]
    for verb,_,_,_ in _extract_actions(text):
        op={
          'register':'register()','authenticate':'authenticate()','login':'login()','logout':'logout()',
          'upload':'upload()','download':'download()','screen':'screen()','rank':'rank()','shortlist':'shortlist()',
          'assess':'assess()','evaluate':'evaluate()','match':'match()','recommend':'recommend()',
          'detect':'detect()','analyze':'analyze()','explain':'explain()','review':'review()',
          'generate':'generate()','create':'create()','update':'update()','delete':'delete()','remove':'remove()',
          'manage':'manage()','maintain':'maintain()','search':'search()','browse':'browse()','filter':'filter()',
          'view':'view()','retrieve':'retrieve()','place':'place()','book':'book()','cancel':'cancel()',
          'pay':'pay()','process':'process()','track':'track()','send':'send()','receive':'receive()',
          'notify':'notify()','submit':'submit()','approve':'approve()','verify':'verify()','check':'check()',
          'assign':'assign()','schedule':'schedule()','deliver':'deliver()','dispatch':'dispatch()',
          'consult':'consult()','prescribe':'prescribe()','apply':'apply()','request':'request()',
          'configure':'configure()','deploy':'deploy()','backup':'backup()','restore':'restore()',
          'validate':'validate()','calculate':'calculate()','predict':'predict()','classify':'classify()'
        }.get(verb,verb+'()')
        if op not in ops: ops.append(op)
    return ops[:6]

def _relation_label(text, a, b):
    actions=_extract_actions(text)
    if not actions: return 'associated with'
    verb=actions[0][0]
    labels={'process':'processes','manage':'manages','place':'places','update':'updates','create':'creates','track':'tracks','pay':'pays','book':'books','contain':'contains','include':'includes','use':'uses','store':'stores','send':'sends','maintain':'maintains','support':'supports','handle':'handles','link':'links'}
    return labels.get(verb, verb + ('es' if verb.endswith(('s','sh','ch','x','z')) else 's'))

def uml_for(c):
    """Generate UML directly from atomic actions and domain objects in the submitted requirements.
    No fixed business workflow is injected; every use case, class operation and sequence message carries
    source requirement evidence.
    """
    raw=c.get('uml_requirements') or []
    pairs=_split_functional_requirements([x for x in raw if x.get('description')])
    seen=set(); unique=[]
    for record,clause,source,verb,obj in pairs:
        key=(record.get('id'),re.sub(r'[^a-z0-9]+',' ',clause.lower()).strip())
        if key not in seen:
            seen.add(key); unique.append((record,clause,source,verb,obj))
    pairs=unique[:36]
    source_requirements=[x[2] for x in pairs]
    actors=_infer_actors(source_requirements)
    use_cases=[]
    for record,clause,source,verb,obj in pairs:
        name=_use_case_name(clause)
        if not name: continue
        actor=_actor_for(source,actors)
        use_cases.append({'id':f'UC{len(use_cases)+1}','name':name,'requirement_id':record.get('id') or 'REQ','requirement':source,'action':verb,'object':obj,'actor':actor})
    dedup=[]; seen=set()
    for u in use_cases:
        key=(u['actor'],u['name'].lower(),u['requirement_id'])
        if key not in seen: seen.add(key); dedup.append(u)
    use_cases=dedup[:36]
    associations=[{'actor':u['actor'],'use_case':u['id'],'requirement':u['requirement_id']} for u in use_cases]

    # Domain model: extract entities from the complete requirement corpus, not only action objects.
    # This keeps nouns such as Order, Payment and Inventory visible even when they occur as objects
    # in a separate clause. A conservative allow-list prevents NFR/technology words becoming classes.
    entity_sources={}
    entity_actions={}
    for record in raw:
        source=str(record.get('description',''))
        for entity in _split_entities(source):
            if entity not in set(actors)|{'System User','System'}:
                entity_sources.setdefault(entity,[]).append((record,source))
        for record0,clause,source0,verb,obj in pairs:
            if record0.get('id')==record.get('id'):
                for entity in _split_entities(obj):
                    entity_actions.setdefault(entity,[]).append((source0,verb))
    # Prefer entities supported by multiple requirements, then by their first occurrence.
    entity_names=[e for e in entity_sources if e.lower() not in {'availability','performance','scalability','security','reliability','maintainability','cost','latency','throughput','resilience','recovery','monitoring','observability','encryption','authentication','authorization','technology','architecture','requirement','requirements','system','platform','application','service','data','infrastructure','deployment','compliance','auditability'}]
    entity_names=sorted(entity_names,key=lambda e:(-len({r.get('id') for r,_ in entity_sources[e]}), list(entity_sources).index(e)))[:14]
    classes=[]
    for entity in entity_names:
        related_text=[src for _,src in entity_sources.get(entity,[])]
        operations=[]
        for source0,verb in entity_actions.get(entity,[]): operations.extend(_operation_names(verb+' '+entity)[:1])
        operations=list(dict.fromkeys(operations))[:4] or ['view()']
        low=' '.join(related_text).lower()
        attrs=['id']
        for a in ('name','email','status','amount','score','date','type','location','description','createdAt','updatedAt','quantity','price','role','timestamp'):
            if re.search(r'\b'+re.escape(a.lower())+r'\b',low) and a not in attrs: attrs.append(a)
        classes.append({'name':entity,'attributes':attrs[:5],'operations':operations,
                        'requirements':list(dict.fromkeys([r.get('id') for r,_ in entity_sources.get(entity,[]) if r.get('id')]))[:8]})
    # Association edges only connect classes explicitly co-mentioned in the same requirement.
    # We do not invent inheritance/composition; those require explicit semantic evidence.
    class_rel=[]; relation_keys=set()
    for record in raw:
        source=str(record.get('description',''))
        matched=[]
        for entity in entity_names:
            if any(re.search(r'\b'+re.escape(token)+r's?\b',source,re.I) for token in [entity, entity.lower()]):
                matched.append(entity)
        for i,a in enumerate(matched):
            for b in matched[i+1:]:
                key=tuple(sorted((a,b)))
                if a!=b and key not in relation_keys:
                    relation_keys.add(key)
                    class_rel.append({'from':a,'to':b,'label':'associated with',
                                      'requirement_id':record.get('id') or 'REQ','evidence':source,
                                      'type':'association'})
    # If a domain is very small or requirements are terse, use action-object links as a grounded fallback.
    if not class_rel and len(entity_names)>1:
        for record,clause,source,verb,obj in pairs:
            matched=[e for e in entity_names if re.search(r'\b'+re.escape(e)+r's?\b',source+' '+obj,re.I)]
            for i,a in enumerate(matched):
                for b in matched[i+1:]:
                    key=tuple(sorted((a,b)))
                    if key not in relation_keys:
                        relation_keys.add(key); class_rel.append({'from':a,'to':b,'label':'associated with','requirement_id':record.get('id') or 'REQ','evidence':source,'type':'association'})
    class_rel=class_rel[:28]

    # Sequence: preserve the actual requirement action order across a representative end-to-end flow.
    # Each action is traced to its requirement, actor and domain object. The system boundary is explicit.
    seq_pairs=pairs[:20]
    primary=use_cases[0] if use_cases else {'requirement':'No actionable functional requirement was supplied.','requirement_id':'N/A','actor':actors[0]}
    participant_names=[]
    for u in use_cases[:20]:
        for p in (u['actor'],'System'):
            if p not in participant_names: participant_names.append(p)
        for e in _split_entities(u['object']):
            if e in entity_names and e not in participant_names: participant_names.append(e)
    # Add selected architecture components only when they are directly mapped to requirement actions.
    mapping=c.get('requirement_mappings',{}) or {}
    for u in use_cases[:8]:
        for comp in mapping.get(u['requirement_id'],[])[:2]:
            if comp in c.get('components',[]) and comp not in participant_names: participant_names.append(comp)
    participant_names=participant_names[:10] or ['System User','System']
    messages=[]
    for u in use_cases[:20]:
        actor=u['actor']; obj_entities=[e for e in _split_entities(u['object']) if e in entity_names]
        messages.append({'from':actor,'to':'System','label':u['name'],'requirement_id':u['requirement_id']})
        if obj_entities:
            messages.append({'from':'System','to':obj_entities[0],'label':f"{u['action']} {obj_entities[0]}",'requirement_id':u['requirement_id']})
            messages.append({'from':obj_entities[0],'to':'System','label':f"{u['action']} completed",'requirement_id':u['requirement_id']})
        messages.append({'from':'System','to':actor,'label':f"Return {u['name']}",'requirement_id':u['requirement_id']})
    messages=messages[:96]
    return {'use_case':{'actors':actors,'use_cases':use_cases,'associations':associations},
            'class':{'classes':classes,'relations':class_rel},
            'sequence':{'participants':participant_names,'messages':messages,'requirement_id':primary['requirement_id'],'requirement':primary.get('requirement','')},
            'sources':{'functional_requirements':source_requirements}}

def plantuml_for(c):
    components=list(dict.fromkeys(c.get("components",[]))); aliases={name:f"C{i}" for i,name in enumerate(components)}
    lines=["@startuml","title ARCHDS — Requirement-Derived Component Architecture","left to right direction","skinparam componentStyle rectangle","skinparam linetype ortho","skinparam shadowing false","skinparam packageStyle rectangle","skinparam defaultTextAlignment center"]
    for layer,title in LAYER_TITLES.items():
        members=[n for n in components if _layer(n)==layer]
        if not members: continue
        lines.append(f'package "{title}" {{')
        for name in members:
            reqs=c.get("component_requirements",{}).get(name,[])
            label=name if not reqs else f"{name}\\n[{', '.join(reqs[:4])}]"
            lines.append(f'  component "{label}" as {aliases[name]}')
        lines.append('}')
    for a,b in _relations(c): lines.append(f'{aliases[a]} --> {aliases[b]}')
    lines.append("@enduml"); return "\n".join(lines)


def uml_plantuml(c):
    u= c.get("uml") or uml_for(c); lines=[]
    uc=u["use_case"]; lines += ["@startuml","title ARCHDS — Requirement-Derived Use Case Diagram","left to right direction","skinparam packageStyle rectangle"]
    lines.append('rectangle "System Boundary" {')
    for x in uc["use_cases"]: lines.append(f'  usecase "{x["name"].replace(chr(34), chr(39))}" as {x["id"]}')
    lines.append('}')
    for actor in uc["actors"]: lines.append(f'actor "{actor}" as A{_safe_id(actor)[1:]}')
    for a in uc["associations"]: lines.append(f'A{_safe_id(a["actor"])[1:]} --> {a["use_case"]}')
    lines.append("@enduml"); usecase="\n".join(lines)
    cl=u["class"]; lines=["@startuml","title ARCHDS — Requirement-Derived Domain Class Diagram","skinparam classAttributeIconSize 0"]
    for x in cl["classes"]:
        lines.append(f'class "{x["name"]}" {{'); lines += [f'  {a}' for a in x["attributes"]]; lines += ["  --"]; lines += [f'  +{o}' for o in x["operations"]]; lines.append('}')
    for r in cl["relations"]:
        lines.append(f'"{r["from"]}" -- "{r["to"]}" : {r["label"]}')
    lines.append("@enduml"); klass="\n".join(lines)
    sq=u["sequence"]; lines=["@startuml","title ARCHDS — Requirement-Derived Request Sequence","autonumber"]
    for p in sq["participants"]: lines.append(f'participant "{p}" as P{_safe_id(p)[1:]}')
    for m in sq["messages"]: lines.append(f'P{_safe_id(m["from"])[1:]} -> P{_safe_id(m["to"])[1:]}: {m["label"]}')
    lines.append("@enduml"); sequence="\n".join(lines)
    return {"use_case":usecase,"class":klass,"sequence":sequence}


def svg_for(c):
    g=graph_for(c); width=1360; height=g.get("canvas_height",650); esc=lambda x: html.escape(str(x), quote=True)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    out.append('<defs><marker id="archds-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#64748b"/></marker></defs>')
    for group in g["groups"]:
        out.append(f'<rect x="{group["x"]}" y="{group["y"]}" width="{group["width"]}" height="{group["height"]}" rx="16" fill="none" stroke="#334155"/>')
        out.append(f'<text x="{group["x"]+16}" y="{group["y"]+22}" font-family="Inter,Segoe UI,Arial" font-size="13" fill="#475569">{esc(group["title"])}</text>')
    byid={n["id"]:n for n in g["nodes"]}
    for e in g["edges"]:
        pts=e.get("points") or []
        if len(pts)>1:
            d=" ".join(("M" if i==0 else "L")+f" {p['x']} {p['y']}" for i,p in enumerate(pts))
            out.append(f'<path d="{d}" fill="none" stroke="#64748b" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#archds-arrow)"/>')
    for n in g["nodes"]:
        reqs=n.get("requirements",[]); out.append(f'<rect x="{n["x"]}" y="{n["y"]}" width="{n["width"]}" height="{n["height"]}" rx="12" fill="#fff" stroke="#cbd5e1"/>')
        out.append(f'<text x="{n["x"]+14}" y="{n["y"]+31}" font-family="Inter,Segoe UI,Arial" font-size="13" font-weight="700" fill="#17213a">{esc(_short(n["label"],30))}</text>')
        out.append(f'<text x="{n["x"]+14}" y="{n["y"]+53}" font-family="Inter,Segoe UI,Arial" font-size="10" fill="#64748b">{esc(" · ".join(reqs[:3]) if reqs else "Requirement-derived")}</text>')
    out.append('</svg>'); return ''.join(out)


def add_diagrams(candidates, requirement_records=None):
    for c in candidates:
        tmp = dict(c)
        if requirement_records:
            tmp["uml_requirements"] = requirement_records
        tmp["capability_requirements_text"] = [item for values in c.get("component_evidence", {}).values() for item in values if isinstance(item, str)]
        c["graph"] = graph_for(c)
        c["plantuml_source"] = plantuml_for(c)
        c["uml"] = uml_for(tmp)
        c["uml_plantuml"] = uml_plantuml(tmp)
        c["uml_svg"] = uml_svg_for(tmp)
        c["diagram_svg"] = svg_for(c)
    return candidates


def _has(profile, *terms):
    text = " ".join(profile.functional_requirements + profile.non_functional_requirements + profile.constraints + profile.technology_preferences).lower()
    return any(t in text for t in terms)


def system_design_framework(profile, candidate):
    """Build a runtime request/data-flow framework from the actual requirement profile.
    Infrastructure nodes appear only when the requirements justify them.
    """
    tags=set(profile.tags); nodes=[]; edges=[]
    scale_numbers=[int(x.replace(",","")) for x in re.findall(r"\b\d[\d,]*\b", profile.expected_users or "") if x.replace(",","").isdigit()]
    large_user_base=bool(scale_numbers and max(scale_numbers)>10000)
    def add(label, kind, reason, reqs=None):
        if label not in [n["label"] for n in nodes]:
            nodes.append({"id":f"F{len(nodes)+1}","label":label,"kind":kind,"reason":reason,"requirements":reqs or []})
        return next(n["id"] for n in nodes if n["label"]==label)
    def link(a,b,label="request"):
        if a and b and not any(e["from"]==a and e["to"]==b for e in edges): edges.append({"from":a,"to":b,"label":label})
    req_ids=lambda words:[f"R{i+1}" for i,r in enumerate(profile.functional_requirements+profile.non_functional_requirements) if any(w in r.lower() for w in words)]
    client=add("User / Client", "actor", "External user or client entry point derived from the system intent.")
    previous=client
    if _has(profile,"global", "worldwide", "multi-region", "multiple regions"):
        n=add("Global DNS / Traffic Routing","routing","Global access or multi-region deployment is explicitly required."); link(previous,n); previous=n
    if _has(profile,"web", "browser", "frontend", "portal") and ("scalability" in tags or "low_latency" in tags or "bursty" in tags or large_user_base):
        n=add("CDN / Edge Cache","edge","Web delivery plus scale/latency/burst requirements justify edge caching.",req_ids(["latency","traffic","scale","users"])); link(previous,n); previous=n
    if "scalability" in tags or "availability" in tags or large_user_base:
        n=add("Load Balancer","edge","Horizontal scaling or availability requirements require traffic distribution.",req_ids(["scale","traffic","availability","uptime"])); link(previous,n); previous=n
    if "security" in tags:
        n=add("WAF / Security Boundary","security","Security/privacy requirements justify an explicit ingress protection boundary.",profile.security_drivers[:4]); link(previous,n); previous=n
    edge_label = "API Gateway / Edge" if "API Gateway / Edge" in candidate.get("components", []) else ("API Gateway" if "API Gateway" in candidate.get("components", []) else None)
    if edge_label:
        n=add(edge_label,"gateway","Candidate architecture exposes an API edge boundary.",req_ids(["api","access","request"])); link(previous,n); previous=n
    if "security" in tags or any(x in candidate.get("components", []) for x in ("Identity & Access","Identity Provider")):
        n=add("Identity & Access","security","Authentication/authorization is required by the supplied security and access requirements.",profile.security_drivers[:4]); link(previous,n,"authenticate/authorize"); previous=n
    # Cache is a data-plane optimization, not a duplicate system layer.
    if "scalability" in tags or "low_latency" in tags or "read_heavy" in tags:
        n=add("Distributed Cache","data","Scale, latency or read-heavy requirements justify cache-aside/read-through optimization.",req_ids(["latency","scale","read","traffic"])); link(previous,n,"cache lookup"); previous=n
    domain=[x for x in candidate.get("components", []) if _layer(x)=="domain" and x not in ("Application Modules","Domain Services","Functions")]
    if not domain: domain=[x for x in candidate.get("components", []) if _layer(x)=="domain"][:1]
    for d in domain[:8]:
        n=add(d,"business","Business capability generated from a functional requirement.",candidate.get("component_requirements",{}).get(d,[])[:8]); link(previous,n,"invoke capability")
    if any(x in candidate.get("components", []) for x in ("Durable Event Broker","Kafka","RabbitMQ","Apache Pulsar","NATS","Amazon SQS","Pub/Sub")):
        broker=next(x for x in candidate.get("components", []) if x in ("Durable Event Broker","Kafka","RabbitMQ","Apache Pulsar","NATS","Amazon SQS","Pub/Sub"))
        n=add(broker,"messaging","Asynchronous/event-driven behavior was detected in the requirements.",req_ids(["async","event","notification","stream"]));
        for d in domain[:4]: link(next(n2["id"] for n2 in nodes if n2["label"]==d),n,"publish event")
    data=[x for x in candidate.get("data_stores", []) if x]
    for d in data[:6]:
        n=add(d,"data","Persistence or data-access requirement detected; vendor appears only when explicitly required or justified.",candidate.get("component_requirements",{}).get(d,[])[:8]);
        for x in nodes:
            if x["kind"]=="business": link(x["id"],n,"read/write")
    if "auditability" in tags and "Audit & Compliance" in candidate.get("components", []):
        n=add("Audit & Compliance","control","Auditability/compliance is an explicit architectural driver.",req_ids(["audit","compliance","history"]));
        for x in nodes:
            if x["kind"] in ("gateway","business","security"): link(x["id"],n,"audit")
    if "availability" in tags or _has(profile,"disaster recovery","backup","failover"):
        n=add("Backup / Disaster Recovery","resilience","Availability, failover, backup or disaster recovery requirements justify recovery infrastructure.",req_ids(["availability","failover","backup","disaster","recovery"]));
        for x in nodes:
            if x["kind"]=="data": link(x["id"],n,"backup/restore")
    if "observability" in tags or any(x in candidate.get("components", []) for x in ("Observability","Monitoring")):
        n=add("Observability","control","Monitoring/observability is explicitly requested or inferred as an operational requirement.",req_ids(["observability","monitor","metric","log","trace"]));
        for x in nodes:
            if x["kind"] in ("gateway","business","messaging"): link(x["id"],n,"telemetry")
    business=[n for n in nodes if n["kind"]=="business"]
    data_nodes=[n for n in nodes if n["kind"]=="data"]
    front=[n["label"] for n in nodes if n["kind"] in ("actor","routing","edge","gateway","security")]
    cache=[n for n in data_nodes if "cache" in n["label"].lower()]
    if cache: front.append(cache[0]["label"])
    if business: front.append(f"Business Capabilities ({len(business)})")
    persistence=[n for n in data_nodes if n not in cache and "backup" not in n["label"].lower() and "observability" not in n["label"].lower()]
    if persistence: front.append(f"Data & Persistence ({len(persistence)})")
    return {"nodes":nodes,"edges":edges,"request_path":front,"principles":["Only requirement-justified infrastructure is shown.","Functional capabilities remain distinct from infrastructure concerns.","The request path is separated from the multi-agent decision process."]}


def agent_decision_framework(profile, candidates):
    candidate_nodes=[{"id":c["candidate_id"],"label":c["name"],"kind":"candidate","evidence":c.get("description","")} for c in candidates]
    reviewers=["Security Reviewer","Scalability Reviewer","Performance Reviewer","Reliability Reviewer","Cost Reviewer","Maintainability Reviewer"]
    return {
        "stages":[
            {"id":"requirements","label":"Requirement Intelligence","agents":["Requirement Analyst","Requirement Clarifier","Architectural Driver Analyst"],"evidence":profile.drivers},
            {"id":"knowledge","label":"Architecture Knowledge","agents":["Architecture Knowledge Agent"],"evidence":profile.tags},
            {"id":"competition","label":"Candidate Competition","agents":["Architecture Generator"],"candidates":candidate_nodes},
            {"id":"debate","label":"Adversarial Debate","agents":reviewers,"rule":"Each reviewer evaluates every candidate against the same requirement profile."},
            {"id":"refine","label":"Refinement & Verification","agents":["Refinement Agent","Architecture Consistency Verifier"],"rule":"Findings must create an observable architecture change or be rejected with evidence."},
            {"id":"optimize","label":"Multi-Objective Pareto Analysis","agents":["Multi-Objective Evaluator","Pareto Optimizer"],"rule":"Candidates are compared across requirement-derived objectives; non-dominated candidates remain in the frontier."},
            {"id":"judge","label":"Architecture Judge","agents":["Architecture Judge"],"rule":"Selects using constraints, evidence, coverage, risks and objective fit; not a hardcoded template."},
            {"id":"explain","label":"Explainability & Traceability","agents":["Explainability Agent","Diagram Agent","Traceability Agent","Confidence & Research Metrics Agent"],"rule":"Every final decision links back to requirements and evidence."},
        ],
        "competition_rule":"Candidates are independent alternatives. Reviewers challenge all candidates before refinement and Pareto selection.",
        "human_gate":"Human decision-maker reviews evidence and records the final decision."
    }


def _svg_wrap(body, width, height):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="#ffffff"/>{body}</svg>'


def uml_svg_for(c):
    """Render UML with explicit layout/ports so actors, classes and lifelines never overlap."""
    u=c.get("uml") or uml_for(c)
    esc=lambda x: html.escape(str(x),quote=True)
    font='Inter,Segoe UI,Arial'

    # ---------- USE CASE ----------
    uc=u["use_case"]; usecases=uc.get("use_cases",[])[:10]; actors=uc.get("actors",[])[:5]
    if not actors: actors=['System User']
    # One vertical stack per actor. This intentionally favors readability over compactness:
    # no actor can overlap another actor and no association can cross another use-case ellipse.
    groups={a:[x for x in usecases if x.get('actor')==a] for a in actors}
    ordered=[]
    for a in actors: ordered.extend(groups.get(a,[]))
    cell_w,cell_h=355,82
    boundary_x=320; boundary_y=92; boundary_w=1125
    total_rows=max(1,len(ordered)); boundary_h=72+total_rows*cell_h
    w=1500; h=boundary_y+boundary_h+55
    body=[f'<text x="42" y="40" font-family="{font}" font-size="24" font-weight="800" fill="#17213a">Use Case Diagram</text>',
          f'<text x="42" y="65" font-family="{font}" font-size="11" fill="#64748b">Only actionable functional requirements become user goals; quality attributes remain outside the use-case model.</text>',
          f'<rect x="{boundary_x}" y="{boundary_y}" width="{boundary_w}" height="{boundary_h}" rx="18" fill="#fbfcff" stroke="#aebed2" stroke-width="1.5"/>',
          f'<text x="{boundary_x+20}" y="{boundary_y+27}" font-family="{font}" font-size="10" font-weight="900" letter-spacing="1" fill="#536a88">SYSTEM BOUNDARY · SUBMITTED SYSTEM</text>']
    # Assign each use case a unique row.
    pos={}; actor_rows={a:[] for a in actors}
    for i,item in enumerate(ordered):
        cx=boundary_x+300; cy=boundary_y+82+i*cell_h
        pos[item['id']]=(cx,cy); actor_rows[item['actor']].append(cy)
        body += [f'<ellipse cx="{cx}" cy="{cy}" rx="145" ry="25" fill="#fff" stroke="#6355e6" stroke-width="1.7"/>',
                 f'<text x="{cx}" y="{cy+3}" text-anchor="middle" font-family="{font}" font-size="9.5" font-weight="700" fill="#263a5c">{esc(_short(item["name"],40))}</text>']
    actor_pos={}
    for i,a in enumerate(actors):
        ys=actor_rows.get(a,[])
        if not ys: continue
        ay=sum(ys)/len(ys); actor_pos[a]=(120,ay)
        body += [f'<circle cx="120" cy="{ay-25}" r="10" fill="none" stroke="#315d96" stroke-width="2.2"/>',
                 f'<line x1="120" y1="{ay-15}" x2="120" y2="{ay+14}" stroke="#315d96" stroke-width="2.2"/>',
                 f'<line x1="104" y1="{ay-2}" x2="136" y2="{ay-2}" stroke="#315d96" stroke-width="2.2"/>',
                 f'<line x1="120" y1="{ay+14}" x2="108" y2="{ay+34}" stroke="#315d96" stroke-width="2.2"/>',
                 f'<line x1="120" y1="{ay+14}" x2="132" y2="{ay+34}" stroke="#315d96" stroke-width="2.2"/>']
        words=str(a).split(); lines=[]; line=''
        for word in words:
            if len(line)+len(word)+1>15 and line: lines.append(line); line=word
            else: line=(line+' '+word).strip()
        if line: lines.append(line)
        for j,line in enumerate(lines[:2]):
            body.append(f'<text x="120" y="{ay+53+j*14}" text-anchor="middle" font-family="{font}" font-size="10" font-weight="800" fill="#243b5e">{esc(line)}</text>')
    # Each actor gets one dedicated vertical association rail. Because use cases are stacked,
    # the rail only serves that actor's own rows and never crosses an ellipse.
    for i,a in enumerate(actors):
        if a not in actor_pos: continue
        ax,ay=actor_pos[a]; lane=boundary_x-28-i*24
        for item in groups.get(a,[]):
            cx,cy=pos[item['id']]
            body.append(f'<path d="M 137 {ay} L {lane} {ay} L {lane} {cy} L {cx-145} {cy}" fill="none" stroke="#8292a8" stroke-width="1.15" stroke-linejoin="round"/>')
    use_svg=_svg_wrap(''.join(body),w,h)

    # ---------- CLASS DIAGRAM ----------
    cl=u["class"]; classes=cl.get("classes",[])[:14]; relations=cl.get('relations',[])[:28]
    cols=3; cw=330; ch=154; gapx=65; gapy=82; left=40; top=100
    rows=max(1,(len(classes)+cols-1)//cols); grid_w=cols*cw+(cols-1)*gapx
    w=max(1220,left+grid_w+100+max(0,len(relations))*5); h=top+rows*(ch+gapy)+36
    body=[f'<defs><marker id="umlArrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#64758e"/></marker></defs>',
          f'<text x="34" y="38" font-family="{font}" font-size="24" font-weight="800" fill="#17213a">Domain Class Diagram</text>',
          f'<text x="34" y="63" font-family="{font}" font-size="11" fill="#64748b">Domain entities and associations are traced to co-occurring requirements. Solid lines represent associations; no unsupported inheritance or composition is fabricated.</text>']
    pos={}
    for i,x in enumerate(classes):
        col=i%cols; row=i//cols; x0=left+col*(cw+gapx); y0=top+row*(ch+gapy); pos[x['name']]={'x':x0,'y':y0,'col':col,'row':row}
    # Route all associations through the whitespace between cards/rows. Draw edges first so they
    # cannot visually overwrite class text; each route starts and ends on the nearest class border.
    row_lane_counts={}
    for ri,r in enumerate(relations):
        a=r.get('from'); b=r.get('to')
        if a not in pos or b not in pos or a==b: continue
        A=pos[a]; B=pos[b]
        if A['row']==B['row'] and abs(A['col']-B['col'])==1:
            if A['col']<B['col']: sx,sy,tx,ty=A['x']+cw,A['y']+ch/2,B['x'],B['y']+ch/2
            else: sx,sy,tx,ty=A['x'],A['y']+ch/2,B['x']+cw,B['y']+ch/2
            d=f'M {sx} {sy} L {tx} {ty}'
            lx=(sx+tx)/2; ly=sy-8
        elif A['row']==B['row']:
            # Non-adjacent same-row classes: route below the row, outside every class box.
            key=('same',A['row']); lane=row_lane_counts.get(key,0); row_lane_counts[key]=lane+1
            gy=top+(A['row']+1)*(ch+gapy)-gapy/2+lane*9
            sx=A['x']+cw/2; tx=B['x']+cw/2
            d=f'M {sx} {A["y"]+ch} L {sx} {gy} L {tx} {gy} L {tx} {B["y"]+ch}'
            lx=(sx+tx)/2; ly=gy-4
        else:
            # For cross-row relationships, use a dedicated outer channel and the whitespace
            # immediately below each endpoint row. This avoids routing across intermediate cards.
            key=('cross',min(A['row'],B['row']),max(A['row'],B['row']))
            lane=row_lane_counts.get(key,0); row_lane_counts[key]=lane+1
            channel_x=left+grid_w+24+lane*5
            downward=A['row']<B['row']
            if downward:
                sy=A['y']+ch; ty=B['y']
                gy1=top+(A['row']+1)*(ch+gapy)-gapy/2
                gy2=top+B['row']*(ch+gapy)-gapy/2
            else:
                sy=A['y']; ty=B['y']+ch
                gy1=top+A['row']*(ch+gapy)-gapy/2
                gy2=top+(B['row']+1)*(ch+gapy)-gapy/2
            sx=A['x']+cw/2; tx=B['x']+cw/2
            d=f'M {sx} {sy} L {sx} {gy1} L {channel_x} {gy1} L {channel_x} {gy2} L {tx} {gy2} L {tx} {ty}'
            lx=channel_x; ly=(gy1+gy2)/2-4
        body.append(f'<path d="{d}" fill="none" stroke="#64758e" stroke-width="1.35" stroke-linejoin="round"/>')
        label=_short(r.get('label','associated with'),22)
        body.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-family="{font}" font-size="7.2" fill="#53657d" stroke="#ffffff" stroke-width="3" paint-order="stroke">{esc(label)}</text>')
    # Draw class cards over edge paths, keeping every connector outside card interiors.
    for x in classes:
        q=pos[x['name']]; x0=q['x']; y0=q['y']
        body += [f'<rect x="{x0}" y="{y0}" width="{cw}" height="{ch}" rx="12" fill="#ffffff" stroke="#315d96" stroke-width="1.7"/>',
                 f'<rect x="{x0}" y="{y0}" width="{cw}" height="37" rx="12" fill="#edf4ff"/>',
                 f'<text x="{x0+cw/2}" y="{y0+24}" text-anchor="middle" font-family="{font}" font-size="14" font-weight="800" fill="#1f4778">{esc(x["name"])}</text>']
        yy=y0+57
        for a in x.get('attributes',[])[:4]: body.append(f'<text x="{x0+15}" y="{yy}" font-family="{font}" font-size="9.5" fill="#52627d">- {esc(a)}</text>'); yy+=15
        body.append(f'<line x1="{x0}" y1="{y0+98}" x2="{x0+cw}" y2="{y0+98}" stroke="#d8e0ea"/>'); yy=y0+120
        for op in x.get('operations',[])[:2]: body.append(f'<text x="{x0+15}" y="{yy}" font-family="{font}" font-size="9.5" fill="#28385a">+ {esc(op)}</text>'); yy+=14
    # A compact legend helps reviewers distinguish a grounded association from other UML semantics.
    body.append(f'<text x="{left}" y="{h-12}" font-family="{font}" font-size="9" fill="#64748b">Legend: ─ association · relationship evidence is available in generated PlantUML source</text>')
    class_svg=_svg_wrap(''.join(body),w,h)

    # ---------- SEQUENCE DIAGRAM ----------
    sq=u['sequence']; parts=sq.get('participants',[])[:6]; msgs=sq.get('messages',[])[:8]
    if not parts: parts=['System User']
    n=len(parts); gap=205; w=max(1100,100+(n-1)*gap+100); h=max(430,175+len(msgs)*62)
    body=[f'<defs><marker id="seqArrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0,0 L9,4 L0,8 z" fill="#596b85"/></marker></defs>',
          f'<text x="30" y="38" font-family="{font}" font-size="24" font-weight="800" fill="#17213a">Requirement-Specific Sequence Diagram</text>',
          f'<text x="30" y="63" font-family="{font}" font-size="11" fill="#64748b">Scenario derived from: {esc(_short(sq.get("requirement",""),160))}</text>']
    xs={}
    for i,pname in enumerate(parts):
        x=60+i*gap; xs[pname]=x
        body += [f'<rect x="{x-72}" y="84" width="144" height="42" rx="9" fill="#edf4ff" stroke="#315d96"/>',
                 f'<text x="{x}" y="110" text-anchor="middle" font-family="{font}" font-size="9.5" font-weight="800" fill="#1f4778">{esc(_short(pname,22))}</text>',
                 f'<line x1="{x}" y1="126" x2="{x}" y2="{h-34}" stroke="#a7b4c6" stroke-width="1.2" stroke-dasharray="6 5"/>']
    for i,m in enumerate(msgs):
        if m.get('from') not in xs or m.get('to') not in xs: continue
        y=155+i*62; x1=xs[m['from']]; x2=xs[m['to']]
        if x1==x2:
            body.append(f'<path d="M {x1} {y} L {x1+55} {y} L {x1+55} {y+28} L {x1} {y+28}" fill="none" stroke="#596b85" stroke-width="1.6" marker-end="url(#seqArrow)"/>')
            tx=x1+65
        else:
            direction=1 if x2>x1 else -1
            body.append(f'<line x1="{x1+direction*5}" y1="{y}" x2="{x2-direction*5}" y2="{y}" stroke="#596b85" stroke-width="1.6" marker-end="url(#seqArrow)"/>')
            tx=(x1+x2)/2
        body.append(f'<text x="{tx}" y="{y-9}" text-anchor="middle" font-family="{font}" font-size="8.5" fill="#2e405e">{esc(_short(m.get("label",""),48))}</text>')
    body.append(f'<text x="30" y="{h-12}" font-family="{font}" font-size="9" fill="#7a8aa1">Messages are derived from the selected functional scenario and the candidate components mapped to that requirement.</text>')
    seq_svg=_svg_wrap(''.join(body),w,h)
    return {"use_case":use_svg,"class":class_svg,"sequence":seq_svg}

