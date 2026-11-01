# Dissertation Traceability Matrix

| Dissertation requirement | Implementation |
|---|---|
| Centralized architecture decision support | React + Spring Boot workspace |
| Functional/non-functional requirements | Create Project wizard + persisted requirements |
| Specialized agents | 9 explicit Python agent modules |
| Architecture knowledge retrieval | Retrieval agent with lexical fallback and optional Sentence Transformers reranking |
| Multiple alternatives | Requirement-adapted candidate generation, 2–8 candidates |
| Quality evaluation | 8 quality attributes, 0–100 scores and explanations |
| User priorities | Eight validated integer weights totaling 100 |
| Multi-objective optimization | NSGA-II through pymoo, with dependency-free NSGA-II fallback |
| Pareto analysis | Exact candidate-level nondominance + objective visualization |
| Critique | Dedicated critique agent |
| Verification | Requirement coverage and consistency checks |
| Iterative refinement | Critique-driven iterations followed by re-evaluation/re-verification |
| Explainability | Rationale, strengths, trade-offs, risks, assumptions, confidence and change factors |
| PlantUML | Candidate-derived PlantUML source + optional SVG rendering + source fallback |
| Human decision control | Decision endpoint records selected candidate and rationale |
| Auditability | Audit log plus job history and persisted analysis artifacts |
| Async workflow | AnalysisJob with QUEUED/RUNNING/COMPLETED/FAILED and polling |
| Security | BCrypt, JWT expiry, RBAC, CORS, validation, sanitized errors |
| Database | PostgreSQL production profile; H2 development profile; structured relational entities |
| Docker | PostgreSQL, AI service, backend and frontend with health checks |
| Arbitrary domains | No banking-specific pipeline logic; domain drivers are inferred from input |
