# System Architecture

The platform is split into presentation, application/orchestration, AI/optimization and data layers. React calls protected Spring Boot APIs. Spring Boot owns authentication, projects, jobs, persistence and audit. Analysis is asynchronous and invokes the FastAPI pipeline over an internal service URL in Docker (`http://ai-service:8000`). PostgreSQL is reached as `postgres:5432` from the backend container. The AI service owns the nine-agent workflow, retrieval, scoring, NSGA-II optimization, verification, refinement, explanation and candidate-derived PlantUML.

Human decision authority is explicit: AI recommends; the user records the final decision.
