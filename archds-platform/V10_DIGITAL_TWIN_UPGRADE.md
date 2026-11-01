# ARCHDS V10 — Digital Twin Studio

## What was added

ARCHDS now includes a requirement-derived **Digital Twin Studio**. The twin is built from the selected candidate returned by the architecture pipeline rather than from a fixed sample topology.

### Digital Twin flow

`User Requirements → Requirement Profile → Selected Candidate → Actual Component Graph → Digital Twin State → Scenario Injection → Dependency Propagation → Requirement Impact → AI Actions`

### Scenario library

- Baseline runtime
- 10× traffic surge
- Regional failure
- Database degradation
- Latency injection
- Cache loss
- Security-control stress
- Custom scenario text

### Twin outputs

- Component health/state
- Component load
- Dependency in/out counts
- Requirement mappings affected
- Estimated latency
- Availability
- Throughput index
- Degraded / at-risk component count
- Event timeline
- Architecture-specific remediation suggestions

The UI is intentionally tied to the selected architecture's component names, relations and requirement mappings. It does not substitute a generic architecture template.

## New API

`POST http://localhost:8000/api/v1/digital-twin`

Payload:

```json
{
  "candidate": {"...": "selected Candidate object"},
  "requirement_profile": {"...": "RequirementProfile object"},
  "scenario_key": "traffic_10x",
  "custom_scenario": ""
}
```

## UI

Open an analysis and select **Digital Twin** beside What-if Lab. Choose a scenario, optionally enter a custom challenge, then run the simulation.
