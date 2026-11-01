# ARCHDS V6

This release focuses on making the research contribution visible rather than merely describing it.

## Core idea
ARCHDS accepts natural-language requirements, derives architectural drivers and business capabilities, creates multiple architecture candidates, subjects them to independent critics and verification, creates evidence-driven challengers, re-evaluates the pool, applies Pareto optimization and produces a traceable champion architecture.

## New visual research evidence
- Competition Arena
- Round-by-round replay
- Challenger vs current champion
- Side-by-side survivor cards
- Requirement fingerprint
- Champion evolution history
- Agent evidence trail
- Requirement IDs on architecture components
- Clean UML lanes and orthogonal relations
- PlantUML source with requirement references

## Run without Docker
### AI
`cd ai-service`
`python -m venv .venv`
`.venv\\Scripts\\activate`
`python -m pip install -r requirements.txt`
`uvicorn app.main:app --host 0.0.0.0 --port 8000`

### Backend
`cd backend`
`mvn spring-boot:run`

### Frontend
`cd frontend`
`npm install`
`npm run dev`

Open http://localhost:5173

## V7 UML fidelity upgrade
The UML/architecture view is now treated as a validated projection of the candidate architecture model. Before a candidate is shown as diagram-complete, ARCHDS checks that every component and dependency in the architecture graph is represented exactly once in the diagram, that no unmodelled edges are introduced, that requirement traceability references are valid, and that the PlantUML source is complete. The UI exposes this validation state.
