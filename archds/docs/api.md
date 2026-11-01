# API Contract

All protected endpoints use `Authorization: Bearer <JWT>`.

## Analysis
`POST /api/projects/{id}/run-analysis` returns `202 Accepted` and a job object with `job_id`, `status`, `progress`, `current_stage` and `message`.

`GET /api/jobs/{jobId}` returns live status: `QUEUED`, `RUNNING`, `COMPLETED` or `FAILED`.

`GET /api/projects/{id}/analysis` returns the complete validated AI result after completion.

## Decision
`POST /api/projects/{id}/decision` accepts `{ "candidateId": "cand-...", "rationale": "..." }` and records a human decision plus audit event.
