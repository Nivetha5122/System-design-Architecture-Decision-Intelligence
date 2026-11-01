# ARCHDS V7 — Presentation, Competition, Reports & RBAC Upgrade

## Included

- Fixed the dashboard hero contrast so the headline remains readable on the light visual theme.
- Added a requirement-derived framework mini runtime map using the selected candidate's actual components.
- Added a functional Competition workspace with candidate sorting, score bars, coverage, Pareto state, reviewer finding counts and candidate selection.
- Added an AI-generated report centre to the side navigation. Completed analyses automatically appear there and can be downloaded as a self-contained HTML report.
- Added a report download button directly on the completed analysis decision board.
- Reports are assembled from the completed analysis result: project description, requirement records, architectural drivers, candidate competition, recommendation, confidence, traceability, risks, trade-offs and research metrics.
- Added RBAC roles: ADMIN, ARCHITECT, REVIEWER, USER.
- Added local demo accounts below.
- Added backend role-aware security rules for destructive operations, analysis execution, human decisions and audit access.
- Existing requirement-driven AI pipeline is preserved; the UI does not substitute a generic architecture when the user changes technology or quality requirements.

## Demo credentials

| Role | Email | Password |
|---|---|---|
| ADMIN | admin@archds.local | Admin@12345 |
| ARCHITECT | architect@archds.local | Architect@12345 |
| REVIEWER | reviewer@archds.local | Reviewer@12345 |
| USER | user@archds.local | User@12345 |

These are intentionally local/demo credentials for the development H2 profile. Change them before any non-local deployment.

## Report format

The report download is a self-contained HTML document. It can be opened in a browser and printed/saved as PDF from the browser print dialog without requiring an additional server-side PDF dependency.

## Validation note

The environment used to package this release does not contain Maven and the frontend dependency install could not complete within the build environment timeout, so a full production compile was not possible in this packaging environment. The source changes were made against the supplied project structure and should be verified with the provided Windows launcher on the target machine.
