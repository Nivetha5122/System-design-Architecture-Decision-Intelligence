# ARCHDS — Final Requirement-Driven Release

## What is fixed
- Removed the universal PostgreSQL fallback from architecture generation.
- Preserved technology preferences inside the requirement profile so the AI pipeline can actually use them.
- Added explicit/inferred technology evidence for databases, frameworks, messaging, cache, search and object storage.
- Added requirement-derived Framework Blueprint and Explainable AI views.
- Added a no-vendor state instead of silently inventing a vendor when the user did not specify one.
- Fixed the New Analysis flow so it does not start the same analysis twice.
- Improved Windows launcher behavior so already-healthy AI/backend/frontend services are reused instead of creating duplicate port-binding failures.
- Improved architecture graph data classification and SVG font rendering.
- Added a regression test proving MongoDB, generic SQL and Spring Boot/FastAPI inputs produce different technology outputs.

## Verification
AI service tests: **10 passed**.

## Important
The local 20-agent pipeline is deterministic/reproducible by default. It is not claimed to be a newly trained machine-learning model. The optional LLM provider remains available for enrichment when configured, while core architecture selection remains grounded in the supplied requirements.
