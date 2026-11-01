# ARCHDS V8 — Decision Intelligence Upgrade

## Major upgrades

- Professional **PDF decision package** instead of HTML reports.
- PDF contains the actual final decision, decision rationale, requirement coverage, candidate competition, traceability, risks, trade-offs, assumptions, research metrics and technology evidence.
- PDF embeds generated architecture, UML component and runtime sequence diagrams derived from the selected candidate graph.
- New **UML & Runtime** workspace tab with an interactive requirement-derived component blueprint and sequence-style runtime flow.
- Framework workspace upgraded with layered engineering lanes, component cards, technology evidence, deployment shape and animated runtime flow.
- Fixed dashboard hero heading visibility so the primary title is never rendered white-on-light.
- Competition remains candidate-specific and selectable; the selected candidate drives framework, UML and explainability views.
- What-if Lab expanded from one fixed scenario to eight challenge modes: traffic, user population, availability, latency, cost, regional failure, database replacement and framework replacement.
- What-if changes are injected into the AI pipeline as explicit challenge text rather than changing a visual label only.
- PDF endpoint added to the AI service at `/api/v1/report/pdf`.
- ReportLab + Pillow dependencies added.

## Requirement-driven guarantee

The upgrade does not introduce a universal architecture template. Diagrams, framework layers, UML artifacts and report content are rendered from the completed candidate returned by the requirement-driven pipeline.

## Validation

- Python AI service modules compile successfully.
- Full pipeline execution completed during release validation.
- PDF endpoint returned a valid `%PDF` document during validation.
- Generated report contained five A4 pages including architecture/UML/runtime artifacts.

## Run

```cmd
cd /d "C:\Users\Dell\Downloads\ARCHDS-Final-Complete-V8\archds-platform"
scripts\START-ARCHDS.cmd
```

Open `http://localhost:5173`.

If port 8000 is already running, the launcher reuses the healthy AI service instead of starting a second listener.
