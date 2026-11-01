# ARCHDS Digital Twin upgrade (V8.9.4)

## What changed
- Expanded the Digital Twin scenario lab from a relevance-filtered list that could collapse to one item into a 10-scenario experiment suite.
- Requirement-matched scenarios remain marked `HIGH`; additional scenarios are marked `CONTEXTUAL` so users can still stress-test risks that are not explicit in the requirement text.
- Added an impact propagation view: trigger → affected components → linked requirements → mitigation response.
- Added three scenario-specific alternative mitigation paths for traffic surges, component failures, security pressure, and data growth, with general alternatives for other scenarios.
- Preserved the deterministic simulation/evolution endpoints and requirement-linked architecture graph behavior.

## Scenario suite
Critical component failure, traffic surge, dependency outage, latency pressure, security pressure, data growth, disaster recovery, deployment rollback, regional outage, and peak workload window (the exact set can vary slightly with requirement relevance while remaining capped at 10).

## Validation
- Python byte-compilation passed for the Digital Twin service.
- Smoke-tested all returned scenarios with a representative candidate graph; simulation results and architecture evolution returned successfully.
- Frontend production build was attempted but did not complete within the execution time limit; run `npm ci && npm run build` in `frontend/` before deployment.

## Research integrity note
Digital Twin scores are deterministic analytical estimates, not measured production SLOs. Proposed alternatives require architecture-owner review and validation before implementation.
