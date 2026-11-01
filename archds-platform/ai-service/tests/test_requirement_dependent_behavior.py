from app.models import RequirementInput
from app.workflow.orchestrator import run_pipeline

def test_small_low_budget_prefers_simple_deployment():
    r=RequirementInput(project_name="Campus Attendance",description="Simple low cost attendance application",functional_requirements=["Record attendance"],non_functional_requirements=["Low cost"],expected_users="500 users")
    out=run_pipeline(r)
    assert out.recommendation.pattern_key in {"modular_monolith","layered","clean_hexagonal"}

def test_high_scale_realtime_prefers_distributed_candidate():
    r=RequirementInput(project_name="Realtime Platform",description="10 million users and real-time processing",functional_requirements=["Process events","Send live updates"],non_functional_requirements=["High traffic","High availability"] ,expected_users="10 million users")
    out=run_pipeline(r)
    assert out.recommendation.pattern_key in {"microservices","event_driven","hybrid","cqrs","serverless"}

def test_security_audit_has_security_driver():
    r=RequirementInput(project_name="Financial",description="Sensitive financial transaction platform",functional_requirements=["Process transactions"],non_functional_requirements=["Strict security","Auditability","High availability"])
    out=run_pipeline(r)
    assert "security" in out.requirement_profile.tags
    assert "auditability" in out.requirement_profile.tags


def test_acceptance_scenarios_are_requirement_dependent():
    a=run_pipeline(RequirementInput(project_name="College Attendance",description="Small college attendance application for 500 users. Low budget. Simple CRUD. Normal availability. No real-time processing."))
    b=run_pipeline(RequirementInput(project_name="National Food Delivery",description="National food delivery platform. 10 million users. High weekend traffic. Real-time driver tracking. Payment processing. 99.99% availability."))
    c=run_pipeline(RequirementInput(project_name="Financial Transactions",description="Financial transaction platform. Strict security. Auditability. High availability. Strong transaction integrity. Sensitive financial data."))
    assert a.requirement_profile.tags == ["cost_sensitive"]
    assert a.recommendation.pattern_key in {"modular_monolith","layered","clean_hexagonal"}
    assert b.recommendation.pattern_key in {"microservices","event_driven","hybrid","cqrs","serverless"}
    assert c.recommendation.pattern_key in {"microservices","event_driven","hybrid","cqrs"}
    assert len({a.recommendation.pattern_key,b.recommendation.pattern_key,c.recommendation.pattern_key}) >= 2
    assert a.recommendation.graph != b.recommendation.graph
    assert b.recommendation.graph != c.recommendation.graph


def test_traceability_and_agent_registry_are_real_outputs():
    req=RequirementInput(project_name="Trace Test",description="Secure real-time service for 1 million users with high availability and auditability.")
    out=run_pipeline(req)
    assert len(out.agent_registry) >= 20
    assert all(x["execution"]=="completed" for x in out.agent_registry)
    assert out.requirement_profile.requirement_records
    assert out.traceability
    assert all(x["architectural_driver"] and x["components"] for x in out.traceability)
    assert out.convergence["status"] in {"CONVERGED","MAX_ITERATIONS"}

def test_database_preference_is_not_hardcoded():
    mongo=run_pipeline(RequirementInput(
        project_name="Catalog Mongo",
        description="A scalable product catalog with search and product metadata.",
        functional_requirements=["Register users", "Search products", "Store product metadata"],
        non_functional_requirements=["High scalability", "Low latency"],
        technology_preferences=["MongoDB, React, FastAPI"]
    ))
    sql=run_pipeline(RequirementInput(
        project_name="Catalog SQL",
        description="A scalable product catalog with search and product metadata.",
        functional_requirements=["Register users", "Search products", "Store product metadata"],
        non_functional_requirements=["High scalability", "Low latency"],
        technology_preferences=["SQL, React, Spring Boot"]
    ))
    assert "MongoDB" in mongo.recommendation.data_stores
    assert "PostgreSQL" not in mongo.recommendation.data_stores
    assert "SQL Relational Database" in sql.recommendation.data_stores
    assert "PostgreSQL" not in sql.recommendation.data_stores
    assert mongo.recommendation.tech_stack["compute"] == "FastAPI"
    assert sql.recommendation.tech_stack["compute"] == "Spring Boot"
    assert mongo.recommendation.tech_stack["data"] != sql.recommendation.tech_stack["data"]
