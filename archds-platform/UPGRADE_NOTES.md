# ARCHDS Research-Grade Upgrade

Base: ARCHDS Colourful/SpringBoot/UML V7, selected after comparison with the supplied V3.1 archive. V7 already contained the broader tournament/diagram/UI implementation; V3.1's relevant persistence fixes were retained.

## Major implementation changes
- Added an explicit 20-agent execution registry with independent deterministic specialist analyses.
- Added requirement records with confidence, ambiguity and architectural relevance.
- Added explicit requirement-to-driver mappings.
- Added independent security, scalability, performance, reliability, cost and maintainability reviews.
- Added hard-constraint checks and an auditable Architecture Judge policy.
- Added evidence-based confidence calculation.
- Added architecture diversity measurement.
- Added real convergence checks using critical findings, Pareto-frontier stability and score improvement.
- Added requirement → driver → decision → component → evidence → evaluation → critique traceability.
- Added actual SVG generation from the architecture graph and browser SVG/UML/PDF-print export controls.
- Added UML, Agent Board and Research tabs.
- Removed frontend inference that marks agents complete from percentage progress.
- Added semantic negation handling so phrases such as “No real-time processing” do not create a real-time driver.
- Made What-If analysis re-run the architecture pipeline against the changed workload/availability requirement.
- Updated stress analysis to compare candidate resilience under the requested scenario.
- Backend now passes the saved candidate-count and iteration-count settings into the AI service instead of hardcoding 5/5.
- Added acceptance and traceability tests.

## Validation
- AI service: `python -m pytest -q` → 9 passed.
- AI service: `python -m compileall -q app` → passed.
- End-to-end acceptance scenarios A/B/C executed successfully; the three generated architecture graphs were distinct.
- Frontend build could not be completed in the sandbox because the npm dependency installation stalled and left no usable Vite executable. The final ZIP intentionally excludes `node_modules`; run `npm install` followed by `npm run build` on Windows/local development.
- Maven was not available in the sandbox, so the Spring Boot build could not be executed here.
