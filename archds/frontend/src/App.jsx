import React, { Component, useEffect, useMemo, useRef, useState } from 'react';
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { auth, projects, jobs, reports, audit, errorMessage } from './services/api';

const AGENTS = [
  ['REQ','Requirement Analyst'],['CLAR','Requirement Clarifier'],['DRV','Architectural Driver Analyst'],['RAG','Architecture Knowledge Agent'],
  ['GEN','Architecture Generator'],['SEC','Security Reviewer'],['SCL','Scalability Reviewer'],['PERF','Performance Reviewer'],
  ['REL','Reliability Reviewer'],['COST','Cost Reviewer'],['MAINT','Maintainability Reviewer'],['VERIFY','Consistency Verifier'],
  ['EVAL','Multi-Objective Evaluator'],['PARETO','Pareto Optimizer'],['REF','Refinement Agent'],['JUDGE','Architecture Judge'],
  ['WHY','Explainability Agent'],['DIAG','Diagram Agent'],['TRACE','Traceability Agent'],['CONF','Research Metrics Agent']
];
function confidencePct(value){const raw=String(value??0).replace('%','').trim();const n=Number(raw);if(!Number.isFinite(n))return '0%';const pct=n<=1?n*100:n;return `${Math.round(Math.max(0,Math.min(100,pct)))}%`;}
function currentUser(){try{return JSON.parse(sessionStorage.getItem('archds_user')||'{}')}catch{return {}}}
function reportToast(message,type='info'){
  const existing=document.getElementById('archds-report-toast');
  if(existing) existing.remove();
  const el=document.createElement('div');
  el.id='archds-report-toast';
  el.className=`archds-toast show ${type}`;
  const title=type==='success'?'Report ready':type==='error'?'Report download failed':'Generating report';
  el.innerHTML=`<b>${title}</b><span></span>`;
  el.querySelector('span').textContent=message;
  document.body.appendChild(el);
  window.setTimeout(()=>{el.classList.remove('show');window.setTimeout(()=>el.remove(),240)},type==='info'?3500:5000);
}
function hasRole(...roles){const r=currentUser().role||'REVIEWER';return roles.includes(r)}
function Protected({children}){return sessionStorage.getItem('archds_token')?children:<Navigate to="/login" replace/>;}
function RoleGate({roles,children}){return hasRole(...roles)?children:<div className="access-denied section-card"><div className="access-icon">LOCK</div><span className="eyebrow">RBAC CONTROL</span><h2>Role-restricted workspace</h2><p>Your current role <b>{currentUser().role||'REVIEWER'}</b> does not have access to this area.</p><NavLink className="btn primary" to="/dashboard">Return to dashboard</NavLink></div>}
function Logo(){return <div className="brand"><div className="brand-mark"><span>A</span><i>D</i></div><div><b>ARCHDS</b><small>Adaptive Architecture Intelligence</small></div></div>}
function Shell({children}){const nav=useNavigate();const loc=useLocation();const user=currentUser();const logout=()=>{sessionStorage.clear();nav('/login')};const items=[['/dashboard','Overview','⌂'],['/projects','Projects','◫'],['/create-project','New analysis','＋'],['/history','Run history','◷'],['/reports','AI reports','▤'],['/audit','Decision audit','✓'],['/rbac','Access & roles','◇']];return <div className="app-shell"><aside className="sidebar"><Logo/><div className="nav-label">WORKSPACE</div><nav>{items.map(([to,label,icon])=><NavLink key={to} to={to} className={({isActive})=>`nav-item ${isActive?'active':''}`}><span>{icon}</span>{label}{label==='AI reports'&&<em className="nav-badge">NEW</em>}</NavLink>)}</nav><div className="side-research"><div className="pulse"><i/> Research engine</div><p>20 specialist agents<br/>Requirement-derived reasoning</p><div className="role-chip">{user.role||'REVIEWER'} · RBAC</div></div><div className="side-user"><div className="avatar">{(user.name||user.email||'R').slice(0,1).toUpperCase()}</div><div><b>{user.name||'Researcher'}</b><small>{user.role||'REVIEWER'} · {user.email||'Local workspace'}</small></div><button onClick={logout} title="Sign out">↪</button></div></aside><main className="main"><header className="topbar"><div><span className="crumb">ARCHDS / {loc.pathname.startsWith('/project')?'ARCHITECTURE REVIEW':'RESEARCH WORKSPACE'}</span><h1>{loc.pathname.startsWith('/project')?'Decision intelligence board':'Adaptive architecture workspace'}</h1></div><div className="top-status"><span className="live-dot"/> Engine ready <span className="top-divider"/> <b>{user.role||'REVIEWER'}</b> · Java 21 · Python · React</div></header><div className="content">{children}</div></main></div>}
function Auth({register=false}){const nav=useNavigate();const [f,setF]=useState(register?{name:'',email:'',password:''}:{email:'',password:''});const [err,setErr]=useState('');const [busy,setBusy]=useState(false);async function submit(e){e.preventDefault();setBusy(true);setErr('');try{const r=register?await auth.register(f):await auth.login(f);sessionStorage.setItem('archds_token',r.data.token);sessionStorage.setItem('archds_user',JSON.stringify(r.data));nav('/dashboard')}catch(e){setErr(errorMessage(e))}finally{setBusy(false)}}return <div className="auth-page"><div className="auth-visual"><Logo/><div className="auth-copy"><span className="eyebrow">REQUIREMENTS → ARCHITECTURE</span><h1>Design systems that <em>explain themselves.</em></h1><p>ARCHDS turns natural-language requirements into competing architecture blueprints, challenges them with specialist reviewers and exposes the evidence behind the final decision.</p><div className="mini-flow"><span>Requirements</span><b>→</b><span>Agents</span><b>→</b><span>Competition</span><b>→</b><span>Decision</span></div></div><div className="auth-orbit"><span>20 agents</span><span>Pareto</span><span>Traceable</span><span>Explainable</span></div></div><form className="auth-card" onSubmit={submit}><span className="eyebrow">{register?'CREATE RESEARCH SPACE':'WELCOME BACK'}</span><h2>{register?'Start building architecture intelligence':'Sign in to ARCHDS'}</h2><p className="muted">Your local workspace keeps analysis evidence and decisions together.</p>{register&&<label>Name<input required value={f.name} onChange={e=>setF({...f,name:e.target.value})}/></label>}<label>Email<input type="email" required value={f.email} onChange={e=>setF({...f,email:e.target.value})}/></label><label>Password<input type="password" required minLength="8" value={f.password} onChange={e=>setF({...f,password:e.target.value})}/></label>{err&&<div className="alert error">{err}</div>}<button className="btn primary wide" disabled={busy}>{busy?'Connecting…':register?'Create workspace':'Enter workspace'}</button><button type="button" className="text-btn" onClick={()=>nav(register?'/login':'/register')}>{register?'Already have an account? Sign in':'New here? Create an account'}</button>{!register&&<div className="demo-credentials"><b>Local demo roles</b><span>ADMIN · admin@archds.local · Admin@12345</span><span>ARCHITECT · architect@archds.local · Architect@12345</span><span>REVIEWER · reviewer@archds.local · Reviewer@12345</span></div>}</form></div>}
function Dashboard(){const [ps,setPs]=useState([]);useEffect(()=>{projects.list().then(r=>setPs(r.data)).catch(()=>{})},[]);return <div className="stack"><section className="dashboard-hero"><div className="hero-copy"><span className="eyebrow">ADAPTIVE ARCHITECTURE INTELLIGENCE</span><h2>From requirements to a <span>defensible architecture.</span></h2><p>Generate multiple requirement-specific architectures, let specialist agents challenge every trade-off, optimize the Pareto frontier and preserve the evidence chain.</p><NavLink className="btn primary" to="/create-project">Start an analysis <b>↗</b></NavLink></div><div className="hero-visual"><div className="halo"/><div className="hero-core"><b>20</b><small>AGENTS</small></div><div className="orbit o1">REQ</div><div className="orbit o2">REVIEW</div><div className="orbit o3">PARETO</div><div className="orbit o4">DECISION</div></div></section><div className="metric-grid"><Metric value={ps.length} label="Active projects" accent="violet"/><Metric value="5–8" label="Competing candidates" accent="cyan"/><Metric value="20" label="Research agents" accent="amber"/><Metric value="Discrete Pareto" label="Optimization model" accent="green"/></div><section className="section-card"><SectionHead eyebrow="RECENT ANALYSES" title="Your architecture work" action={<NavLink to="/projects">View all →</NavLink>}/>{ps.length?ps.slice(0,5).map((p,i)=><NavLink className="project-list-row" to={`/project/${p.id}`} key={p.id}><div className={`project-icon p${i%4}`}>{p.name.slice(0,1).toUpperCase()}</div><div className="row-main"><b>{p.name}</b><span>{p.description||'Requirement-driven architecture study'}</span></div><div className="row-meta"><small>ARCHITECTURE STUDY</small><strong>Open →</strong></div></NavLink>):<EmptyState/>}</section><section className="section-card"><SectionHead eyebrow="RESEARCH LOOP" title="How ARCHDS reasons"/><div className="research-loop">{['Requirements','Drivers','Candidate competition','Multi-agent debate','Pareto frontier','Digital Twin','Explainability','Human decision'].map((x,i)=><div className="loop-step" key={x}><span>{String(i+1).padStart(2,'0')}</span><b>{x}</b>{i<7&&<i>→</i>}</div>)}</div></section></div>}
function Metric({value,label,accent='violet'}){return <div className={`metric-card ${accent}`}><div className="metric-icon">✦</div><div><strong>{value}</strong><span>{label}</span></div></div>}
function SectionHead({eyebrow,title,action}){return <div className="section-head"><div><span className="eyebrow">{eyebrow}</span><h3>{title}</h3></div>{action}</div>}
function EmptyState(){return <div className="empty-state"><div>＋</div><b>No architecture studies yet</b><span>Create a project and describe the system you want ARCHDS to reason about.</span><NavLink className="btn secondary" to="/create-project">Create first analysis</NavLink></div>}
function Create(){
  const nav=useNavigate();
  const [busy,setBusy]=useState(false);
  const [err,setErr]=useState('');
  const [advanced,setAdvanced]=useState(false);
  const [form,setForm]=useState({name:'',description:'',functional:'',nonfunctional:'',constraints:'',tech:'',users:'',budget:''});
  const update=(k,v)=>{setErr('');setForm(x=>({...x,[k]:v}))};
  async function submit(){
    setBusy(true);setErr('');
    try{
      const p=(await projects.create({name:form.name.trim(),description:form.description.trim()})).data;
      await projects.saveRequirements(p.id,{
        functionalRequirements:form.functional,
        nonFunctionalRequirements:form.nonfunctional,
        constraints:form.constraints,
        technologyPreferences:form.tech,
        expectedUsers:form.users,
        budget:form.budget,
        alternatives:3,
        maxIterations:2
      });
      nav(`/project/${p.id}?run=1`);
    }catch(e){setErr(errorMessage(e));setBusy(false)}
  }
  return <div className="stack narrow">
    <div className="page-title"><div><span className="eyebrow">NEW ARCHITECTURE STUDY</span><h2>Describe the system. ARCHDS does the reasoning.</h2></div><NavLink to="/dashboard" className="text-btn">Cancel</NavLink></div>
    <section className="form-card">
      <SectionHead eyebrow="AUTOMATED ARCHITECTURE DISCOVERY" title="What are you designing?"/>
      <div className="input-guidance"><b>Two required inputs. The agents handle the rest.</b><span>ARCHDS infers functional requirements, quality attributes, architectural drivers, technology choices, and evaluation priorities. You do not need to write NFRs or provide scores.</span></div>
      <label>Project title<input value={form.name} onChange={e=>update('name',e.target.value)} placeholder="e.g. Smart Online Appointment Platform" maxLength={160}/></label>
      <label>Short system description<textarea rows="5" value={form.description} onChange={e=>update('description',e.target.value)} placeholder="Explain who uses the system and what it does. Mention any important risks or constraints if known; ARCHDS can infer reasonable defaults for the rest." maxLength={4000}/></label>
      <details className="advanced-inputs" open={advanced} onToggle={e=>setAdvanced(e.currentTarget.open)}>
        <summary>Optional advanced inputs <span>Only if you already know them</span></summary>
        <p className="muted">Leave these empty to let the agents infer them. These fields refine the analysis; they are not required.</p>
        <div className="form-grid">
          <label>Known functional requirements<textarea rows="4" value={form.functional} onChange={e=>update('functional',e.target.value)} placeholder="Optional — one per line"/></label>
          <label>Known quality requirements<textarea rows="4" value={form.nonfunctional} onChange={e=>update('nonfunctional',e.target.value)} placeholder="Optional — security, latency, availability…"/></label>
          <label>Known constraints<textarea rows="3" value={form.constraints} onChange={e=>update('constraints',e.target.value)} placeholder="Optional constraints"/></label>
          <label>Technology preferences<textarea rows="3" value={form.tech} onChange={e=>update('tech',e.target.value)} placeholder="Optional — existing stack or mandated technology"/></label>
        </div>
        <div className="mini-fields"><label>Expected users / workload<input value={form.users} onChange={e=>update('users',e.target.value)} placeholder="Optional"/></label><label>Budget or cost constraint<input value={form.budget} onChange={e=>update('budget',e.target.value)} placeholder="Optional"/></label></div>
      </details>
      {err&&<div className="alert error">{err}</div>}
      <div className="launch-summary"><Metric value="3" label="Architecture candidates"/><Metric value="2" label="Refinement passes"/><Metric value="20" label="Specialist roles"/><Metric value="Auto" label="Objective weights"/></div>
      <div className="form-actions"><button className="btn primary" disabled={busy||!form.name.trim()||!form.description.trim()} onClick={submit}>{busy?'Starting analysis…':'Generate architecture ↗'}</button></div>
    </section>
  </div>
}
function candidateKey(c){return c?.candidate_id??c?.candidateKey??c?.candidate_key??c?.candidateId??c?.id??'';}
function normalizedCandidate(c){if(!c)return c; const k=candidateKey(c); return k?{...c,candidate_id:String(k)}:c;}
function Project(){
  const {id}=useParams();
  const [searchParams,setSearchParams]=useSearchParams();
  const runStartedRef=useRef(false);
  const [project,setProject]=useState(null); const [result,setResult]=useState(null); const [job,setJob]=useState(null);
  const [err,setErr]=useState(''); const [tab,setTab]=useState('blueprint'); const [candidateId,setCandidateId]=useState(null);
  const [twin,setTwin]=useState(null); const [twinScenarios,setTwinScenarios]=useState([]); const [decision,setDecision]=useState('');
  const loadResult=async()=>{try{const r=await projects.result(id);if(r.data){const normalized={...r.data,candidates:(r.data.candidates||[]).map(normalizedCandidate),recommendation:normalizedCandidate(r.data.recommendation)};setResult(normalized);setCandidateId(candidateKey(normalized.recommendation)||candidateKey(normalized.candidates?.[0]));return true}}catch(e){}return false};
  const pollRun=async(jobId)=>{try{const r=await jobs.get(jobId);setJob(r.data);if(r.data.status==='FAILED'){setErr(r.data.errorMessage||'Analysis failed');return}if(r.data.status==='COMPLETED'){await loadResult();return}setTimeout(()=>pollRun(jobId),1200)}catch(e){setErr(errorMessage(e))}};
  const runAnalysis=async()=>{try{setErr('');const r=await projects.run(id);setJob(r.data);if(!r.data?.jobId)throw new Error('The backend accepted the analysis request but did not return a job ID.');pollRun(r.data.jobId)}catch(e){setErr(errorMessage(e))}};
  useEffect(()=>{
    let cancelled=false;
    (async()=>{
      try{
        const r=await projects.get(id);
        if(cancelled)return;
        setProject(r.data);
        const hasResult=await loadResult();
        if(!cancelled && searchParams.get('run')==='1' && !runStartedRef.current){
          runStartedRef.current=true;
          setSearchParams({}, {replace:true});
          if(!hasResult) await runAnalysis();
        }
      }catch(e){if(!cancelled)setErr(errorMessage(e))}
    })();
    return()=>{cancelled=true};
  },[id]);
  const selected=useMemo(()=>result?.candidates?.find(c=>String(candidateKey(c))===String(candidateId))||result?.recommendation||result?.candidates?.[0],[result,candidateId]);
  async function loadTwinScenarios(){try{const r=await projects.digitalTwinScenarios(id);setTwinScenarios(r.data?.scenarios||[])}catch(e){setErr(errorMessage(e))}}
  async function runTwinScenario(scenarioId,intensity=1){try{setErr('');const r=await projects.digitalTwinSimulate(id,{scenarioId,intensity});setTwin(r.data)}catch(e){setErr(errorMessage(e))}}
  if(!project && err)return <div className="loading-page"><div className="section-card" style={{maxWidth:760}}><span className="eyebrow">PROJECT LOAD ERROR</span><h2>ARCHDS could not open this study</h2><p>{err}</p><div className="form-actions"><NavLink className="btn secondary" to="/projects">Back to projects</NavLink><button className="btn primary" onClick={()=>{setErr('');window.location.reload()}}>Retry</button></div></div></div>;
  if(!project)return <div className="loading-page"><div className="spinner"/><b>Loading architecture study…</b><span>Retrieving requirements and previous analysis evidence.</span></div>;
  return <div className="stack">
    <div className="project-banner"><div><span className="eyebrow">{project.name}</span><h2>Architecture decision board</h2><p>{project.description}</p></div><div className="project-actions"><button className="btn secondary" onClick={()=>setTab('agents')}>View agent board</button><button className="btn primary" onClick={runAnalysis}>Run again ↻</button></div></div>
    {job&&<JobBanner job={job}/>} {err&&<div className="alert error"><b>Run diagnostics</b><span>{err}</span><button onClick={()=>{setErr('');loadResult()}}>Retry</button></div>}
    {result&&<><div className="decision-strip"><div><span className="eyebrow">RECOMMENDED ARCHITECTURE</span><h3>{result.recommendation?.name}</h3><p>{result.recommendation?.description}</p></div><div className="confidence"><strong>{confidencePct(result.research_metrics?.confidence??0)}</strong><span>decision confidence</span></div><div className="decision-actions"><span className="pareto-pill">◆ Pareto-aware</span><button className="btn secondary small" onClick={()=>downloadReport(project)}>Report ↓</button><button className="btn primary" onClick={()=>setTab('decision')}>Review decision →</button></div></div><div className="candidate-ribbon">{(result.candidates||[]).map(c=><button className={c.candidate_id===selected?.candidate_id?'candidate active':'candidate'} onClick={()=>{setCandidateId(c.candidate_id);setTab('blueprint')}} key={c.candidate_id}><span>{c.is_pareto_optimal?'◆':'○'}</span><div><b>{c.name}</b><small>{c.pattern_key}</small></div><strong>{Number(c.scores?.weighted_total||0).toFixed(1)}</strong></button>)}</div><div className="analysis-tabs" onMouseEnter={()=>{if(!twinScenarios.length)loadTwinScenarios()}}>{[['blueprint','Overview'],['requirements','Requirements'],['competition','Competition'],['framework','Architecture'],['uml','UML'],['explainability','Explainability'],['advisor','Ask ARCHDS'],['twin','Digital Twin'],['delivery','Delivery'],['decision','Decision']].map(([k,l])=><button className={tab===k?'active':''} onClick={()=>setTab(k)} key={k}>{l}</button>)}</div>{tab==='blueprint'&&<Blueprint candidate={selected} result={result}/>} {tab==='requirements'&&<Requirements result={result}/>} {tab==='framework'&&<Framework candidate={selected} result={result}/>} {tab==='competition'&&<Competition candidates={result.candidates||[]} selected={selected} setSelected={setCandidateId} debate={result.debate||[]}/>} {tab==='uml'&&<UML candidate={selected} result={result}/>} {tab==='explainability'&&<Explainability candidate={selected} result={result}/>} {tab==='advisor'&&<ArchitectureAdvisor projectId={id} result={result}/>} {tab==='twin'&&<DigitalTwin projectId={id} result={result} scenarios={twinScenarios} twin={twin} loadScenarios={loadTwinScenarios} runScenario={runTwinScenario}/>} {tab==='delivery'&&<DeliveryLab projectId={id} result={result}/>} {tab==='decision'&&<Decision result={result} projectId={id} decision={decision} setDecision={setDecision}/>}</>}</div>}

