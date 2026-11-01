from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape
from fastapi.responses import Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, LongTable, Flowable

styles = getSampleStyleSheet()

def add_style(name, parent, **kwargs):
    if name not in styles.byName:
        styles.add(ParagraphStyle(name=name, parent=styles[parent], **kwargs))

NAVY = colors.HexColor('#12395f')
NAVY2 = colors.HexColor('#173f68')
TEXT = colors.HexColor('#394b63')
MUTED = colors.HexColor('#64748b')
GRID = colors.HexColor('#d8e1eb')
LIGHT = colors.HexColor('#f4f7fa')

add_style('RTitle','Title',fontName='Helvetica-Bold',fontSize=18,leading=21,textColor=NAVY,spaceAfter=4)
add_style('RSubtitle','Normal',fontSize=8.4,leading=11,textColor=MUTED,spaceAfter=5)
add_style('RH1','Heading1',fontName='Helvetica-Bold',fontSize=13.5,leading=16,textColor=NAVY,spaceBefore=5,spaceAfter=6)
add_style('RH2','Heading2',fontName='Helvetica-Bold',fontSize=9.5,leading=11.5,textColor=NAVY2,spaceBefore=5,spaceAfter=3)
add_style('RBody','BodyText',fontSize=7.25,leading=9.4,textColor=TEXT,spaceAfter=3)
add_style('RSmall','BodyText',fontSize=6.35,leading=8.1,textColor=TEXT,spaceAfter=2)
add_style('RTiny','BodyText',fontSize=5.7,leading=7,textColor=MUTED,spaceAfter=1)
add_style('RMetric','Normal',fontName='Helvetica-Bold',fontSize=12,leading=14,textColor=NAVY,alignment=TA_CENTER)
add_style('RMetricLabel','Normal',fontSize=5.8,leading=7,textColor=MUTED,alignment=TA_CENTER)
add_style('RMono','Code',fontName='Courier',fontSize=5.5,leading=6.6,textColor=TEXT)


def safe(v):
    return escape(str(v if v is not None else ''))


def num(v, default=0):
    try: return float(v)
    except Exception: return float(default)


def fmt(v):
    if v is None or v == '': return '—'
    try:
        x=float(v)
        return f'{x:.1f}' if x % 1 else f'{int(x)}'
    except Exception:
        return str(v)


def pct(v):
    x=num(v)
    return f'{x:.1f}%'


def compact_text(v, n=300):
    s=str(v if v is not None else '').strip()
    return s if len(s)<=n else s[:n-1].rstrip()+'…'


def bullet_list(items, limit=18, style='RBody'):
    out=[]
    for x in (items or [])[:limit]:
        if isinstance(x, dict):
            x=x.get('description') or x.get('title') or x.get('name') or x.get('text') or ''
        if str(x).strip(): out.append(Paragraph('• '+safe(compact_text(x,420)), styles[style]))
    return out


def cell(v, style='RSmall'):
    return Paragraph(safe(compact_text(v,520)), styles[style])


