## V8.9.3 — Automated requirement-to-architecture discovery

Minimal-input architecture synthesis, inferred functional and non-functional requirements, requirement-derived objective weights, concrete technology recommendations, connected system-design patterns, and optional advanced constraints. Existing Digital Twin, Delivery Lab, UML, traceability, Pareto comparison, and decision audit workflows are retained.

# ARCHDS — Adaptive Requirements-to-Architecture Decision System

**From requirements to architecture — reasoned, challenged, optimized.**

ARCHDS is an explainable architecture decision support platform for a Master's thesis. It does not use a fixed architecture template. It derives architectural drivers from requirements, retrieves relevant architecture knowledge, creates differentiated candidates, independently challenges them, refines weaknesses, performs multi-objective Pareto analysis, detects convergence and produces a requirement-traceable recommendation.

## Stack
- Frontend: React 19 + Vite, responsive enterprise UI, interactive SVG architecture graph.
- Backend: Spring Boot 3.3, Java 21, PostgreSQL/H2, JWT + BCrypt, asynchronous jobs.
- AI: Python/FastAPI, Pydantic, deterministic provider, optional OpenAI-compatible provider, semantic retrieval option, Pareto optimization.
- Deployment: Docker Compose.

## Run
```text
copy .env.example .env
docker compose up --build
```
Open `http://localhost:3000` with Docker, or `http://localhost:5173` for local Vite development.

**Windows local development:** run `scripts\start-ai.cmd`, `scripts\start-backend.cmd`, and `scripts\start-frontend.cmd` in three terminals. A one-click launcher is also included as `scripts\START-ARCHDS.cmd`. For the complete no-Docker stack, use `scripts\START-NO-DOCKER.cmd`.
Backend health: `http://localhost:8080/api/health`.
AI health: `http://localhost:8000/health`.

Development demo credentials: `demo@archds.local` / `Demo@12345`.

**No-Docker default database:** local PostgreSQL at `localhost:5432/architecture_db` using `architecture_user` / `host`. See `docs/LOCAL-POSTGRES-SETUP.md`.

## Research loop
1. Natural-language or structured requirements.
2. Completeness, specificity, ambiguity and contradiction analysis.
3. Driver extraction and requirement-derived priority weighting.
4. Architecture knowledge retrieval.
5. Multiple requirement-adapted candidates.
6. Independent security, scalability/performance, reliability and cost/complexity review.
7. Consistency verification.
8. Multi-objective evaluation and Pareto frontier.
9. Targeted refinement and re-evaluation.
10. Stop on convergence or maximum iterations.
11. Judge, explain, visualize and trace every requirement to evidence.

## Key endpoints
- `POST /api/projects`
- `POST /api/projects/{id}/requirements`
- `POST /api/projects/{id}/requirements/analyze`
- `POST /api/projects/{id}/run-analysis`
- `GET /api/jobs/{jobId}`
- `GET /api/projects/{id}/analysis`
- `POST /api/projects/{id}/what-if`
- `POST /api/projects/{id}/stress-test`
- `POST /api/projects/{id}/decision`

## Validation
AI tests are in `ai-service/tests`. Backend tests are under `backend/src/test`. Frontend is validated with `npm run build`. Docker Compose provides the production-like integration topology.

See `docs/research-methodology.md`, `docs/evaluation-methodology.md` and `docs/experiment-guide.md` for dissertation experiments.

## V3.1 fix included
The frontend now normalizes Spring Boot snake_case job responses (`job_id`, `current_stage`, `error_message`) to the UI fields used by the polling state. This prevents requests such as `/api/jobs/undefined` and allows the Review → Analysis page to advance when the asynchronous job starts. The job polling also rejects a missing job ID instead of generating an invalid URL.


## V2 research features

