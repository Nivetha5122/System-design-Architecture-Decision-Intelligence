# ARCHDS Final UI & Architecture Visualization Upgrade

## What changed
- Reworked the architecture canvas into a clean, layered, requirement-derived blueprint.
- Fixed the previous fixed-lane layout that could make lower layers overlap when a requirement produced many components.
- Each layer is now sized from the actual number of generated components and stacked dynamically.
- Component cards use restrained pastel accents, vector-style service badges, dependency arrows, and requirement IDs.
- Added component inspection by clicking a node.
- Added animated Architecture Replay to reveal generated components progressively.
- Added subtle enterprise UI motion, hover states, glass navigation, improved cards, and responsive behavior.
- Preserved the existing requirement-specific multi-agent pipeline, candidate competition, critique, optimization, traceability and decision evidence.

## Requirement-specific principle
The visualizer consumes `candidate.graph` returned by the AI service. It does not select a fixed architecture template for display. Components, relationships, requirement links and candidate metadata are rendered from the selected candidate returned for the user's requirements.

## Validation performed
- Python AI service source compiled successfully with `python -m compileall`.
- Dynamic graph layout was tested with a multi-row candidate and confirmed with zero node overlaps.
- Existing frontend dependencies and scripts were preserved.

## Local run
1. Start the AI service on port 8000.
2. Start the Spring Boot backend on port 8080.
3. Start the frontend with `npm run dev` in `frontend`.
4. Open `http://localhost:5173`.

If Maven is not installed globally on Windows, start the existing Spring Boot backend from the IDE or use the project's Docker workflow.