def table(data, widths, header=True, repeat=1, font=6.35):
    rows=[]
    for row in data:
        cooked=[]
        for v in row:
            cooked.append(v if isinstance(v, Flowable) else cell(v))
        rows.append(cooked)
    cls=LongTable if len(rows)>12 else Table
    t=cls(rows,colWidths=widths,repeatRows=repeat if header else 0,splitByRow=1,hAlign='LEFT')
    commands=[
        ('GRID',(0,0),(-1,-1),0.35,GRID),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
    ]
    if header:
        commands += [('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]
    t.setStyle(TableStyle(commands))
    return t


def heading(story, n, title, intro=None):
    story.append(Paragraph(f'{n}. {safe(title)}', styles['RH1']))
    if intro: story.append(Paragraph(safe(intro), styles['RBody']))


def build_pdf(result):
    project=result.get('project_name') or 'Architecture Decision Report'
    profile=result.get('requirement_profile') or {}
    metrics=result.get('research_metrics') or {}
    candidates=result.get('candidates') or []
    rec=result.get('recommendation') or (candidates[0] if candidates else {})
    trace=result.get('traceability') or []
    explanations=result.get('explanations') or []
    exp=next((x for x in explanations if x.get('candidate_id')==rec.get('candidate_id')), {})
    optimization=result.get('optimization') or {}
    convergence=result.get('convergence') or {}

    functional=profile.get('functional_requirements') or []
    quality=profile.get('non_functional_requirements') or profile.get('quality_attributes') or []
    constraints=profile.get('constraints') or []
    prefs=profile.get('technology_preferences') or []
    drivers=profile.get('drivers') or profile.get('architectural_drivers') or []
    records=profile.get('requirement_records') or []

    coverage=num(metrics.get('requirement_coverage'))
    confidence=num(metrics.get('confidence'))
    selected_score=num((rec.get('scores') or {}).get('weighted_total'))
    pareto=sum(1 for c in candidates if c.get('is_pareto_optimal'))
    if not pareto: pareto=int(num(metrics.get('pareto_frontier_size')))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(GRID); canvas.line(15*mm,11*mm,195*mm,11*mm)
        canvas.setFont('Helvetica',5.8); canvas.setFillColor(MUTED)
        canvas.drawString(15*mm,6.5*mm,'ARCHITECTURE DECISION REPORT · SYSTEM ARCHITECT')
        canvas.drawRightString(195*mm,6.5*mm,f'Page {doc.page}')
        canvas.restoreState()

    buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=15*mm,rightMargin=15*mm,topMargin=13*mm,bottomMargin=15*mm,
                          title=f'ARCHDS · Architecture Decision Report · {project}',author='System Architect Decision Engine',
                          subject='Requirement-driven competitive architecture decision report')
    story=[]

    # PAGE 1 — reference-style requirement intelligence
    story += [Paragraph('ARCHDS · ARCHITECTURE DECISION REPORT',styles['RTiny']),
              Paragraph(safe(project),styles['RTitle']),
              Paragraph('Requirement-driven competitive synthesis · multi-agent review · Pareto evidence · Digital Twin · human decision gate',styles['RSubtitle'])]
    metrics_table=[
        [Paragraph('Decision confidence',styles['RMetricLabel']),Paragraph('Requirement coverage',styles['RMetricLabel']),Paragraph('Final score',styles['RMetricLabel']),Paragraph('Pareto frontier',styles['RMetricLabel'])],
        [Paragraph(f'{confidence:.1f}%',styles['RMetric']),Paragraph(f'{coverage:.1f}%',styles['RMetric']),Paragraph(f'{selected_score:.2f}',styles['RMetric']),Paragraph(str(pareto),styles['RMetric'])]
    ]
    story.append(table(metrics_table,[44*mm]*4,header=False))
    heading(story,1,'Requirement intelligence',f'Architecture readiness: {pct(profile.get("architecture_readiness", profile.get("completeness",0)))}')
    story.append(Paragraph('Architectural drivers',styles['RH2']))
    story += bullet_list(drivers,16)
    story.append(Paragraph('Functional requirements',styles['RH2']))
    # Prefer the actual submitted functional list; if unavailable, reconstruct from requirement records.
    fr=functional
    if not fr:
        fr=[r.get('description','') for r in records if str(r.get('type','')).lower() in ('functional','fr')]
    story += bullet_list(fr,22)

    # PAGE 2
    story.append(PageBreak())
    heading(story,'','',None) if False else None
    story.append(Paragraph('Quality attributes',styles['RH2']))
    story += bullet_list(quality,20)
    story.append(Paragraph('Constraints',styles['RH2']))
    story += bullet_list(constraints,18)
    story.append(Paragraph('Technology preferences',styles['RH2']))
    story += bullet_list(prefs,18)
    story.append(Paragraph('Requirement quality',styles['RH2']))
    qrows=[['Completeness','Specificity','Consistency','Ambiguity','Architecture readiness'],
           [pct(profile.get('completeness')),pct(profile.get('specificity')),pct(profile.get('consistency')),pct(profile.get('ambiguity')),pct(profile.get('architecture_readiness',profile.get('completeness')) )]]
    story.append(table(qrows,[35*mm]*5))
    story.append(Spacer(1,3))
    heading(story,2,'Competitive architecture decision',f'{safe(rec.get("name") or "No architecture selected")} · {safe(rec.get("pattern_key") or "architecture pattern")}')
    story.append(Paragraph('Requirement-adapted '+safe(rec.get('description') or 'Selected architecture generated from the submitted requirement profile and architectural drivers.') ,styles['RBody']))
    story.append(Paragraph('Selection policy',styles['RH2']))
    story.append(Paragraph('Hard constraints → critical findings → Pareto status → requirement coverage → weighted objectives.',styles['RBody']))
    story.append(Paragraph('Selected architecture capability map',styles['RH2']))
    comps=rec.get('components') or []
    story += bullet_list(comps,16)

    # PAGE 3
    story.append(PageBreak())
    story.append(Paragraph('Candidate Pattern Score Pareto Coverage',styles['RH2']))
    rows=[['Candidate','Pattern','Score','Pareto','Coverage']]
    for c in sorted(candidates,key=lambda x:num((x.get('scores') or {}).get('weighted_total')),reverse=True)[:10]:
        covmap=c.get('requirement_coverage') or {}
        cov=(sum(bool(x) for x in covmap.values())/max(1,len(covmap)))*100
        rows.append([c.get('name',''),c.get('pattern_key',''),fmt((c.get('scores') or {}).get('weighted_total')),'Yes' if c.get('is_pareto_optimal') else 'No',f'{cov:.1f}%'])
    if len(rows)>1: story.append(table(rows,[58*mm,34*mm,25*mm,25*mm,30*mm]))
    story.append(Paragraph('Accepted trade-offs',styles['RH2']))
    story += bullet_list(rec.get('disadvantages') or rec.get('tradeoffs') or [],8)
    story.append(Paragraph('Risk findings',styles['RH2']))
    findings=rec.get('critique_findings') or []
    if findings:
        riskrows=[['Severity','Finding','Affected requirements']]
        for f in findings[:8]: riskrows.append([f.get('severity','REVIEW'),f.get('description') or f.get('title',''),', '.join(f.get('affected_requirements') or [])])
        story.append(table(riskrows,[23*mm,105*mm,44*mm]))
    else:
        story.append(Paragraph('No unresolved specialist/adversarial risk findings were recorded for the selected candidate.',styles['RBody']))
    story.append(Paragraph('Evidence for the recommendation',styles['RH2']))
    evidence=trace[:10]
    if evidence:
        for x in evidence:
            rid=x.get('requirement_id') or ''
            req=x.get('requirement') or ''
            comps=x.get('components') or []
            if not comps:
                links=x.get('candidate_links') or []
                link=next((l for l in links if l.get('candidate_id')==rec.get('candidate_id')),{})
                comps=link.get('evidence') or []
            story.append(Paragraph(f'• <b>{safe(rid)}</b> is addressed by <b>{safe(", ".join(comps[:4]) or "requirement-derived architecture boundary")}</b> because the requirement is: {safe(compact_text(req,380))}',styles['RSmall']))

    # PAGE 4
    story.append(PageBreak())
    heading(story,3,'Explainability & traceability','The system explains each architectural choice through the submitted requirement, the architectural driver, the mapped component and the resulting decision evidence. This evidence chain is analysis-specific; it is not a fixed explanation template.')
    trrows=[['Req','Submitted requirement','Architecture evidence']]
    for x in trace[:20]:
        rid=x.get('requirement_id','')
        req=x.get('requirement','')
        comps=x.get('components') or []
        driver=x.get('architectural_driver') or ''
        evidence=', '.join(comps[:5]) or ', '.join(x.get('evidence') or [])
        trrows.append([rid,req,f'{driver}; {evidence}'])
    if len(trrows)>1: story.append(table(trrows,[17*mm,91*mm,67*mm]))
    story.append(Paragraph('Selected decision rationale',styles['RH2']))
    story.append(Paragraph(safe(exp.get('rationale') or 'The selected architecture provides the strongest combined evidence across constraints, critical findings, Pareto efficiency, requirement coverage and weighted objectives.'),styles['RBody']))
    story.append(Paragraph('Digital Twin & What-If laboratory',styles['RH2']))
    story.append(Paragraph('The Digital Twin is reconstructed from the selected architecture graph and submitted requirements. Scenarios change simulation inputs and produce propagation, metric deltas and mitigation recommendations.',styles['RBody']))
    try:
        from .digital_twin import scenario_catalog
        scenarios=scenario_catalog(profile,rec)
    except Exception:
        scenarios=[]
    twinrows=[['Scenario','Trigger','Requirement relevance','Proposed response']]
    response_map={
      'traffic_surge':'Autoscaling + queue smoothing','component_failure':'Failover + circuit breaker','dependency_failure':'Timeout + fallback isolation',
      'latency_pressure':'Cache + request-path optimization','regional_outage':'Multi-region failover','security_pressure':'Policy + rate limiting + audit',
      'data_growth':'Partitioning + indexing','flash_sale':'Burst autoscaling + queueing','disaster_recovery':'Recovery automation + restore validation',
      'cost_pressure':'Right-sizing + workload tiering','deployment_rollback':'Canary + health-gated rollback','observability_loss':'Redundant telemetry + audit retention'
    }
    for s in scenarios[:8]:
        relevance=s.get('requirement_relevance') or s.get('relevance') or 'HIGH'
        twinrows.append([s.get('title',''),s.get('change',''),relevance,response_map.get(s.get('id'),'Requirement-preserving adaptive response')])
    if len(twinrows)>1: story.append(table(twinrows,[44*mm,55*mm,30*mm,46*mm]))

    # PAGE 5
    story.append(PageBreak())
    twinrows2=[['Scenario','Trigger','Requirement relevance','Proposed response']]
    for s in scenarios[8:18]:
        relevance=s.get('requirement_relevance') or s.get('relevance') or 'HIGH'
        twinrows2.append([s.get('title',''),s.get('change',''),relevance,response_map.get(s.get('id'),'Requirement-preserving adaptive response')])
    if len(twinrows2)>1: story.append(table(twinrows2,[44*mm,55*mm,30*mm,46*mm]))
    story.append(Paragraph('5. Closed-loop delivery lab',styles['RH1']))
    story.append(Paragraph('The system can translate the selected candidate into deployment-oriented Terraform and Kubernetes starting artifacts and run a local structural validation/feedback pass. These artifacts are research/development starting points, not a claim that infrastructure has been provisioned.',styles['RBody']))
    story.append(Paragraph('Derived runtime components',styles['RH2']))
    story += bullet_list(comps,22)
    story.append(Paragraph('Validation model',styles['RH2']))
    story += bullet_list(['Balanced Terraform blocks','Kubernetes API objects and selectors','Deployment selector consistency','Architecture-to-deployment component consistency','Feedback regeneration when structural validation fails'],10)
    # Research / refinement evidence, compact
    story.append(Paragraph('Decision evolution evidence',styles['RH2']))
    evrows=[['Initial score','Final score','Improvement','Convergence','Agent agreement'],
            [fmt(metrics.get('initial_score')),fmt(metrics.get('final_score')),f'{num(metrics.get("refinement_improvement_percent")):.2f}%',safe(convergence.get('status','NOT_RECORDED')),pct(metrics.get('agent_agreement'))]]
    story.append(table(evrows,[35*mm]*5))

    # PAGE 6
    story.append(PageBreak())
    heading(story,6,'Decision record')
    story.append(Paragraph(f'<b>Selected architecture: {safe(rec.get("name") or "No recommendation")}</b>',styles['RBody']))
    story.append(Paragraph('Requirement-adapted '+safe(rec.get('description') or 'Selected from the generated architecture alternatives using requirement evidence.'),styles['RBody']))
    story.append(Paragraph('Advantages',styles['RH2']))
    story += bullet_list(rec.get('advantages') or [],8)
    story.append(Paragraph('Trade-offs',styles['RH2']))
    story += bullet_list(rec.get('disadvantages') or [],8)
    story.append(Paragraph('Optimization evidence',styles['RH2']))
    optrows=[['Candidate','Score','Pareto','Coverage','Verified']]
    for c in sorted(candidates,key=lambda x:num((x.get('scores') or {}).get('weighted_total')),reverse=True)[:10]:
        covmap=c.get('requirement_coverage') or {}
        cov=sum(bool(x) for x in covmap.values())/max(1,len(covmap))*100
        optrows.append([c.get('name',''),fmt((c.get('scores') or {}).get('weighted_total')),'Yes' if c.get('is_pareto_optimal') else 'No',f'{cov:.1f}%', 'Yes' if c.get('verified') else 'No'])
    if len(optrows)>1: story.append(table(optrows,[55*mm,27*mm,27*mm,35*mm,28*mm]))
    story.append(Paragraph('Architecture accountability',styles['RH2']))
    story.append(Paragraph('ARCHDS recommends from evidence. The human decision-maker remains accountable for the final architecture. Security approval, operational readiness, capacity validation, legal/compliance review and production authorization remain responsibilities of the designated engineering organization.',styles['RBody']))
    story.append(Paragraph(f'Generated {datetime.now().strftime("%d %B %Y, %H:%M")} · Candidate count {len(candidates)} · Pareto frontier {pareto} · Requirement coverage {coverage:.1f}% · Decision confidence {confidence:.1f}%',styles['RTiny']))

    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return buf.getvalue()


def pdf_response(result):
    if hasattr(result,'model_dump'):
        result=result.model_dump()
    data=build_pdf(result)
    return Response(content=data,media_type='application/pdf',headers={
        'Content-Disposition':'attachment; filename="Architecture_Decision_Report.pdf"',
        'Content-Length':str(len(data)),
        'Cache-Control':'no-store, no-cache, must-revalidate',
        'Pragma':'no-cache',
        'X-Architecture-Report':'reference-style-system-architect'
    })
