## V7.4 research product upgrade

Digital Twin simulation, requirement-grounded scenario lab, competitive multi-agent debate, simplified research workspace, requirement-specific explainability and cleaner architecture/UML visualization.

# ARCHDS V7.1 — Start Here

## Services

1. AI service: `scripts\start-ai.cmd`
2. Backend: `scripts\start-backend.cmd`
3. Frontend: from the project root run `npm run dev`

Or run `scripts\START-ARCHDS.cmd` for the project startup workflow.

## Important

After changing requirements, run a fresh analysis. Requirement-derived UML and the new runtime framework are generated as part of the analysis result, so an older stored result may not contain the new artifact fields.

The PDF button now downloads a real server-generated PDF from:

`GET /api/projects/{projectId}/report.pdf`

## Demo roles

- ADMIN — `admin@archds.local`
- ARCHITECT — `architect@archds.local`
- REVIEWER — `reviewer@archds.local`

New registrations receive the REVIEWER role.


## Database (V7.1.1)
Without Docker, ARCHDS now uses local PostgreSQL by default. See `docs/LOCAL-POSTGRES-SETUP.md`. H2 is retained only for explicit development/testing use.
