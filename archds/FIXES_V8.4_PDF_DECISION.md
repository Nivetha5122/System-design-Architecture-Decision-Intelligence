# ARCHDS V8.4 — PDF & Decision Fix

## Fixed
- Decision requests now accept both camelCase and snake_case candidate identifiers.
- Frontend decision submission now sends `candidate_id`, matching the backend API naming strategy.
- Candidate key normalization also accepts `candidateId`.
- PDF AI-service read timeout reduced so the UI cannot remain in Generating indefinitely when the AI service is unavailable.
- Spring backend retains a valid local PDF fallback when the AI report service fails or returns a non-PDF response.
- PDF response identifies whether the report came from the AI renderer or local fallback via `X-ARCHDS-Report`.

## Verification
- Python AI source/tests compile successfully.
- PDF renderer generated a valid `%PDF-` document successfully.
- Maven/frontend production builds could not be executed in this environment because Maven and frontend `node_modules` are not installed.