function Decision({result,projectId,decision,setDecision}){
  const candidate=result?.candidates?.find(c=>String(candidateKey(c))===String(decision))||result?.recommendation||result?.candidates?.[0];
  const [rationale,setRationale]=useState('');
  const [busy,setBusy]=useState(false);
  useEffect(()=>{if(!decision){const id=candidateKey(result?.recommendation)||candidateKey(result?.candidates?.[0]);if(id)setDecision(String(id))}},[decision,result,setDecision]);
  const [saved,setSaved]=useState(false);
  const [error,setError]=useState('');
  const choose=String(decision || candidateKey(candidate) || '');
  const validCandidateIds=new Set((result?.candidates||[]).map(candidateKey).map(String).filter(Boolean));
  const submit=async()=>{
    if(!choose)return;
    setBusy(true); setError(''); setSaved(false);
    try{
      if(!validCandidateIds.has(String(choose))) throw new Error('Please select a valid architecture candidate before recording the decision.');
      await projects.decision(projectId,{candidate_id:String(choose),rationale:rationale.trim()});
      setSaved(true);
    }catch(e){setError(errorMessage(e));}
    finally{setBusy(false);}
  };
  return <div className="stack decision-page">
    <section className="section-card decision-hero">
      <div><span className="eyebrow">HUMAN ARCHITECT DECISION GATE</span><h2>Review and record the final architecture decision</h2><p>ARCHDS provides the evidence; the architect records the final choice and rationale. Nothing is auto-approved.</p></div>
      <div className="framework-badge"><b>{result?.candidates?.length||0}</b><span>candidates reviewed</span></div>
    </section>
    <section className="section-card">
      <SectionHead eyebrow="CANDIDATE SELECTION" title="Choose the architecture to approve"/>
      <div className="decision-candidates">{(result?.candidates||[]).map(c=><button type="button" key={candidateKey(c)} className={`decision-candidate ${choose===String(candidateKey(c))?'selected':''}`} onClick={()=>{setDecision(String(candidateKey(c)));setSaved(false);}}>
        <div><b>{c.name}</b><small>{c.pattern_key||'Requirement-derived candidate'}</small></div><strong>{Number(c.scores?.weighted_total||0).toFixed(1)}</strong><span>{c.is_pareto_optimal?'◆ Pareto':'○ Candidate'}</span>
      </button>)}</div>
    </section>
    {candidate&&<section className="section-card decision-review">
      <div className="decision-review-head"><div><span className="eyebrow">SELECTED ARCHITECTURE</span><h3>{candidate.name}</h3><p>{candidate.description}</p></div><div className="score-badge"><b>{Number(candidate.scores?.weighted_total||0).toFixed(1)}</b><span>weighted score</span></div></div>
      <div className="metric-grid"><Metric value={`${Object.values(candidate.requirement_coverage||{}).filter(Boolean).length}/${Object.keys(candidate.requirement_coverage||{}).length}`} label="Requirements covered"/><Metric value={candidate.is_pareto_optimal?'Yes':'No'} label="Pareto efficient" accent="green"/><Metric value={(candidate.critique_findings||[]).length} label="Review findings" accent="amber"/></div>
      <label className="field-label">Architect rationale <span>optional</span></label>
      <textarea className="decision-rationale" value={rationale} onChange={e=>{setRationale(e.target.value);setSaved(false)}} maxLength={4000} placeholder="Record why this candidate is being selected, including any accepted trade-offs or human judgement…"/>
      <div className="form-actions"><span className="muted">This decision is recorded against the selected project and candidate.</span><button className="btn primary" disabled={busy||!validCandidateIds.has(String(choose))} onClick={submit}>{busy?'Recording decision…':'Record final decision ↗'}</button></div>
      {saved&&<div className="success">✓ Final architecture decision recorded successfully.</div>}
      {error&&<div className="alert error"><b>Decision could not be recorded:</b> {error}</div>}
    </section>}
  </div>
}
function JobBanner({job}){const done=job.status==='COMPLETED',failed=job.status==='FAILED';return <div className={`job-banner ${failed?'failed':done?'done':''}`}><div className="job-top"><div><span className="eyebrow">ANALYSIS EXECUTION</span><b>{failed?'Analysis stopped':done?'Analysis complete':'Agents are reasoning…'}</b></div><strong>{job.progress}%</strong></div><div className="progress"><i style={{width:`${job.progress}%`}}/></div><div className="job-bottom"><span>{job.currentStage||'INITIALIZING'}</span><span>{job.message}</span></div></div>}
function Blueprint({candidate,result}){
  if(!candidate)return <EmptyState/>;
  const exp=result.explanations?.find(x=>x.candidate_id===candidate.candidate_id)||{};
  const reqs=result.requirement_profile?.requirement_records||[];
  const coverage=Object.values(candidate.requirement_coverage||{}).filter(Boolean).length;
  return <div className="blueprint-layout"><section className="blueprint-card"><div className="blueprint-head"><div><span className="eyebrow">REQUIREMENT-DERIVED SYSTEM BLUEPRINT</span><h3>{candidate.name}</h3><p>{candidate.description}</p></div><div className="score-badge"><b>{Number(candidate.scores?.weighted_total||0).toFixed(1)}</b><span>weighted score</span></div></div><ArchitectureCanvas candidate={candidate} result={result}/><div className="legend-row"><span><i className="legend-dot violet"/>Experience</span><span><i className="legend-dot cyan"/>Edge & integration</span><span><i className="legend-dot amber"/>Business capabilities</span><span><i className="legend-dot green"/>Data & platform</span><small>{coverage}/{reqs.length||Object.keys(candidate.requirement_coverage||{}).length} supplied requirements covered</small></div></section><aside className="blueprint-side"><EvidenceCard title="Why this architecture" kicker="EVIDENCE" items={(exp.evidence||[]).slice(0,4)} empty="No requirement-specific evidence was returned."/><EvidenceCard title="Trade-offs" kicker="ACCEPTED COST" items={(exp.tradeoffs||candidate.disadvantages||[]).slice(0,4)} tone="amber" empty="No material trade-off was recorded."/><EvidenceCard title="Risks & uncertainty" kicker="REVIEW FINDINGS" items={(exp.risks||candidate.critique_findings?.map(x=>x.description||x.title)||[]).slice(0,4)} tone="rose" empty="No unresolved risk finding was returned."/></aside></div>
}
function EvidenceCard({title,kicker,items,tone='',empty}){const label=tone==='amber'?'Optimization trade-off':tone==='rose'?'Open review finding':'Requirement evidence';return <section className={`info-card ${tone}`}><span className="eyebrow">{kicker}</span><h4>{title}</h4>{items?.length?items.map((x,i)=><div className="evidence-item" key={i}><div className="evidence-item-head"><i>{tone==='rose'?'!':tone==='amber'?'↳':'✓'}</i><span>{label} {i+1}</span></div><p>{typeof x==='string'?x:(x?.description||x?.title||JSON.stringify(x))}</p></div>):<p className="muted">{empty}</p>}</section>}

