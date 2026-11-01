# ARCHDS V7.1 — Final Validation Record

## Included in this package

- Requirement-driven candidate generation
- Requirement completeness/specificity/consistency/ambiguity analysis
- Technology preferences and restrictions
- Differentiated architecture candidates
- Specialist/adversarial review
- Iterative refinement and convergence evidence
- Discrete non-dominated Pareto analysis
- Requirement traceability and decision evidence
- Separate multi-agent research framework
- Separate runtime system-design framework
- Requirement-derived Use Case, Class and Sequence UML
- What-if and stress-test experiments
- Human decision gate and ADR evidence
- 3-role RBAC: ADMIN, ARCHITECT, REVIEWER
- Persistent local PostgreSQL by default without Docker
- Docker PostgreSQL profile retained
- Real PDF generation through ReportLab
- PDF download through the Spring Boot API
- Responsive research-grade UI

## Validation performed in the packaging environment

- AI service automated tests: **13 passed**
- Python application source imports through the test suite
- PDF report module is included and wired to both AI and Spring Boot endpoints
- Maven `mainClass` is explicitly configured as `com.vit.archds.ArchDsApplication`
- No-Docker startup explicitly selects the PostgreSQL profile
- No-Docker startup verifies local `psql` connectivity before launching services
- Frontend source is carried forward from the research-grade UI package

## Local Windows verification

The packaging environment does not contain Maven and could not complete a Vite dependency installation, so the following two environment-dependent checks must be run on the target Windows machine:

```cmd
cd backend
mvn clean compile
mvn spring-boot:run
```

and from the project root:

```cmd
npm run build
```

The previous Maven main-class failure is addressed by the explicit Spring Boot `mainClass` configuration in `backend/pom.xml`.
