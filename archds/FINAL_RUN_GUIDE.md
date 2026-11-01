# ARCHDS Final Run Guide

## Windows
1. Open Command Prompt.
2. `cd /d "<extracted-folder>\archds-platform"`
3. Run `scripts\START-ARCHDS.cmd`.
4. Open http://localhost:5173

The launcher now checks ports 8000, 8080 and 5173 first and does not start duplicate services when one is already healthy.

## Requirement-driven behavior
- Technology preferences are preserved from the user input and passed into the AI profile.
- PostgreSQL is never injected as a universal default. If the user specifies MongoDB, MySQL, SQL, DynamoDB, etc., the candidate data layer follows that requirement.
- If no vendor is specified, ARCHDS keeps the vendor open or marks an inferred technology explicitly.
- Framework choices are derived from explicit preferences or clearly labeled as unspecified/inferred.
- Architecture components, relationships, framework blueprint, explanation, requirement mappings and diagrams are generated from the current requirement set.

## Local deterministic mode
The 20-agent pipeline is deterministic and reproducible by default. An external OpenAI-compatible provider can be configured through `LLM_API_KEY`, `LLM_BASE_URL` and `LLM_MODEL`, but the architecture decision remains grounded in the structured requirement profile.