function ArchitectureCanvas({candidate,result}){
  const g=candidate?.graph;
  const [selected,setSelected]=useState(null);
  const [replay,setReplay]=useState(false);
  const [visible,setVisible]=useState(0);
  const [showAllEdges,setShowAllEdges]=useState(false);
  useEffect(()=>{
    if(!replay){setVisible(g?.nodes?.length||0);return;}
    setVisible(0);
    let i=0;
    const timer=setInterval(()=>{i+=1;setVisible(i);if(i>=(g?.nodes?.length||0))clearInterval(timer)},120);
    return()=>clearInterval(timer);
  },[replay,g]);
  if(!g) return <div className="empty-state">No structured graph was returned.</div>;
  const w=g.canvas_width||1260,h=g.canvas_height||760;
  const palette={experience:{stroke:'#7657e8',fill:'#f3efff',soft:'#e8e1ff',text:'#4c3aa5',icon:'UI'},edge:{stroke:'#2387c9',fill:'#edf7ff',soft:'#dcefff',text:'#17649a',icon:'API'},domain:{stroke:'#d98922',fill:'#fff7e9',soft:'#ffedcf',text:'#9a5a08',icon:'SVC'},data:{stroke:'#20a777',fill:'#edf9f4',soft:'#d9f3e8',text:'#0d7554',icon:'DB'}};
  const iconFor=(label,layer)=>{
    const x=String(label).toLowerCase();
    if(x.includes('gateway')) return 'GW';
    if(x.includes('identity')||x.includes('security')||x.includes('auth')) return 'SEC';
    if(x.includes('database')||x.includes('postgres')) return 'DB';
    if(x.includes('cache')||x.includes('replica')) return 'CA';
    if(x.includes('queue')||x.includes('broker')||x.includes('event')) return 'MQ';
    if(x.includes('search')||x.includes('index')) return 'SR';
    if(x.includes('monitor')||x.includes('observ')) return 'OBS';
    if(x.includes('payment')||x.includes('transaction')) return 'PAY';
    if(x.includes('notification')||x.includes('alert')) return 'NTF';
    if(x.includes('telemetry')) return 'TEL';
    if(x.includes('tracking')) return 'GPS';
    if(x.includes('client')||x.includes('web')||x.includes('mobile')||x.includes('app')) return 'UI';
    return palette[layer]?.icon||'SYS';
  };
  const byId=Object.fromEntries((g.nodes||[]).map(n=>[n.id,n]));
  const nodeW=(n)=>n.width||250,nodeH=(n)=>n.height||96;
  const edgePath=(a,b,index=0)=>{
    const clean=pts=>pts.filter((p,i)=>i===0||p.x!==pts[i-1].x||p.y!==pts[i-1].y);
    // Prefer deterministic backend routing when available.
    const edgePoints=(g.edges||[]).find(e=>e.source===a.id&&e.target===b.id)?.points;
    if(Array.isArray(edgePoints)&&edgePoints.length>1) return clean(edgePoints).map((p,i)=>`${i?'L':'M'} ${p.x} ${p.y}`).join(' ');
    const aw=nodeW(a), ah=nodeH(a), bw=nodeW(b), bh=nodeH(b);
    const ca={x:a.x+aw/2,y:a.y+ah/2}, cb={x:b.x+bw/2,y:b.y+bh/2};
    const lane=(index%9-4)*12;
    if(a.layer!==b.layer){
      const downward=cb.y>=ca.y; const sy=downward?a.y+ah:a.y; const ty=downward?b.y:b.y+bh;
      const mid=(sy+ty)/2+lane;
      return clean([{x:ca.x,y:sy},{x:ca.x,y:mid},{x:cb.x,y:mid},{x:cb.x,y:ty}]).map((p,i)=>`${i?'L':'M'} ${p.x} ${p.y}`).join(' ');
    }
    const right=cb.x>=ca.x; const x1=right?a.x+aw:a.x; const x2=right?b.x:b.x+bw;
    if(Math.abs(ca.y-cb.y)<12) return `M ${x1} ${ca.y} L ${x2} ${cb.y}`;
    const channel=(right?Math.max(a.x+aw,b.x+bw):Math.min(a.x,b.x))+(right?34+Math.abs(lane):-(34+Math.abs(lane)));
    return clean([{x:x1,y:ca.y},{x:channel,y:ca.y},{x:channel,y:cb.y},{x:x2,y:cb.y}]).map((p,i)=>`${i?'L':'M'} ${p.x} ${p.y}`).join(' ');
  };
  const reqLabelMap=Object.fromEntries((result?.requirement_profile?.requirement_records||[]).map(r=>[r.id,r.description]));
  const humanReqs=(n)=>((n.requirements||[]).map(x=>reqLabelMap[x]||x).filter(Boolean));
  const wrapLabel=(text,max=27)=>{const words=String(text).split(/\s+/);const lines=[''];for(const word of words){const next=(lines[lines.length-1]+' '+word).trim();if(next.length>max&&lines[lines.length-1])lines.push(word);else lines[lines.length-1]=next;}return lines.slice(0,2)};
  const shortText=(text,max=30)=>{const value=String(text||'').replace(/\s+/g,' ').trim();return value.length>max?value.slice(0,max-1)+'…':value;};
  return <div className="arch-visual-shell">
    <div className="arch-toolbar">
      <div><span className="eyebrow">LIVE REQUIREMENT GRAPH</span><b>{g.nodes.length} components · {g.edges.length} dependencies</b></div>
      <div className="arch-toolbar-actions">
        <span className="arch-derived">● Derived from this candidate</span>
        <button className="mini-action" onClick={()=>setShowAllEdges(x=>!x)}>{showAllEdges?'Show key dependencies':'Show all dependencies'}</button>
        <button className="mini-action" onClick={()=>setReplay(x=>!x)}>{replay?'Stop replay':'▶ Replay architecture'}</button>
      </div>
    </div>
    <div className="architecture-canvas clean-canvas">
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Requirement-derived architecture diagram">
        <defs>
          <filter id="softShadow" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="5" stdDeviation="7" floodOpacity=".12"/></filter>
          <marker id="archArrowClean" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#71809a"/></marker>
          <linearGradient id="laneGlow" x1="0" x2="1"><stop offset="0" stopColor="#fff" stopOpacity=".95"/><stop offset="1" stopColor="#f7f9fd" stopOpacity=".65"/></linearGradient>
        </defs>
        <rect width={w} height={h} fill="#f8fafc"/>
        {g.groups.map(group=>{
          const p=palette[group.id]||palette.domain;
          return <g key={group.id}>
            <rect x={group.x} y={group.y} width={group.width} height={group.height} rx="22" fill="url(#laneGlow)" stroke={p.stroke} strokeOpacity=".38" strokeWidth="1.5"/>
            <rect x={group.x+16} y={group.y+12} width="260" height="31" rx="15.5" fill={p.soft}/>
            <circle cx={group.x+32} cy={group.y+27.5} r="5" fill={p.stroke}/>
            <text x={group.x+46} y={group.y+32} fill={p.text} fontSize="12" fontWeight="800" letterSpacing="1">{group.title.toUpperCase()}</text>
          </g>
        })}
        <g className="arch-edges">
          {(g.edges||[]).filter((e,ei)=>showAllEdges||ei<Math.min(18,g.edges.length)).map((e,ei)=>{const a=byId[e.source],b=byId[e.target];if(!a||!b)return null;return <path key={e.id} d={edgePath(a,b,ei)} fill="none" stroke="#7b8799" strokeWidth={showAllEdges?'1.15':'1.55'} strokeOpacity={showAllEdges?'.32':'.62'} markerEnd="url(#archArrowClean)"/>})}
        </g>
        {(g.nodes||[]).map((n,i)=>{
          const p=palette[n.layer]||palette.domain;
          const active=selected?.id===n.id;
          const shown=!replay||i<visible;
          const reqs=humanReqs(n);
          return <g key={n.id} className={`diagram-node-pro ${shown?'show':'hide'}`} onClick={()=>setSelected(n)} filter="url(#softShadow)">
            <rect x={n.x} y={n.y} width={nodeW(n)} height={nodeH(n)} rx="15" fill="#ffffff" stroke={active?p.stroke:'#d8e0ea'} strokeWidth={active?2.5:1.2}/>
            <rect x={n.x} y={n.y} width="6" height={nodeH(n)} rx="3" fill={p.stroke}/>
            <rect x={n.x+15} y={n.y+18} width="46" height="46" rx="12" fill={p.fill} stroke={p.soft}/>
            <text x={n.x+38} y={n.y+47} textAnchor="middle" fill={p.text} fontSize="10" fontWeight="900">{iconFor(n.label,n.layer)}</text>
            {wrapLabel(n.label).map((line,li)=><text key={li} x={n.x+76} y={n.y+30+li*14} fill="#17213a" fontSize="11.5" fontWeight="800">{line}</text>)}
            <text x={n.x+76} y={n.y+61} fill="#7a879b" fontSize="8.5">{reqs.length?shortText(reqs[0],30):'Requirement-derived service'}</text>
            <circle cx={n.x+nodeW(n)-17} cy={n.y+18} r="4.5" fill={p.stroke}/>
          </g>
        })}
      </svg>
    </div>
    <div className="arch-footer">
      <div className="arch-legend">{Object.entries(palette).map(([k,p])=><span key={k}><i style={{background:p.stroke}}/>{k==='domain'?'Business':k==='edge'?'Edge & identity':k==='data'?'Data & platform':'Experience'}</span>)}</div>
      <span className="arch-hint">Click a component to inspect its requirement links</span>
    </div>
    {selected&&<div className="component-inspector">
      <div className="inspector-icon">{iconFor(selected.label,selected.layer)}</div>
      <div className="inspector-main"><span className="eyebrow">SELECTED COMPONENT</span><h4>{selected.label}</h4><p>{(selected.requirements||[]).length?`Driven by ${humanReqs(selected).join(' · ')}.`:'Derived from the candidate architecture constraints.'}</p></div>
      <button className="mini-action" onClick={()=>setSelected(null)}>Close</button>
    </div>}
  </div>
}
function Requirements({result}){const r=result.requirement_profile||{};return <div className="grid-2"><section className="section-card"><SectionHead eyebrow="REQUIREMENT INTELLIGENCE" title="What the agents understood"/><div className="readiness"><div className="readiness-ring" style={{'--p':Number(r.architecture_readiness??0)}}><b>{r.architecture_readiness??0}</b><span>readiness</span></div><div><h3>Architectural drivers</h3><div className="tag-row big">{(r.drivers||[]).map(x=><span key={x}>{x}</span>)}</div><p className="muted">Completeness, specificity, consistency and ambiguity are assessed before candidate generation.</p></div></div>{[['Completeness',r.completeness],['Specificity',r.specificity],['Consistency',r.consistency],['Ambiguity control',100-(r.ambiguity||0)]].map(([l,v])=><div className="quality-row" key={l}><span>{l}</span><i><b style={{width:`${Math.max(0,Math.min(100,Number(v||0)))}%`}}/></i><strong>{Number(v||0)}%</strong></div>)}</section><section className="section-card"><SectionHead eyebrow="DECISION WEIGHTS" title="Optimization priorities"/>{Object.entries(r.priority_weights||{}).filter(([,v])=>Number(v)>0).map(([k,v])=><div className="quality-row" key={k}><span>{k.replaceAll('_',' ')}</span><i><b style={{width:`${Math.min(100,Number(v)*10)}%`}}/></i><strong>{v}</strong></div>)}<div className="clarify"><span>?</span><div><b>Clarification status</b><p>{r.clarification_questions?.length?`${r.clarification_questions.length} question(s) surfaced for human review.`:'No material clarification questions remain.'}</p></div></div></section></div>}
function Competition({candidates,selected,setSelected,debate=[]}){
  const [sort,setSort]=useState('score');
  const ordered=useMemo(()=>[...(candidates||[])].sort((a,b)=>{
    if(sort==='coverage')return Number(Object.values(b.requirement_coverage||{}).filter(Boolean).length)-Number(Object.values(a.requirement_coverage||{}).filter(Boolean).length);
    if(sort==='risk')return Number((a.critique_findings||[]).length)-Number((b.critique_findings||[]).length);
    if(sort==='pareto')return Number(b.is_pareto_optimal)-Number(a.is_pareto_optimal)||Number(b.scores?.weighted_total||0)-Number(a.scores?.weighted_total||0);
    return Number(b.scores?.weighted_total||0)-Number(a.scores?.weighted_total||0)
  }),[candidates,sort]);
  const max=Math.max(...ordered.map(c=>Number(c.scores?.weighted_total||0)),1);
  const dimensions=['performance','scalability','security','reliability','availability','maintainability','cost','complexity'];
  const bestDimension=c=>{const scores=c?.scores||{};return dimensions.map(k=>[k,Number(scores[k]??0)]).sort((a,b)=>b[1]-a[1])[0];};
  return <div className="competition-page stack">
    <section className="competition-hero section-card"><div><span className="eyebrow">ARCHITECTURE TOURNAMENT</span><h2>Competing candidates, visible trade-offs.</h2><p>Every candidate is generated from the supplied requirement profile, then compared using the same evidence, constraints and optimization objectives.</p></div><div className="competition-count"><strong>{ordered.length}</strong><span>candidates</span></div></section>
    <section className="section-card"><div className="competition-toolbar"><div><span className="eyebrow">HEAD-TO-HEAD COMPARISON</span><h3>Candidate matrix</h3></div><div className="sort-tabs">{[['score','Weighted score'],['coverage','Coverage'],['risk','Reviewer findings'],['pareto','Pareto first']].map(([k,l])=><button key={k} className={sort===k?'active':''} onClick={()=>setSort(k)}>{l}</button>)}</div></div>
      <div className="competition-grid">{ordered.map((c,i)=>{
        const coverage=Object.values(c.requirement_coverage||{}).filter(Boolean).length;const total=Object.keys(c.requirement_coverage||{}).length||1;const findings=(c.critique_findings||[]).length;const selectedNow=selected?.candidate_id===c.candidate_id;const top=bestDimension(c);
        const reason=(c.decision_evidence||c.advantages||[])[0]||`Strongest modeled dimension: ${top?.[0]||'overall fit'} (${top?.[1]?.toFixed?.(1)||'—'})`;
        const risk=(c.disadvantages||c.critique_findings||[])[0];
        return <button key={c.candidate_id} className={`competition-card ${selectedNow?'selected':''}`} onClick={()=>setSelected(c.candidate_id)}>
          <div className="competition-rank">{i+1}</div><div className="competition-main">
            <div className="competition-title"><div><b>{c.name}</b><small>{c.pattern_key||'Requirement-derived pattern'}</small></div><strong>{Number(c.scores?.weighted_total||0).toFixed(1)}</strong></div>
            <div className="score-bar"><i style={{width:`${Math.max(5,Math.min(100,(Number(c.scores?.weighted_total||0)/max)*100))}%`}}/></div>
            <div className="competition-stats"><span><b>{Math.round(coverage/total*100)}%</b> coverage</span><span><b>{c.is_pareto_optimal?'YES':'NO'}</b> Pareto</span><span><b>{findings}</b> findings</span></div>
            <div className="alternative-insight"><b>Why consider it:</b> {String(reason).slice(0,180)}</div>
            <div className="alternative-risk"><b>Trade-off:</b> {String(risk?.description||risk?.title||'Review the candidate evidence and requirement coverage before selecting it.').slice(0,150)}</div>
            <div className="tag-row">{(c.components||[]).slice(0,5).map(x=><span key={x}>{x}</span>)}</div>
          </div>
        </button>})}</div>{!ordered.length&&<EmptyState/>}</section>
    {debate.length>0&&<section className="section-card debate-panel"><SectionHead eyebrow="MULTI-AGENT DEBATE" title="The recommendation survives competing arguments"/><div className="debate-grid">{debate.map((d,i)=><article className="debate-card" key={i}><span className="debate-role">{d.role}</span><h4>{d.candidate}</h4><p>{d.position}</p>{(d.evidence||[]).slice(0,2).map((e,j)=><small key={j}>Evidence: {e}</small>)}</article>)}</div></section>}
  </div>
}
function Review({candidates}){const findings=candidates.flatMap(c=>(c.critique_findings||[]).map(f=>({...f,candidate:c.name})));return <div className="review-layout"><section className="section-card"><SectionHead eyebrow="ADVERSARIAL REVIEW" title="Specialists challenge the candidates"/>{findings.length?findings.map((f,i)=><div className={`finding-row ${String(f.severity).toLowerCase()}`} key={i}><span>{f.severity}</span><div><b>{f.title}</b><p>{f.description}</p><small>{f.candidate}</small></div></div>):<div className="success">✓ No reviewer findings returned.</div>}</section><aside className="section-card"><SectionHead eyebrow="REVIEW DIMENSIONS" title="Independent lenses"/>{['Security','Scalability','Performance','Reliability','Cost','Maintainability'].map((x,i)=><div className="review-lens" key={x}><span>{String(i+1).padStart(2,'0')}</span><div><b>{x}</b><small>Independent specialist review</small></div><i>✓</i></div>)}</aside></div>}
function Optimization({result}){const o=result.optimization||{};const c=result.candidates||[];return <div className="stack"><section className="section-card"><SectionHead eyebrow="PARETO ANALYSIS" title={o.algorithm||'Multi-objective optimization'}/><div className="pareto-board"><div className="axis-y">Performance</div><div className="scatter">{c.map((x,i)=>{const left=Math.min(92,8+(Number(x.scores?.cost||0)*.82));const bottom=Math.min(88,8+(Number(x.scores?.performance||0)*.78));return <button key={x.candidate_id} className={x.is_pareto_optimal?'scatter-dot frontier':'scatter-dot'} style={{left:`${left}%`,bottom:`${bottom}%`}} title={x.name} onClick={()=>{}}>{i+1}</button>})}<span className="axis-x">Cost efficiency →</span></div></div></section><div className="metric-grid"><Metric value={result.research_metrics?.initial_score??'—'} label="Initial score"/><Metric value={result.research_metrics?.final_score??'—'} label="Final score" accent="green"/><Metric value={`${result.research_metrics?.refinement_improvement_percent??0}%`} label="Iterative improvement" accent="cyan"/><Metric value={result.research_metrics?.architecture_diversity??0} label="Architecture diversity" accent="amber"/></div><div className="grid-2"><section className="section-card"><SectionHead eyebrow="TRADE-OFFS" title="What changed the frontier"/>{(o.tradeoffs||[]).map((x,i)=><div className="bullet" key={i}><i>↳</i><span>{x}</span></div>)}</section><section className="section-card"><SectionHead eyebrow="BASELINE" title="Single-pass vs iterative"/><div className="compare-cards"><Metric value={result.baseline?.score??'—'} label="Baseline"/><Metric value={result.baseline?.proposed?.score??'—'} label="Proposed" accent="green"/></div><div className="success">Improvement +{result.baseline?.proposed?.improvement_vs_initial??0}%</div></section></div></div>}
function Agents({result}){const events=result.agent_trace||[];return <div className="agents-layout"><section className="agent-board">{AGENTS.map(([code,name],i)=>{const ev=events.filter(e=>e.agent===name||String(e.agent).includes(name.split(' ')[0]));return <div className={`agent-card ${ev.length?'executed':''}`} key={code}><div className="agent-code">{code}</div><div><b>{name}</b><small>{ev.length?`${ev.length} evidence event${ev.length>1?'s':''}`:'Registered stage'}</small></div><span>{ev.length?'✓':'○'}</span></div>})}</section><aside className="section-card evidence-panel"><SectionHead eyebrow="EXECUTION EVIDENCE" title="Observed agent events"/>{events.map((e,i)=><div className="event-row" key={i}><span>{String(e.stage||'RUN').slice(0,8)}</span><div><b>{e.agent}</b><p>{e.message}</p><small>{e.duration_ms||0} ms · {e.status}</small></div></div>)}</aside></div>}
function Traceability({items}){return <section className="section-card table-card"><SectionHead eyebrow="REQUIREMENT TRACEABILITY" title="Every decision has an evidence path"/><div className="trace-grid"><div className="trace-head">ID</div><div className="trace-head">Requirement</div><div className="trace-head">Architectural evidence</div><div className="trace-head">Coverage</div>{items.map(x=><React.Fragment key={x.requirement_id}><div><b>{x.requirement_id}</b></div><div>{x.requirement}</div><div>{(x.architectural_decisions||x.candidate_links?.[0]?.evidence||[]).join(', ')||'Mapped through candidate graph'}</div><div>{x.candidate_links?.some(y=>y.satisfied)?<span className="good">✓ Covered</span>:<span className="bad">Gap</span>}</div></React.Fragment>)}</div></section>}
function Framework({candidate,result}){
  if(!candidate) return <EmptyState/>;
  const fw=candidate.system_design_framework||{};
  const agentFw=result?.research_framework||{};
  const nodes=fw.nodes||[]; const edges=fw.edges||[];
  const byId=Object.fromEntries(nodes.map(n=>[n.id,n]));
  const kindColor={actor:'#7657e8',routing:'#2387c9',edge:'#2387c9',gateway:'#2387c9',security:'#d35d79',business:'#d98922',messaging:'#8a63d8',data:'#20a777',control:'#5f7fa8',resilience:'#d08a2d'};
  const layers=['actor','routing','edge','gateway','security','business','messaging','data','control','resilience'];
  const groups=[]; let current=[]; nodes.forEach(n=>{ if(current.length && current[current.length-1].kind!==n.kind){} current.push(n); });
  const laneNodes=[]; const byKind={}; nodes.forEach(n=>(byKind[n.kind]??=[]).push(n));
  const kinds=Object.keys(byKind); const W=Math.max(1120,kinds.length*210); const H=Math.max(330,Math.ceil(nodes.length/4)*115+180);
  kinds.forEach((kind,ki)=>{ const arr=byKind[kind]; arr.forEach((n,i)=>laneNodes.push({...n,x:70+ki*205,y:92+i*112,w:170,h:72})); });
  const pos=Object.fromEntries(laneNodes.map(n=>[n.id,n]));
  const edgePath=(e,i)=>{const a=pos[e.from],b=pos[e.to];if(!a||!b)return '';const sx=a.x+a.w,sy=a.y+a.h/2,tx=b.x,ty=b.y+b.h/2;const gap=(tx-sx);if(gap>=24){const mid=sx+gap/2+(i%3-1)*8;return `M ${sx} ${sy} L ${mid} ${sy} L ${mid} ${ty} L ${tx} ${ty}`;}const channel=Math.max(a.x+a.w,b.x+b.w)+28+(i%5)*10;return `M ${sx} ${sy} L ${channel} ${sy} L ${channel} ${ty} L ${tx} ${ty}`;};
  return <div className="framework-page stack">
    <section className="section-card framework-hero"><div><span className="eyebrow">SYSTEM DESIGN FRAMEWORK · REQUIREMENT DERIVED</span><h2>{candidate.name}</h2><p>The framework view shows the selected runtime path and requirement-justified infrastructure. It is generated from the current candidate rather than a fixed template.</p></div><div className="framework-badge"><b>{nodes.length}</b><span>modeled elements</span></div></section>
    <section className="section-card framework-topology-card"><SectionHead eyebrow="RUNTIME TOPOLOGY" title="Clean component flow"/><div className="framework-canvas"><svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Requirement-derived system framework"><defs><marker id="fwArrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#71809a"/></marker></defs>{kinds.map((kind,i)=><text key={kind} x={70+i*205} y={58} fontSize="10" fontWeight="800" fill="#71809a" letterSpacing="1">{kind.toUpperCase()}</text>)}<g>{edges.map((e,i)=><path key={i} d={edgePath(e,i)} fill="none" stroke="#8795a8" strokeWidth="1.5" strokeOpacity=".72" markerEnd="url(#fwArrow)"/> )}</g>{laneNodes.map(n=>{const c=kindColor[n.kind]||'#5f7fa8';return <g key={n.id}><rect x={n.x} y={n.y} width={n.w} height={n.h} rx="14" fill="#fff" stroke={c} strokeOpacity=".55"/><rect x={n.x} y={n.y} width="5" height={n.h} rx="3" fill={c}/><text x={n.x+16} y={n.y+25} fontSize="10" fontWeight="800" fill="#203653">{String(n.label).slice(0,25)}</text><text x={n.x+16} y={n.y+45} fontSize="7.5" fill="#71809a">{String(n.reason||'Requirement-derived').slice(0,39)}</text></g>})}</svg></div><div className="framework-edge-list">{edges.map((e,i)=><div key={i}><b>{byId[e.from]?.label||e.from}</b><span>{e.label||'request flow'}</span><b>{byId[e.to]?.label||e.to}</b></div>)}</div></section>
    <section className="section-card"><SectionHead eyebrow="REQUIREMENT EVIDENCE" title="Why the framework contains these elements"/><div className="framework-element-grid">{nodes.map(n=><article className={`framework-element kind-${n.kind}`} key={n.id}><div className="framework-kind">{n.kind}</div><h4>{n.label}</h4><p>{n.reason}</p>{n.requirements?.length?<small>Linked requirements: {n.requirements.join(' · ')}</small>:null}</article>)}</div></section>
    <section className="section-card"><SectionHead eyebrow="ARCHDS RESEARCH FRAMEWORK" title="Multi-agent reasoning pipeline"/><div className="agent-framework">{(agentFw.stages||[]).map((stage,i)=><React.Fragment key={stage.id}><article className="agent-stage"><span className="stage-number">{String(i+1).padStart(2,'0')}</span><div><b>{stage.label}</b><p>{(stage.agents||[]).join(' · ')}</p>{stage.rule&&<small>{stage.rule}</small>}</div>{stage.id==='competition'&&<div className="candidate-pills">{(stage.candidates||[]).map(c=><span key={c.id}>{c.label}</span>)}</div>}</article>{i<(agentFw.stages||[]).length-1&&<div className="agent-stage-arrow">↓</div>}</React.Fragment>)}</div><div className="human-gate"><b>Human decision gate</b><span>{agentFw.human_gate||'The final decision remains with the human architect.'}</span></div></section>
  </div>;
}
function UML({candidate}){
  if(!candidate?.uml_svg) return <EmptyState/>;
  const diagrams=[['use_case','USE CASE','Actors, system boundary and user-driven functions'],['class','CLASS','Domain classes and requirement-derived relationships'],['sequence','SEQUENCE','Actual request interaction through the generated architecture']];
  const encode=svg=>`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  return <div className="stack uml-page"><section className="section-card uml-hero"><div><span className="eyebrow">REQUIREMENT-DERIVED UML</span><h2>UML generated from this analysis</h2><p>These diagrams are regenerated from the functional requirements and selected architecture. No fixed hospital/e-commerce diagram is embedded.</p></div><div className="uml-badge">UML</div></section>{diagrams.map(([key,title,desc])=><section className="section-card uml-card" key={key}><SectionHead eyebrow={title} title={desc}/><div className="uml-viewport"><img src={encode(candidate.uml_svg[key])} alt={`${title} diagram generated from requirements`}/></div><details><summary>Show generated PlantUML source</summary><pre>{candidate.uml_plantuml?.[key]||''}</pre></details></section>)}</div>}
function Explainability({candidate,result}){
  if(!candidate)return <EmptyState/>;
  const exp=result.explanations?.find(x=>x.candidate_id===candidate.candidate_id)||{};
  const reqs=result.requirement_profile?.requirement_records||[];
  const driverMap=result.requirement_profile?.driver_mapping||[];
  return <div className="stack"><section className="section-card explain-hero"><span className="eyebrow">EXPLAINABLE AI · EVIDENCE CHAIN</span><h2>Why ARCHDS produced this architecture</h2><p>{exp.rationale||candidate.description}</p><div className="explain-metrics"><Metric value={`${confidencePct(exp.confidence||0)}`} label="Decision confidence" accent="green"/><Metric value={`${Object.values(candidate.requirement_coverage||{}).filter(Boolean).length}/${Object.keys(candidate.requirement_coverage||{}).length}`} label="Requirements covered" accent="cyan"/><Metric value={candidate.is_pareto_optimal?'Yes':'No'} label="Pareto efficient" accent="amber"/></div></section><section className="section-card"><SectionHead eyebrow="REQUIREMENT → EVIDENCE → ARCHITECTURE" title="Every decision is tied to the submitted requirement"/><div className="explain-grid">{reqs.map(r=>{const rid=r.id;const comps=candidate.requirement_mappings?.[rid]||[];const drivers=driverMap.find(x=>x.requirement_id===rid)?.drivers||[];return <article className="explain-card" key={rid}><div className="explain-card-top"><span className="req-badge">Requirement evidence</span><strong>{candidate.requirement_coverage?.[rid]?'COVERED':'GAP'}</strong></div><h4>{r.description}</h4><p><b>Architectural driver:</b> {drivers.length?drivers.join(', '):'Derived directly from this requirement'}</p><p><b>Implemented by:</b> {comps.length?comps.join(', '):'No direct component mapping returned'}</p><small>Evidence chain: submitted requirement → architectural driver → mapped component(s). This explanation is regenerated for this analysis and is not a generic template.</small></article>})}</div></section><div className="grid-2"><section className="section-card"><SectionHead eyebrow="TRADE-OFFS" title="What the optimization accepted"/>{(exp.tradeoffs||candidate.disadvantages||[]).map((x,i)=><div className="bullet" key={i}><i>↳</i><span>{x}</span></div>)}</section><section className="section-card"><SectionHead eyebrow="RISK & ASSUMPTIONS" title="What still needs human judgement"/>{[...(exp.risks||[]),...(exp.assumptions||candidate.assumptions||[])].slice(0,10).map((x,i)=><div className="bullet" key={i}><i>!</i><span>{x}</span></div>)}</section></div></div>
}

function TwinTopology({candidate,twin}){
  const g=candidate?.graph||{};
  const all=(g.nodes||[]).filter(n=>n?.label);
  const stateByLabel=Object.fromEntries(Object.entries(twin?.twin?.components||{}));
  const nodes=all.slice(0,16);
  const byId=Object.fromEntries(nodes.map(n=>[n.id,n]));
  const bucket=n=>{const l=String(n.layer||'').toLowerCase();if(/experience|client|ui/.test(l))return 0;if(/edge|gateway|security|identity/.test(l))return 1;if(/business|service|domain|application/.test(l))return 2;if(/data|integration|platform|messaging|observ/.test(l))return 3;return 2};
  const buckets=[[],[],[],[]];nodes.forEach(n=>buckets[bucket(n)].push(n));
  const positions={}; const xs=[25,270,515,760]; const w=205,h=62;
  buckets.forEach((list,col)=>list.forEach((n,row)=>{positions[n.id]={x:xs[col],y:34+row*92,w,h}}));
  const edges=[];const seen=new Set();
  (g.edges||[]).forEach(e=>{if(!byId[e.source]||!byId[e.target])return;const k=`${e.source}->${e.target}`;if(!seen.has(k)&&edges.length<24){seen.add(k);edges.push(e)}});
  const route=(a,b,i)=>{const A=positions[a.id],B=positions[b.id];if(!A||!B)return '';const sx=A.x+A.w,sy=A.y+A.h/2,tx=B.x,ty=B.y+B.h/2;const forward=tx>=sx-5;if(forward){const mx=(sx+tx)/2;return `M${sx} ${sy} H${mx} V${ty} H${tx}`;}const lane=510+i*7;return `M${A.x} ${sy} H${lane} V${ty} H${tx+A.w}`};
  const height=Math.max(300,Math.max(...buckets.map(x=>x.length))*92+50);
  return <div className="twin-topology"><div className="twin-topology-meta"><span>Requirement-derived runtime topology</span><small>Critical path view · {nodes.length}{all.length>nodes.length?` of ${all.length}`:''} components · {edges.length} routed dependencies</small></div><svg viewBox={`0 0 1000 ${height}`} role="img" aria-label="Digital twin topology"><defs><marker id="twinArrowClean" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="#91a0b3"/></marker></defs><g className="twin-links">{edges.map((e,i)=>{const a=byId[e.source],b=byId[e.target];return <path key={i} d={route(a,b,i)} fill="none" stroke="#9eacbd" strokeWidth="1.15" markerEnd="url(#twinArrowClean)" opacity=".82"/>})}</g>{nodes.map(n=>{const p=positions[n.id],st=stateByLabel[n.label]||{},load=Number(st.load||0),failed=st.status==='FAILED',hot=load>=85;const fill=failed?'#fff1f3':hot?'#fff8e9':'#fff';const stroke=failed?'#d95c70':hot?'#d39a35':'#cbd8e8';return <g key={n.id}><rect x={p.x} y={p.y} width={p.w} height={p.h} rx="12" fill={fill} stroke={stroke} strokeWidth="1.25"/><circle cx={p.x+16} cy={p.y+17} r="5" fill={failed?'#d95c70':hot?'#d39a35':'#22a77a'}/><text x={p.x+28} y={p.y+20} fontSize="9" fontWeight="800" fill="#263b58">{String(n.label).slice(0,31)}</text><text x={p.x+14} y={p.y+40} fontSize="7.2" fill="#78879e">{failed?'FAILED':`LOAD ${load.toFixed(0)}%`} · {n.layer||'runtime'}</text></g>})}</svg><div className="twin-legend"><span><i className="healthy"/>Healthy</span><span><i className="hot"/>High load</span><span><i className="failed"/>Failed</span></div></div>
}

function ArchitectureAdvisor({projectId,result}){
  const [question,setQuestion]=useState(''); const [busy,setBusy]=useState(false); const [answer,setAnswer]=useState(null); const [error,setError]=useState('');
  const ask=async()=>{if(!question.trim())return;setBusy(true);setError('');try{const r=await projects.advisor(projectId,question.trim());setAnswer(r.data)}catch(e){setError(errorMessage(e))}finally{setBusy(false)}};
  const prompts=['Why is the selected architecture a good fit for my requirements?','Which submitted requirement is most at risk, and what evidence supports that?','How would the selected architecture respond if my workload increased significantly?','Which components implement my highest-priority requirements?','What should I validate before accepting this architecture?'];
  return <div className="stack advisor-page"><section className="advisor-hero section-card"><div><span className="eyebrow">ARCHITECTURE ADVISOR</span><h2>Ask ARCHDS about this architecture.</h2><p>Ask questions in plain language. The advisor uses the submitted requirements, selected candidate, reviewer findings, optimization evidence and architecture mappings rather than a generic chatbot knowledge base.</p></div><div className="advisor-badge">AI</div></section><section className="section-card"><div className="advisor-input"><textarea value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();ask()}}} placeholder="Ask about risks, trade-offs, scalability, security, requirements, Digital Twin scenarios or deployment decisions…"/><button className="btn primary" disabled={busy||!question.trim()} onClick={ask}>{busy?'Reviewing evidence…':'Ask ARCHDS ↗'}</button></div><div className="advisor-prompts">{prompts.map(p=><button key={p} onClick={()=>setQuestion(p)}>{p}</button>)}</div></section>{error&&<div className="alert error"><b>Advisor unavailable:</b> {error}</div>}{answer&&<><section className="section-card advisor-answer"><div className="advisor-answer-head"><div><span className="eyebrow">EVIDENCE-GROUNDED ANSWER</span><h3>{answer.mode==='llm'?'Senior architecture reasoning':'Deterministic architecture reasoning'}</h3></div><span className="advisor-source">Based on this analysis</span></div><p className="advisor-text">{answer.answer}</p>{(answer.issues||[]).length>0&&<div><h4>Issues requiring attention</h4>{answer.issues.map((x,i)=><div className="advisor-item" key={i}><b>{x.severity} · {x.title}</b><span>{x.detail}</span></div>)}</div>}{(answer.suggestions||[]).length>0&&<div><h4>Recommended next actions</h4>{answer.suggestions.map((x,i)=><div className="advisor-item suggestion" key={i}><b>Action {i+1}</b><span>{x}</span></div>)}</div>}</section><section className="section-card"><SectionHead eyebrow="DECISION CONTEXT" title="Evidence used by the advisor"/><div className="tag-row big"><span>{answer.evidence?.architecture||result.recommendation?.name}</span>{(answer.evidence?.drivers||[]).map(x=><span key={x}>{x}</span>)}</div></section></>}</div>
}
function DigitalTwin({projectId,result,scenarios,twin,loadScenarios,runScenario}){
  const [active,setActive]=useState(null); const [intensity,setIntensity]=useState(1); const [evolution,setEvolution]=useState(null); const [evolving,setEvolving]=useState(false); const [evolutionError,setEvolutionError]=useState('');
  useEffect(()=>{if(!scenarios.length)loadScenarios()},[projectId]);
  const selected=active||scenarios[0];
  const metrics=twin?.metrics||{}; const delta=twin?.delta||{};
  const run=async()=>{if(!selected)return;setEvolution(null);setEvolutionError('');await runScenario(selected.id,intensity)};
  const evolveTwin=async()=>{if(!selected)return;setEvolving(true);setEvolutionError('');try{const r=await projects.digitalTwinEvolve(projectId,{scenarioId:selected.id,intensity});setEvolution(r.data)}catch(e){setEvolutionError(errorMessage(e))}finally{setEvolving(false)}};
  return <div className="twin-page stack">
    <section className="twin-hero section-card"><div><span className="eyebrow">ARCHITECTURE DIGITAL TWIN</span><h2>Test the selected architecture before deployment.</h2><p>The twin is reconstructed from the selected candidate and the submitted requirements. Every scenario changes the simulation inputs and produces a new propagation result, metric delta and mitigation plan.</p><div className="twin-badges"><span>Requirement-linked</span><span>Deterministic replay</span><span>Failure propagation</span><span>Adaptive response</span></div></div><div className="twin-core"><b>{result.recommendation?.name}</b><span>{result.recommendation?.components?.length||0} modeled components</span></div></section>
    <section className="section-card"><SectionHead eyebrow="SCENARIO LAB" title="What-if experiments grounded in this architecture"/><div className="scenario-grid scenario-grid-wide">{scenarios.map(s=><button key={s.id} className={`scenario-option ${selected?.id===s.id?'active':''}`} onClick={()=>{setActive(s);}}><div className="scenario-top"><b>{s.title}</b><em className={s.relevance==='HIGH'?'high':''}>{s.relevance}</em></div><span>{s.subtitle}</span><small>{s.change}</small></button>)}</div>{!scenarios.length&&<div className="empty-state compact"><b>Building requirement-grounded scenarios…</b><span>ARCHDS is deriving the scenario set from the submitted requirements.</span></div>}
      <div className="twin-controls"><label>Stress intensity <b>{intensity.toFixed(1)}×</b><input type="range" min="0.5" max="2" step="0.1" value={intensity} onChange={e=>{setIntensity(Number(e.target.value));}}/></label><button className="btn primary" disabled={!selected} onClick={run}>Run simulation ↗</button><button className="btn secondary" disabled={!selected||evolving||!twin} onClick={evolveTwin}>{evolving?'Evolving…':'Evolve architecture ↗'}</button></div>
      {selected&&<div className="scenario-why"><b>Why this scenario:</b> {selected.why}<span> · Requirement anchor: {selected.requirement_anchor}</span></div>}
    </section>
    {twin&&<>
      <section className="section-card"><SectionHead eyebrow="DIGITAL TWIN TOPOLOGY" title="Live simulated state of the selected architecture"/><TwinTopology candidate={result.recommendation} twin={twin}/></section>
      <section className="metric-grid twin-metrics"><Metric value={metrics.architecture_score??'—'} label="Twin score" accent="violet"/><Metric value={`${metrics.availability_index??'—'}`} label="Availability index" accent="green"/><Metric value={`${metrics.latency_index??'—'}`} label="Latency index" accent="cyan"/><Metric value={`${metrics.resilience_index??'—'}`} label="Resilience index" accent="amber"/></section>
      <section className="section-card twin-result-card"><div className="twin-result-head"><div><span className="eyebrow">SIMULATION RESULT</span><h3>{twin.scenario?.title} · {twin.severity}</h3><p>{twin.timeline?.[1]?.state}</p></div><div className="score-delta"><b>{delta.architecture_score>0?'+':''}{delta.architecture_score??0}</b><span>score delta</span></div></div>
        <div className="delta-grid">{Object.entries(delta).filter(([k])=>k!=='architecture_score').map(([k,v])=><div key={k}><span>{k.replaceAll('_',' ')}</span><b className={Number(v)<0?'negative':'positive'}>{Number(v)>0?'+':''}{v}</b></div>)}</div>
        <div className="solution-panel"><span className="eyebrow">PROPOSED ARCHITECTURAL RESPONSE</span><h4>{twin.recommended_solution?.title||'Adaptive response'}</h4>{(twin.recommended_solution?.actions||twin.proposed_adaptations||[]).map(x=><div className="bullet" key={x}><i>✓</i><span>{x}</span></div>)}<p><b>Expected effect:</b> {twin.recommended_solution?.expected_effect}</p><p><b>Human gate:</b> {twin.recommended_solution?.human_gate}</p></div>
      </section>
      {evolution&&<section className="section-card evolution-card"><div className="twin-result-head"><div><span className="eyebrow">ARCHITECTURE EVOLUTION LOOP</span><h3>Counterfactual mitigation proposal</h3><p>{evolution.explanation}</p></div><div className="score-delta"><b>{evolution.recovery_ratio}%</b><span>stress recovery modeled</span></div></div><div className="metric-grid twin-metrics"><Metric value={evolution.baseline?.architecture_score??'—'} label="Baseline" accent="violet"/><Metric value={evolution.stressed?.architecture_score??'—'} label="Under stress" accent="amber"/><Metric value={evolution.projected_after_mitigation?.architecture_score??'—'} label="Projected after mitigation" accent="green"/></div><div className="evolution-grid"><div><span className="eyebrow">BLAST RADIUS</span><b>{evolution.blast_radius?.count||0} components affected</b><small>{(evolution.blast_radius?.requirements||[]).join(', ')||'No requirement mapping directly exposed.'}</small></div><div><span className="eyebrow">ARCHITECTURE PATCH</span>{(evolution.architecture_patch||[]).map(x=><div className="bullet" key={x.component}><i>+</i><span><b>{x.component}</b> — {x.reason}</span></div>)}{!(evolution.architecture_patch||[]).length&&<small>No structural mutation proposed; existing controls are sufficient for this stress level.</small>}</div></div><div className="solution-panel"><span className="eyebrow">DECISION GATE</span><h4>Review → Re-run competition → Pareto-check → Delivery validation</h4><p>{evolution.decision_gate?.message}</p></div></section>}
      {evolutionError&&<div className="inline-error"><b>Evolution analysis failed:</b> {evolutionError}</div>}
      <div className="grid-2"><section className="section-card"><SectionHead eyebrow="PROPAGATION" title="Affected requirements & components"/><div className="twin-state-list">{(twin.twin?.nodes||[]).filter(n=>n.status==='FAILED'||Number(n.load)>=85).slice(0,12).map(n=><div className="twin-state-row" key={n.id||n.label}><span className={`state-dot ${String(n.status).toLowerCase()}`}/><div><b>{n.label}</b><small>{n.layer||'runtime component'}</small></div><strong>{n.status==='FAILED'?'FAILED':`${Number(n.load||0).toFixed(0)}%`}</strong></div>)}{!(twin.twin?.nodes||[]).some(n=>n.status==='FAILED'||Number(n.load)>=85)&&<p className="muted">No component crossed the critical threshold in this run.</p>}</div>{(twin.affected_requirements||[]).length>0&&<div className="tag-row">{twin.affected_requirements.map(x=><span key={x}>{x}</span>)}</div>}</section>
      <section className="section-card"><SectionHead eyebrow="ASSUMPTIONS" title="What the simulation does not claim"/>{(twin.assumptions||[]).length?twin.assumptions.map(x=><div className="bullet" key={x}><i>!</i><span>{x}</span></div>):<p className="muted">The model uses the submitted requirement profile and selected architecture graph. Production traffic, cloud pricing and physical failure rates are not assumed.</p>}</section></div>
      <section className="section-card"><SectionHead eyebrow="IMPACT PROPAGATION" title="Change → affected area → recovery flow"/><div className="impact-flow"><div className="impact-flow-step trigger"><span>01 · TRIGGER</span><b>{twin.scenario?.title||'Selected scenario'}</b><small>{twin.scenario?.change||'Scenario input applied'}</small></div><div className="impact-flow-arrow">→</div><div className="impact-flow-step affected"><span>02 · BLAST RADIUS</span><b>{(twin.affected_components||[]).length} affected component(s)</b><small>{(twin.affected_components||[]).slice(0,4).join(' · ')||'No component crossed the modeled impact threshold'}</small></div><div className="impact-flow-arrow">→</div><div className="impact-flow-step requirements"><span>03 · REQUIREMENTS</span><b>{(twin.affected_requirements||[]).length} linked requirement(s)</b><small>{(twin.affected_requirements||[]).slice(0,4).join(' · ')||'No direct requirement mapping returned by the current graph'}</small></div><div className="impact-flow-arrow">→</div><div className="impact-flow-step recovery"><span>04 · RESPONSE</span><b>{(twin.proposed_adaptations||[]).length} mitigation action(s)</b><small>{(twin.proposed_adaptations||[]).slice(0,3).join(' · ')||'Review architecture controls'}</small></div></div><p className="simulation-note">Propagation is based on the generated architecture graph and requirement mappings. Unmapped dependencies are shown as unknown rather than assumed.</p></section>
      <section className="section-card"><SectionHead eyebrow="MITIGATION OPTIONS" title="Alternative responses for this scenario"/><div className="twin-alternatives">{(()=>{const sid=twin.scenario?.id;const options={traffic_surge:[['Scale out','Add horizontal autoscaling and load-aware routing.','Best when capacity headroom is the main issue.'],['Buffer the burst','Introduce a durable queue and apply back-pressure.','Best when short spikes overwhelm synchronous services.'],['Reduce hot-path work','Cache high-read responses and move non-critical work async.','Best when repeated reads or fan-out dominate latency.']],component_failure:[['Fail over','Use health checks and a redundant service/data boundary.','Best when availability targets dominate.'],['Contain the fault','Apply circuit breakers, bounded retries and graceful degradation.','Best when cascading failures are the primary risk.'],['Remove single points','Replicate critical components and test recovery paths.','Best when the topology has a critical singleton.']],security_pressure:[['Enforce at the edge','Centralize policy, rate limits and identity checks.','Best for concentrated inbound pressure.'],['Reduce blast radius','Apply least privilege and isolate sensitive services.','Best when trust boundaries are weak.'],['Preserve evidence','Harden immutable audit events and alerting.','Best when auditability is critical.']],data_growth:[['Optimize access','Index and partition the highest-volume data paths.','Best when query pressure dominates.'],['Separate workloads','Use read replicas or analytical storage boundaries.','Best when transactional and analytical loads compete.'],['Control retention','Tier archival data and cache safe repeat reads.','Best when storage growth drives cost.']]};const defaults=[['Add redundancy','Introduce a redundant runtime boundary and health-checked failover.','Best for availability and resilience.'],['Isolate dependencies','Use timeouts, circuit breakers and bounded retries.','Best for dependency instability.'],['Improve observability','Add correlated logs, metrics, traces and actionable alerts.','Best when diagnosis or recovery is slow.']];return (options[sid]||defaults).map((x,i)=><article className="twin-alternative" key={x[0]}><span>OPTION {String(i+1).padStart(2,'0')}</span><b>{x[0]}</b><p>{x[1]}</p><small>{x[2]}</small></article>)})()}</div><p className="simulation-note">Alternatives are decision-support suggestions, not automatically applied changes. Validate cost, operational ownership and requirement priorities before adopting one.</p></section>
      <section className="section-card"><SectionHead eyebrow="SIMULATION TIMELINE" title="What changed inside the twin"/><div className="twin-timeline">{(twin.timeline||[]).map((x,i)=><div className="twin-step" key={i}><span>{x.t}</span><div><b>{x.event}</b><p>{x.state}</p></div><em>{x.severity}</em></div>)}</div><p className="simulation-note">{twin.simulation_note}</p></section>
    </>}
  </div>
}

function DeliveryLab({projectId,result}){
  const [data,setData]=useState(null); const [busy,setBusy]=useState(false); const [error,setError]=useState('');
  const generate=async()=>{setBusy(true);setError('');try{const r=await projects.deliveryGenerate(projectId);setData(r.data)}catch(e){setError(errorMessage(e))}finally{setBusy(false)}};
  const download=(name,text)=>{const blob=new Blob([text],{type:'text/plain;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)};
  return <div className="stack delivery-page"><section className="delivery-hero section-card"><div><span className="eyebrow">DELIVERY ENGINEERING LAB</span><h2>Turn the selected architecture into reviewable deployment artifacts.</h2><p>Artifacts are generated from the current requirements, selected architecture and technology preferences. ARCHDS validates their structure locally and clearly separates generated starting points from production deployment.</p><div className="delivery-badges"><span>Requirement-derived</span><span>Terraform</span><span>Kubernetes</span><span>Docker Compose</span><span>Validation</span></div></div><button className="btn primary" onClick={generate} disabled={busy}>{busy?'Generating & validating…':'Generate delivery artifacts ↗'}</button></section>
    {error&&<div className="alert error"><b>Delivery lab failed:</b> {error}</div>}
    {data&&<><section className="metric-grid"><Metric value={data.status} label="Validation status" accent="green"/><Metric value={data.validation?.checks?.filter(x=>x.passed).length||0} label="Checks passed" accent="cyan"/><Metric value={data.derived_components?.length||0} label="Architecture elements" accent="violet"/><Metric value={data.deployable_components?.length||0} label="Deployable services" accent="amber"/></section><section className="section-card"><SectionHead eyebrow="GENERATED ARTIFACTS" title="Requirement-linked delivery package"/><div className="artifact-actions">{Object.entries(data.artifacts||{}).map(([key,value])=><button key={key} className="btn secondary small" onClick={()=>download(`ARCHDS_${key}.txt`,value)}>{key.replaceAll('_',' ')} ↓</button>)}</div><div className="artifact-grid">{Object.entries(data.artifacts||{}).map(([key,value])=><article className="artifact-card" key={key}><div className="artifact-card-head"><b>{key.replaceAll('_',' ')}</b><span>DERIVED</span></div><pre className="artifact-preview">{value}</pre></article>)}</div></section><section className="section-card"><SectionHead eyebrow="VALIDATION" title="Structural checks"/>{(data.validation?.checks||[]).map((x,i)=><div className="delivery-check" key={i}><span className={x.passed?'ok':'bad'}>{x.passed?'✓':'!'}</span><div><b>{x.message}</b><small>{x.artifact}</small></div></div>)}<p className="simulation-note">{data.research_note}</p></section></>}
    {!data&&<section className="section-card"><div className="empty-state compact"><b>No delivery package generated yet</b><span>Run the lab to derive deployment artifacts from the selected architecture and current requirements.</span></div></section>}
  </div>;
}
async function downloadReport(project){
  if(!project?.id){reportToast('This project has no valid ID, so the PDF cannot be generated.');return;}
  reportToast('Generating the PDF report…','info');
  try{
    const response=await reports.download(project.id);
    const contentType=String(response.headers?.['content-type']||'').toLowerCase();
    if(response.status!==200 || !response.data) throw new Error('The report service returned an empty response.');
    const blob=response.data instanceof Blob?response.data:new Blob([response.data],{type:'application/pdf'});
    const header=new Uint8Array(await blob.slice(0,5).arrayBuffer());
    const signature=String.fromCharCode(...header);
    if(blob.size<100 || signature!=='%PDF-'){
      let message='The server did not return a valid PDF file.';
      if(response.data instanceof Blob){try{const text=await response.data.text();const parsed=JSON.parse(text);message=parsed.message||parsed.error||message}catch{}}
      throw new Error(contentType.includes('json')?message:'Invalid PDF response from the server.');
    }
    const safeName=String(project.name||'Architecture_Study').replace(/[^a-z0-9]+/gi,'_').replace(/^_+|_+$/g,'')||'Architecture_Study';
    // Force a browser download instead of relying on Content-Disposition from XHR.
    // This works consistently behind Vite, Nginx and Spring Boot proxies.

    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');
    a.href=url;
    a.download=`ARCHDS_${safeName}_Architecture_Report.pdf`;
    a.style.display='none';
    document.body.appendChild(a);
    a.click();
    setTimeout(()=>{a.remove();URL.revokeObjectURL(url)},3000);
    reportToast('PDF generated successfully. Check your Downloads folder.','success');
  }catch(e){
    let message=errorMessage(e);
    if(e.code==='ECONNABORTED'||e.name==='CanceledError'||e.code==='ERR_NETWORK') message='PDF generation timed out or the backend is unreachable. Make sure the Spring Boot backend and AI service are running, then try again.';
    if(e.response?.data instanceof Blob){
      try{const text=await e.response.data.text();const parsed=JSON.parse(text);message=parsed.message||parsed.error||message}catch{}
    }
    reportToast(message);
  }
}
function Reports(){const [rows,setRows]=useState([]);const [busy,setBusy]=useState(null);useEffect(()=>{let live=true;projects.list().then(async r=>{const out=await Promise.all(r.data.map(async p=>{try{const x=await projects.result(p.id);return x.data?{project:p,result:x.data}:null}catch{return null}}));if(live)setRows(out.filter(Boolean))}).catch(()=>{});return()=>{live=false}},[]);return <div className="stack"><div className="page-title"><div><span className="eyebrow">PDF DELIVERABLES</span><h2>Architecture reports</h2><p className="muted">Real PDF files generated from the stored analysis: requirements, competition, runtime framework, UML, traceability and decision evidence.</p></div></div><section className="report-hero section-card"><div><span className="eyebrow">RESEARCH-GRADE REPORT ENGINE</span><h2>One click from analysis to a review-ready PDF.</h2><p>The server generates the PDF from the completed analysis object. It is not an HTML page renamed as PDF.</p></div><div className="report-icon">PDF</div></section><section className="section-card">{rows.length?rows.map(({project,result})=><div className="report-row" key={project.id}><div className="report-file">PDF<br/><span>REAL FILE</span></div><div className="row-main"><b>{project.name}</b><span>{result.recommendation?.name||'Architecture decision'} · {result.research_metrics?.requirement_coverage??0}% requirement coverage</span></div><button className="btn primary small" disabled={busy===project.id} onClick={async()=>{setBusy(project.id);await downloadReport(project);setBusy(null)}}>{busy===project.id?'Generating…':'Download PDF ↓'}</button></div>):<div className="empty-state"><div>PDF</div><b>No completed analyses yet</b><span>Finish an analysis and the generated PDF will appear here automatically.</span></div>}</section></div>}
function RBAC(){const roles=[['ADMIN','Full workspace administration, user management, audit visibility and system controls','admin@archds.local','Admin@12345'],['ARCHITECT','Create requirements, run synthesis, compare candidates, experiments and decisions','architect@archds.local','Architect@12345'],['REVIEWER','Read-only review of requirements, competition, evidence, diagrams, reports and audit information','reviewer@archds.local','Reviewer@12345']];return <div className="stack"><div className="page-title"><div><span className="eyebrow">ROLE-BASED ACCESS CONTROL</span><h2>Workspace permissions</h2></div></div><section className="section-card rbac-grid">{roles.map(([role,desc,email,pw])=><article className="role-card" key={role}><div className={`role-symbol role-${role.toLowerCase()}`}>{role.slice(0,1)}</div><span className="eyebrow">{role}</span><h3>{role}</h3><p>{desc}</p><div className="credential"><span>{email}</span><b>{pw}</b></div></article>)}</section><section className="section-card"><SectionHead eyebrow="CONTROL MODEL" title="How RBAC is applied"/><div className="permission-grid">{[['ADMIN','All workspace operations'],['ARCHITECT','Analysis creation + execution + decision'],['REVIEWER','Evidence + comparison + audit']].map(([r,p])=><div key={r}><b>{r}</b><span>{p}</span></div>)}</div></section></div>}
function Projects(){const [ps,setPs]=useState([]);useEffect(()=>{projects.list().then(r=>setPs(r.data)).catch(()=>{})},[]);return <div className="stack"><div className="page-title"><div><span className="eyebrow">WORKSPACE</span><h2>Architecture studies</h2></div><NavLink className="btn primary" to="/create-project">＋ New analysis</NavLink></div><section className="section-card">{ps.length?ps.map((p,i)=><NavLink className="project-list-row" to={`/project/${p.id}`} key={p.id}><div className={`project-icon p${i%4}`}>{p.name.slice(0,1).toUpperCase()}</div><div className="row-main"><b>{p.name}</b><span>{p.description}</span></div><div className="row-meta"><small>STUDY #{p.id}</small><strong>Open →</strong></div></NavLink>):<EmptyState/>}</section></div>}
function History(){const [rows,setRows]=useState([]);useEffect(()=>{projects.list().then(async r=>{const all=(await Promise.all(r.data.map(p=>projects.history(p.id)))).flatMap(x=>x.data);setRows(all)})},[]);return <div className="stack"><div className="page-title"><div><span className="eyebrow">RUN HISTORY</span><h2>Research executions</h2></div></div><section className="section-card">{rows.length?rows.map(x=><div className="history-row" key={x.jobId}><span className={`status-dot ${String(x.status).toLowerCase()}`}/><div><b>{x.status}</b><span>{x.currentStage}</span></div><strong>{x.progress}%</strong><small>{x.errorMessage||x.message}</small></div>):<EmptyState/>}</section></div>}
function Audit(){const [rows,setRows]=useState([]);useEffect(()=>{audit().then(r=>setRows(r.data)).catch(()=>{})},[]);return <div className="stack"><div className="page-title"><div><span className="eyebrow">AUDITABILITY</span><h2>Decision trail</h2></div></div><section className="section-card">{rows.length?rows.map(x=><div className="history-row" key={x.id}><span className="audit-mark">✓</span><div><b>{x.action}</b><span>{x.resource}</span></div><small>{new Date(x.timestamp).toLocaleString()}</small></div>):<EmptyState/>}</section></div>}
class AppErrorBoundary extends Component{
  constructor(props){super(props);this.state={error:null}}
  static getDerivedStateFromError(error){return {error}}
  componentDidCatch(error,info){console.error('ARCHDS UI render failure',error,info)}
  render(){
    if(this.state.error)return <div className="loading-page"><div className="section-card" style={{maxWidth:900}}><span className="eyebrow">UI DIAGNOSTICS</span><h2>The analysis result could not be rendered</h2><p>ARCHDS received a response, but a dashboard component encountered an unexpected rendering error. Your analysis data is preserved in PostgreSQL.</p><pre style={{whiteSpace:'pre-wrap',background:'#f5f7fb',padding:16,borderRadius:12,overflow:'auto'}}>{this.state.error?.stack||String(this.state.error)}</pre><div className="form-actions"><NavLink className="btn secondary" to="/projects">Back to projects</NavLink><button className="btn primary" onClick={()=>window.location.reload()}>Reload dashboard</button></div></div></div>;
    return this.props.children;
  }
}

export default function App(){return <AppErrorBoundary><Routes><Route path="/login" element={<Auth/>}/><Route path="/register" element={<Auth register/>}/><Route path="*" element={<Protected><Shell><Routes><Route path="/dashboard" element={<Dashboard/>}/><Route path="/projects" element={<Projects/>}/><Route path="/create-project" element={<Create/>}/><Route path="/project/:id" element={<Project/>}/><Route path="/history" element={<History/>}/><Route path="/reports" element={<Reports/>}/><Route path="/rbac" element={<RBAC/>}/><Route path="/audit" element={<RoleGate roles={['ADMIN','ARCHITECT','REVIEWER']}><Audit/></RoleGate>}/><Route path="*" element={<Navigate to="/dashboard"/>}/></Routes></Shell></Protected>}/></Routes></AppErrorBoundary>}
