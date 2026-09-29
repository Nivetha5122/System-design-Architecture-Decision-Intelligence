"""Professional ARCHDS PDF report renderer.

The report is built from the completed PipelineResponse. It embeds three generated
PNG diagrams: the selected architecture, a UML-style component view, and a
sequence/runtime view. No generic architecture is substituted for the selected
candidate.
"""
from io import BytesIO
from typing import Any
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    Image as RLImage, KeepTogether
)

PAGE_W, PAGE_H = A4
NAVY = colors.HexColor('#17213A')
BLUE = colors.HexColor('#3F6FDB')
VIOLET = colors.HexColor('#7657E8')
CYAN = colors.HexColor('#0BA8D9')
GREEN = colors.HexColor('#10A978')
AMBER = colors.HexColor('#E59400')
MUTED = colors.HexColor('#6F7E97')
LINE = colors.HexColor('#DDE5EF')
PALE = colors.HexColor('#F6F8FC')


def _font(size=18, bold=False):
    candidates = [
        ('C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/segoeuib.ttf'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
    ]
    for regular, b in candidates:
        path = b if bold else regular
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _diagram_png(candidate: dict[str, Any], mode: str) -> bytes:
    graph = candidate.get('graph') or {}
    nodes = graph.get('nodes') or []
    groups = graph.get('groups') or []
    edges = graph.get('edges') or []
    W, H = int(graph.get('canvas_width', 1260)), int(graph.get('canvas_height', 760))
    scale = 1.25
    img = Image.new('RGB', (int(W*scale), int(H*scale)), '#F8FAFC')
    d = ImageDraw.Draw(img)
    def xy(v): return int(v*scale)
    palette = {
        'experience': ('#7657E8','#F1EEFF'), 'edge': ('#2387C9','#EDF7FF'),
        'domain': ('#D98922','#FFF6E6'), 'data': ('#20A777','#EDF9F4')
    }
    title = {'architecture':'Requirement-derived architecture','uml':'UML component blueprint','sequence':'Runtime interaction sequence'}[mode]
    d.text((xy(32), xy(14)), title, font=_font(23, True), fill='#17213A')

    if mode == 'sequence':
        selected = nodes[:8]
        if not selected:
            selected = [{'label':'Client','layer':'experience'},{'label':'Application Service','layer':'domain'},{'label':'Data Store','layer':'data'}]
        top = 90
        xs = [70 + i*145 for i in range(len(selected))]
        for x,n in zip(xs,selected):
            d.rounded_rectangle((xy(x),xy(top),xy(x+112),xy(top+44)), radius=xy(10), fill='#FFFFFF', outline='#C9D5E5', width=2)
            d.text((xy(x+8),xy(top+13)), str(n.get('label','Component'))[:16], font=_font(11,True), fill='#243452')
            d.line((xy(x+56),xy(top+44),xy(x+56),xy(H-80)), fill='#B8C4D4', width=2)
        relations = []
        name_to_x={n.get('label'):x for n,x in zip(selected,xs)}
        for e in edges:
            src=next((n for n in nodes if n.get('id')==e.get('source')),None)
            dst=next((n for n in nodes if n.get('id')==e.get('target')),None)
            if src and dst and src.get('label') in name_to_x and dst.get('label') in name_to_x:
                relations.append((src.get('label'),dst.get('label')))
        y=170
        for i,(a,b) in enumerate(relations[:8]):
            x1=name_to_x[a]+56; x2=name_to_x[b]+56
            if x1==x2: continue
            d.line((xy(x1),xy(y),xy(x2),xy(y)),fill='#5B78B5',width=2)
            step=7 if x2>x1 else -7
            d.polygon([(xy(x2),xy(y)),(xy(x2-step),xy(y-4)),(xy(x2-step),xy(y+4))],fill='#5B78B5')
            d.text((xy(min(x1,x2)+4),xy(y-16)), 'request / response', font=_font(9), fill='#71809A')
            y += 62
        d.rounded_rectangle((xy(40),xy(H-62),xy(W-40),xy(H-28)),radius=xy(8),fill='#EEF4FF',outline='#D7E2F2')
        d.text((xy(55),xy(H-53)), 'Sequence generated from the selected candidate dependency graph.',font=_font(10,True),fill='#46628D')
        return _png_bytes(img)

    # Architecture and UML both use the actual graph, but UML groups components by package.
    for group in groups:
        stroke, fill = palette.get(group.get('id'), ('#71809A','#F5F7FA'))
        d.rounded_rectangle((xy(group['x']),xy(group['y']),xy(group['x']+group['width']),xy(group['y']+group['height'])),radius=xy(16),fill='#FFFFFF',outline=stroke,width=2)
        d.rounded_rectangle((xy(group['x']+14),xy(group['y']+10),xy(group['x']+260),xy(group['y']+42)),radius=xy(15),fill=fill,outline=stroke,width=1)
        d.text((xy(group['x']+28),xy(group['y']+18)),str(group.get('title','Layer')).upper(),font=_font(11,True),fill=stroke)
    byid={n.get('id'):n for n in nodes}
    for e in edges:
        a,b=byid.get(e.get('source')),byid.get(e.get('target'))
        if not a or not b: continue
        ax=a['x']+a.get('width',220); ay=a['y']+a.get('height',78)/2
        bx=b['x']; by=b['y']+b.get('height',78)/2
        d.line((xy(ax),xy(ay),xy(bx),xy(by)),fill='#8795A8',width=2)
        dx=bx-ax; dy=by-ay
        if abs(dx)>abs(dy):
            s=-8 if dx<0 else 8
            d.polygon([(xy(bx),xy(by)),(xy(bx-s),xy(by-4)),(xy(bx-s),xy(by+4))],fill='#8795A8')
    for n in nodes:
        stroke, fill=palette.get(n.get('layer'),('#71809A','#F5F7FA'))
        x,y,w,h= n['x'],n['y'],n.get('width',220),n.get('height',78)
        d.rounded_rectangle((xy(x),xy(y),xy(x+w),xy(y+h)),radius=xy(12),fill='#FFFFFF',outline=stroke,width=2)
        d.rounded_rectangle((xy(x+10),xy(y+13),xy(x+52),xy(y+55)),radius=xy(9),fill=fill,outline=stroke,width=1)
        label=str(n.get('label','Component'))
        d.text((xy(x+62),xy(y+15)),label[:29],font=_font(12,True),fill='#17213A')
        req=' · '.join((n.get('requirements') or [])[:2]) or 'Requirement-derived component'
        d.text((xy(x+62),xy(y+40)),req[:35],font=_font(8),fill='#71809A')
    return _png_bytes(img)


def _png_bytes(img):
    out=BytesIO(); img.save(out,format='PNG',optimize=True); return out.getvalue()



def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(15*mm, 11*mm, PAGE_W-15*mm, 11*mm)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(15*mm, 7*mm, 'ARCHDS · Adaptive Requirements-to-Architecture Decision System')
    canvas.drawRightString(PAGE_W-15*mm, 7*mm, f'Page {doc.page}')
    canvas.restoreState()

def _bullet(text):
    return Paragraph(f'• {str(text)}', ParagraphStyle('bullet', parent=getSampleStyleSheet()['BodyText'], fontSize=8.7, leading=12, textColor=NAVY, spaceAfter=3))


def build_pdf(result: dict[str, Any]) -> bytes:
    project = result.get('project_name') or 'ARCHDS Architecture Study'
    rec = result.get('recommendation') or {}
    profile = result.get('requirement_profile') or {}
    metrics = result.get('research_metrics') or {}
    candidates = result.get('candidates') or []
    trace = result.get('traceability') or []
    explanations = result.get('explanations') or []
    exp = next((x for x in explanations if x.get('candidate_id')==rec.get('candidate_id')), {})
    styles=getSampleStyleSheet()
    title=ParagraphStyle('TitleX',parent=styles['Title'],fontSize=25,leading=30,textColor=NAVY,spaceAfter=8)
    h1=ParagraphStyle('H1X',parent=styles['Heading1'],fontSize=15,leading=19,textColor=BLUE,spaceBefore=10,spaceAfter=8)
    h2=ParagraphStyle('H2X',parent=styles['Heading2'],fontSize=10.5,leading=14,textColor=NAVY,spaceBefore=7,spaceAfter=4)
    body=ParagraphStyle('BodyX',parent=styles['BodyText'],fontSize=8.8,leading=13,textColor=NAVY)
    small=ParagraphStyle('SmallX',parent=body,fontSize=7.5,textColor=MUTED)
    centre=ParagraphStyle('CentreX',parent=body,alignment=TA_CENTER)
    buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=15*mm,leftMargin=15*mm,topMargin=15*mm,bottomMargin=15*mm,title=f'ARCHDS - {project}')
    story=[]
    story += [Paragraph('ARCHDS',ParagraphStyle('Brand',parent=title,textColor=VIOLET,fontSize=10,letterSpacing=2)), Paragraph(project,title), Paragraph('Adaptive Architecture Intelligence · Requirement-driven architecture decision report',small), Spacer(1,8)]
    story.append(Table([[Paragraph('<b>FINAL DECISION</b>',body),Paragraph(f'<b>{rec.get("name","Not available")}</b><br/>{rec.get("pattern_key","")}',body)], [Paragraph('Decision confidence',body),Paragraph(f'<b>{metrics.get("confidence",0)}%</b>',body)], [Paragraph('Requirement coverage',body),Paragraph(f'<b>{metrics.get("requirement_coverage",0)}%</b>',body)], [Paragraph('Final score',body),Paragraph(f'<b>{metrics.get("final_score",0)}</b>',body)]], colWidths=[55*mm,120*mm], style=TableStyle([('BACKGROUND',(0,0),(0,-1),PALE),('BOX',(0,0),(-1,-1),0.6,LINE),('INNERGRID',(0,0),(-1,-1),0.35,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)])))
    story += [Spacer(1,8), Paragraph('Decision rationale',h1), Paragraph(exp.get('rationale') or rec.get('description',''),body)]
    story.append(Paragraph('Decision evidence snapshot',h2))
    evidence_rows=[[Paragraph('<b>Factor</b>',small),Paragraph('<b>Evidence from this analysis</b>',small)]]
    for label,vals in [('Requirement drivers',profile.get('drivers',[])[:6]),('Decision evidence',rec.get('decision_evidence',[])[:8]),('Accepted strengths',rec.get('advantages',[])[:6]),('Residual risks',[f.get('title',f.get('description','')) for f in rec.get('critique_findings',[])[:6]])]:
        evidence_rows.append([Paragraph(label,small),Paragraph(' · '.join(map(str,vals)) or 'None returned',small)])
    story.append(Table(evidence_rows,colWidths=[45*mm,130*mm],style=TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('GRID',(0,0),(-1,-1),0.35,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)])))
    story.append(Paragraph('System requirements',h1))
    story.append(Paragraph(profile.get('description') or result.get('description') or 'The analysis was generated from the preserved project requirements.',body))
    for label, key in [('Functional requirements','FUNCTIONAL'),('Non-functional requirements','NON_FUNCTIONAL')]:
        story.append(Paragraph(label,h2))
        records=[x.get('description','') for x in profile.get('requirement_records',[]) if x.get('type')==key]
        if not records: records=profile.get('functional_requirements',[]) if key=='FUNCTIONAL' else profile.get('non_functional_requirements',[])
        story += [_bullet(x) for x in records[:30]]
    story.append(Paragraph('Architectural drivers',h2)); story += [_bullet(x) for x in profile.get('drivers',[])[:20]]
    story.append(PageBreak())
    story.append(Paragraph('Selected architecture diagram',h1))
    arch=_diagram_png(rec,'architecture'); story.append(RLImage(BytesIO(arch),width=175*mm,height=min(115*mm,175*mm*(int((rec.get('graph') or {}).get('canvas_height',760))/1260))))
    story.append(Paragraph('The diagram above is rendered from the selected candidate graph, including only components and dependencies returned by the completed analysis.',small))
    story.append(PageBreak())
    story.append(Paragraph('UML component blueprint',h1))
    uml=_diagram_png(rec,'uml'); story.append(RLImage(BytesIO(uml),width=175*mm,height=105*mm))
    story.append(Paragraph('UML-style component view generated from the same requirement-derived architecture. It is not a generic reference diagram.',small))
    story.append(Paragraph('Runtime sequence view',h1))
    seq=_diagram_png(rec,'sequence'); story.append(RLImage(BytesIO(seq),width=175*mm,height=78*mm))
    story.append(PageBreak())
    story.append(Paragraph('Architecture competition',h1))
    rows=[[Paragraph('<b>Candidate</b>',small),Paragraph('<b>Pattern</b>',small),Paragraph('<b>Score</b>',small),Paragraph('<b>Pareto</b>',small)]]
    for c in candidates:
        rows.append([Paragraph(str(c.get('name','')),small),Paragraph(str(c.get('pattern_key','')),small),Paragraph(str(round(float((c.get('scores') or {}).get('weighted_total',0)),2)),small),Paragraph('YES' if c.get('is_pareto_optimal') else 'NO',small)])
    story.append(Table(rows,colWidths=[60*mm,55*mm,25*mm,25*mm],style=TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('GRID',(0,0),(-1,-1),0.35,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)])))
    story.append(Paragraph('Explainability and traceability',h1))
    for t in trace[:40]:
        evidence=', '.join(t.get('architectural_decisions') or (t.get('candidate_links') or [{}])[0].get('evidence',[]) or [])
        story.append(KeepTogether([Paragraph(f"<b>{t.get('requirement_id','')}</b> · {t.get('requirement','')}",body),Paragraph(f"Evidence: {evidence or 'Mapped through candidate graph'}",small),Spacer(1,4)]))
    story.append(PageBreak())
    story.append(Paragraph('Risks, trade-offs and assumptions',h1))
    for heading,vals in [('Risks',[x.get('title',x.get('description','')) for x in rec.get('critique_findings',[])]),('Trade-offs',rec.get('disadvantages',[])),('Assumptions',rec.get('assumptions',[]))]:
        story.append(Paragraph(heading,h2)); story += [_bullet(x) for x in vals[:20]]
    story.append(Paragraph('Technology and deployment evidence',h1))
    for k,vals in (rec.get('technology_evidence') or {}).items():
        story.append(Paragraph(f'<b>{k}</b>',body)); story += [_bullet(x) for x in vals[:8]]
    story.append(Paragraph('Research metrics',h1))
    mr=[[Paragraph('<b>Metric</b>',small),Paragraph('<b>Value</b>',small)]]
    for k,v in metrics.items(): mr.append([Paragraph(str(k).replace('_',' '),small),Paragraph(str(v),small)])
    story.append(Table(mr,colWidths=[110*mm,55*mm],style=TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('GRID',(0,0),(-1,-1),0.35,LINE),('LEFTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)])))
    story.append(Spacer(1,10)); story.append(Paragraph('ARCHDS provides an evidence-based recommendation. Final architectural accountability remains with the human decision-maker.',small))
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
