# ARCHDS Research Methodology

ARCHDS evaluates architecture synthesis as a requirements-to-decision process rather than template retrieval. The experimental unit is an analysis run: a structured requirement set is converted into a requirement profile, architecture drivers, knowledge evidence and multiple differentiated candidates. Candidates are scored against user and requirement-derived priorities, reviewed by independent concern-oriented critics, verified, refined and re-evaluated until convergence or a maximum iteration limit is reached.

## Research variables
- Independent variables: candidate count, iteration limit, priority profile, baseline/ablation condition.
- Dependent variables: requirement coverage, weighted architecture quality, critical findings, refinement improvement, convergence iteration, reviewer agreement, diversity, runtime and Pareto frontier size.

## Baseline
The baseline is the initial single-pass candidate ranking before iterative critique/refinement. The proposed method is the converged multi-agent loop. This makes improvement measurable without claiming that an LLM alone is a ground-truth architect.

## Threats to validity
Deterministic scores are proxies for architectural quality and should be complemented by expert review in dissertation experiments. Workload estimates and cost are often uncertain. Results are therefore presented as decision support evidence, not guarantees.
