# ARCHDS Agent Design

ARCHDS uses an explicit 20-agent execution registry. The deterministic provider is the validation substrate; an optional OpenAI-compatible provider can enrich reasoning without being the authority.

## Execution stages

1. Requirement Analyst — structures functional/non-functional requirements and readiness.
2. Requirement Clarifier — surfaces only high-impact missing information.
3. Architectural Driver Analyst — maps requirements to drivers.
4. Architecture Knowledge Agent — retrieves and ranks relevant pattern evidence.
5. Architecture Generator — creates differentiated candidates from drivers and business capabilities.
6. Security Reviewer — tests security/trust/audit controls.
7. Scalability Reviewer — tests scale and traffic boundaries.
8. Performance Reviewer — tests real-time/latency paths.
9. Reliability Reviewer — tests failure domains and recovery.
10. Cost Reviewer — tests operational cost and complexity.
11. Maintainability Reviewer — tests engineering/operational maintainability.
12. Architecture Consistency Verifier — checks graph/component consistency.
13. Multi-Objective Evaluator — computes objective values using user and requirement-derived weights.
14. Pareto Optimizer — computes the non-dominated frontier.
15. Refinement Agent — modifies candidates in response to evidence.
16. Architecture Judge — applies hard constraints, critical findings, Pareto status, coverage and objective trade-offs.
17. Explainability Agent — creates requirement-linked rationale.
18. Diagram Agent — renders the selected architecture graph/UML source.
19. Traceability Agent — creates requirement → driver → decision → component → evidence → evaluation → critique chains.
20. Confidence & Research Metrics Agent — calculates evidence-based confidence and experiment metrics.

Every completed stage is represented in `agent_trace`; the UI does not infer completion from percentage progress.
