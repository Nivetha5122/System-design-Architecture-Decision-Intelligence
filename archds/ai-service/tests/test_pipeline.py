from app.models import RequirementInput,QualityWeights
from app.workflow.orchestrator import run_pipeline

def test_pipeline_arbitrary_domain():
 req=RequirementInput(project_name="FoodFlow",description="Real-time food delivery",functional_requirements=["Customers place orders","Drivers receive live delivery updates"],non_functional_requirements=["Support high traffic","Strong security","High availability"],quality_weights=QualityWeights(performance=15,scalability=20,security=20,reliability=15,maintainability=10,cost=5,complexity=5,extensibility=10))
 out=run_pipeline(req);assert len(out.candidates)>=2;assert out.recommendation;assert out.optimization["algorithm"].startswith("Discrete non-dominated Pareto");assert len(out.agent_trace)>=9;assert all(0<=c.scores.weighted_total<=100 for c in out.candidates)

def test_weights_must_sum_100():
 try: QualityWeights(performance=1,scalability=1,security=1,reliability=1,maintainability=1,cost=1,complexity=1,extensibility=1);assert False
 except Exception: assert True

def test_final_recommendation_contains_renderable_diagram():
    req=RequirementInput(
        project_name="Hospital Alerts",
        description="A hospital platform receives patient telemetry, detects abnormal readings, alerts clinicians in real time and must remain available during failures.",
        quality_weights=QualityWeights()
    )
    out=run_pipeline(req)
    assert out.recommendation.graph["nodes"]
    assert out.recommendation.graph["edges"]
    assert "@startuml" in out.recommendation.plantuml_source
    assert "@enduml" in out.recommendation.plantuml_source


def test_natural_language_only_input_is_structured():
    req=RequirementInput(
        project_name="Exam Platform",
        description="Build an online examination platform where students register, take timed exams, submit answers and receive results. It should support high traffic, strong security and reliable operation."
    )
    out=run_pipeline(req)
    assert out.requirement_profile.functional_requirements
    assert out.requirement_profile.non_functional_requirements
    assert out.recommendation.components
