import re

NODE_WIDTH = 220
NODE_HEIGHT = 78
LANE_TOPS = {"experience":60, "edge":205, "domain":350, "data":495}
LAYER_TITLES = {"experience":"Experience", "edge":"Edge, Identity & Integration", "domain":"Business Capabilities", "data":"Data & Platform"}

def _layer(name):
    n=name.lower()
    if any(x in n for x in ("client","mobile","web","portal","app","ui")): return "experience"
    if any(x in n for x in ("gateway","identity","provider","edge","auth","security","load balanc","realtime")): return "edge"
    if any(x in n for x in ("postgres","mysql","mariadb","oracle","sql server","sql relational","mongodb","mongo","dynamodb","cassandra","couchbase","firestore","database","store","storage","blob","object storage","cache","replica","warehouse","index","broker","event log","queue","kafka","rabbit","pulsar","nats","search","telemetry","time-series")): return "data"
    return "domain"

def _relations(c):
    known=set(c.get("components",[])); out=[]
    for rel in c.get("relations",[]):
        if "->" not in rel: continue
        a,b=[x.strip() for x in rel.split("->",1)]
        if a in known and b in known and a!=b: out.append((a,b))
    return list(dict.fromkeys(out))

def graph_for(c):
    """Create a requirement-derived, non-overlapping layered graph.

    The previous implementation used fixed Y positions for every lane. When a
    requirement produced multiple rows in a lane, the next lane could start
    before the previous lane had finished. This version sizes every lane from
    the actual number of nodes and then stacks lanes with a generous gutter.
    """
    components=list(dict.fromkeys(c.get("components",[])))
    layers={k:[] for k in LANE_TOPS}
    for name in components:
        layers[_layer(name)].append(name)

    width_total=1260
    left=42
    lane_width=1176
    node_w=250
    node_h=96
    gap_x=24
    gap_y=24
    lane_pad_top=54
    lane_pad_bottom=28
    lane_gap=34

    nodes=[]
    lookup={}
    groups=[]
    current_y=28

    for layer in ("experience","edge","domain","data"):
        members=layers[layer]
        if not members:
            continue
        cols=min(4,max(1,len(members)))
        rows=(len(members)+cols-1)//cols
        actual_cols=min(cols,len(members))
        inner_width=lane_width-40
        cell_w=(inner_width-gap_x*(actual_cols-1))/actual_cols
        node_width=min(node_w,cell_w)
        lane_height=lane_pad_top + rows*node_h + max(0,rows-1)*gap_y + lane_pad_bottom
        group_y=current_y

        for i,name in enumerate(members):
            col=i%actual_cols
            row=i//actual_cols
            x=left+20+col*(node_width+gap_x)
            y=group_y+lane_pad_top+row*(node_h+gap_y)
            node={
                "id":f"n{len(nodes)}",
                "label":name,
                "type":"component",
                "layer":layer,
                "x":round(x,1),
                "y":round(y,1),
                "width":round(node_width,1),
                "height":node_h,
                "requirements":c.get("component_requirements",{}).get(name,[]),
            }
            nodes.append(node)
            lookup[name]=node["id"]

        groups.append({
            "id":layer,
            "title":LAYER_TITLES[layer],
            "x":left,
            "y":group_y,
            "width":lane_width,
            "height":lane_height,
        })
        current_y += lane_height + lane_gap

    by_name={n["label"]:n for n in nodes}
    edges=[]
    for i,(a,b) in enumerate(_relations(c)):
        if a not in by_name or b not in by_name:
            continue
        edges.append({
            "id":f"e{i}",
            "source":by_name[a]["id"],
            "target":by_name[b]["id"],
            "label":"",
            "kind":"dependency",
        })

    return {
        "nodes":nodes,
        "edges":edges,
        "groups":groups,
        "legend":LAYER_TITLES,
        "canvas_width":width_total,
        "canvas_height":max(650,current_y+18),
    }

def plantuml_for(c):
    components=list(dict.fromkeys(c.get("components",[]))); aliases={name:f"C{i}" for i,name in enumerate(components)}
    lines=["@startuml","title ARCHDS — Requirement-Derived UML Component Architecture","left to right direction","skinparam componentStyle rectangle","skinparam linetype ortho","skinparam shadowing false","skinparam packageStyle rectangle","skinparam defaultTextAlignment center"]
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

def svg_for(c):
    g=graph_for(c); width=1260; height=g.get("canvas_height",650)
    esc=lambda x: str(x).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    out.append('<defs><marker id="archds-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#64748b"/></marker></defs>')
    for group in g["groups"]:
        out.append(f'<rect x="{group["x"]}" y="{group["y"]}" width="{group["width"]}" height="{group["height"]}" rx="16" fill="none" stroke="#334155"/>')
        out.append(f'<text x="{group["x"]+16}" y="{group["y"]+22}" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="13" fill="#94a3b8">{esc(group["title"])}</text>')
    byid={n["id"]:n for n in g["nodes"]}
    for e in g["edges"]:
        a,b=byid[e["source"]],byid[e["target"]]
        aw=a.get("width",NODE_WIDTH); bw=b.get("width",NODE_WIDTH)
        ax=a["x"]+aw; ay=a["y"]+a.get("height",NODE_HEIGHT)/2; bx=b["x"]; by=b["y"]+b.get("height",NODE_HEIGHT)/2
        out.append(f'<path d="M {ax} {ay} C {(ax+bx)/2} {ay}, {(ax+bx)/2} {by}, {bx} {by}" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#archds-arrow)"/>')
    for n in g["nodes"]:
        reqs=n.get("requirements",[])
        nw=n.get("width",NODE_WIDTH); nh=n.get("height",NODE_HEIGHT)
        out.append(f'<rect x="{n["x"]}" y="{n["y"]}" width="{nw}" height="{nh}" rx="12" fill="#111827" stroke="#475569"/>')
        out.append(f'<text x="{n["x"]+12}" y="{n["y"]+30}" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="13" font-weight="600" fill="#f8fafc">{esc(n["label"][:28])}</text>')
        out.append(f'<text x="{n["x"]+12}" y="{n["y"]+52}" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="11" fill="#94a3b8">{esc(", ".join(reqs[:4]) if reqs else n["layer"])}</text>')
    out.append('</svg>')
    return "".join(out)

def add_diagrams(candidates):
    for c in candidates:
        c["graph"]=graph_for(c); c["plantuml_source"]=plantuml_for(c); c["diagram_svg"]=svg_for(c)
    return candidates
