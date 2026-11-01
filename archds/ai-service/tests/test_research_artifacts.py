from app.models import RequirementInput
from app.workflow.orchestrator import run_pipeline
from app.report import build_pdf


def sample():
    return RequirementInput(
        project_name="Hospital Research",
        description="Secure hospital platform for patients and doctors.",
        functional_requirements=["Patient registration", "Book appointments", "Maintain medical records", "Generate reports"],
        non_functional_requirements=["High availability", "Security", "Low latency", "Scalability", "Auditability"],
        constraints=["Protect patient data", "Audit access"], expected_users="50000", budget="Medium",
        num_alternatives=3, max_iterations=1,
    )


def test_runtime_framework_is_distinct_and_requirement_justified():
    out = run_pipeline(sample())
    fw = out.recommendation.system_design_framework
    labels = [x["label"] for x in fw["nodes"]]
    assert "Load Balancer" in labels
    assert "Distributed Cache" in labels
    assert "Business Capabilities (" in " -> ".join(fw["request_path"])
    assert out.research_framework["stages"][2]["label"] == "Candidate Competition"


def test_uml_is_generated_from_requirements_without_repeated_generic_operations():
    out = run_pipeline(sample())
    uml = out.recommendation.uml
    assert uml["use_case"]["use_cases"]
    classes = uml["class"]["classes"]
    assert classes
    operation_sets = {tuple(x["operations"]) for x in classes}
    assert len(operation_sets) > 1 or len(classes) == 1
    assert "System Boundary" in out.recommendation.uml_plantuml["use_case"]


def test_pdf_is_real_pdf():
    out = run_pipeline(sample())
    pdf = build_pdf(out.model_dump())
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 10000