- **Architecture Evolution Engine:** each refinement round creates a traceable challenger from the current champion, applies evidence-driven mutations, runs critic and verification agents, re-evaluates objectives, and performs survivor selection.
- **Convergence guard:** the loop stops after repeated rounds without measurable improvement once high-severity findings are resolved.
- **Adversarial Stress Tournament:** 10x/100x traffic, database failure and region failure challenge every surviving architecture and compare resilience scores, weaknesses and mitigations.
- **Decision evidence:** refinement history records champion, challenger, score delta, high-risk findings and round duration.
- **Clean UML:** requirement-derived component topology with deterministic layout and PlantUML source.


## Final reliability fixes
- Natural-language-only descriptions are accepted; the requirement agent derives an initial functional/NFR profile when structured fields are omitted.
- The selected alternative always receives a structured SVG-ready graph and PlantUML source before the result is returned, preventing an empty Architecture canvas.
- The Alternatives and Max iterations controls are persisted and used by the backend analysis worker instead of being silently replaced with fixed values.
- The frontend shows an explicit diagram error state instead of a blank canvas if a future malformed result is returned.

## Final release verification
Run `scripts\VERIFY-FINAL.cmd` after starting the services. The AI automated suite includes arbitrary-domain, requirement-dependent, natural-language-only, and renderable-UML checks.

### Expected architecture-page behavior
The Architecture tab is backed by structured `graph.nodes` / `graph.edges` data and generated PlantUML. It no longer relies on a static image or a best-effort blank canvas. If malformed data ever reaches the UI, an explicit diagram error state is shown instead of an empty panel.

## V4.1 UI / Research Demonstration Upgrade

The result workspace now exposes the architecture competition as a first-class research artifact:

- **Live Agent Arena** during execution: requirement input → candidate arena → active agent → champion goal.
- **Competition tab** after execution with candidate battlefield, requirement-weighted scores, Pareto survivors, challenger rounds and agent evidence.
- **Tournament snapshot** on the Overview page so reviewers immediately see that the result came from competing alternatives rather than a static template.
- **Requirement-specific evidence framing** explicitly connects the competition to extracted drivers and quality objectives.
- **Animated transitions** for active agents, challenger flow, score bars and research pipeline cards.
- Fixed primary navigation/action text contrast so buttons such as **New analysis** remain readable.

The underlying workflow remains: Requirement intelligence → RAG evidence → candidate generation → multi-objective evaluation → Pareto optimization → critique → verification → challenger refinement → re-evaluation → convergence → diagram generation → explanation → judge.

## V7.5 additions

- Digital Twin scenario laboratory with 12 requirement-grounded what-if scenarios and intensity-sensitive simulation.
- Compact routed Digital Twin topology to prevent overlapping nodes/edges.
- Closed-Loop Delivery Lab for requirement-derived Terraform/Kubernetes starting artifacts with local structural validation and feedback repair.
- Reliability-first PDF engine using ReportLab primitives so report generation does not depend on browser SVG parsing.
- Improved UML routing and requirement-derived class/entity extraction.


## Automated requirement-to-architecture workflow (V8.8 automation update)

The default analysis path requires only a project title and a short natural-language description. Functional requirements, quality attributes, architectural drivers, and domain defaults are inferred by the requirement-analysis stage. Additional fields are optional refinements, not prerequisites.

Objective scores are produced by the evaluator from candidate-specific criteria. Objective weights are derived from the inferred requirement profile by default. A user may optionally provide custom priorities, but does not enter candidate scores. The system records assumptions and uses clarification questions only when a missing detail materially affects the design.

Technology recommendations are evidence-labelled defaults, not universal truths: transactional business systems generally receive a relational system-of-record recommendation; Redis is recommended when workload signals justify caching; RabbitMQ is used for ordinary asynchronous business workflows; Kafka is reserved for high-volume event streams/telemetry; and framework choices are explained by domain and operational needs. Explicit technology constraints take precedence. Review recommendations before production use.


### Updated automated-input experience

The create-study screen now requires only a project title and short description. Optional advanced fields are collapsed by default. Candidate objective scores are generated by the evaluator; users do not enter candidate scores. Quality-attribute weights are inferred from the requirement profile unless optional custom priorities are explicitly supplied. The AI service health endpoint identifies this build with `release: AUTO-REQUIREMENTS`.
