from app.diagram import uml_for, uml_svg_for, uml_plantuml


def test_domain_classes_connect_from_full_requirements_and_skip_nfr_as_class():
    requirements = [
        {"id": "FR1", "description": "Customers can browse products, add products to a shopping cart, and place orders."},
        {"id": "FR2", "description": "The system must process payments and update inventory when an order is placed."},
        {"id": "FR3", "description": "Customers can track orders and receive delivery notifications."},
        {"id": "NFR1", "description": "The platform must support 10000 concurrent users with 99.95% availability and low latency."},
    ]
    uml = uml_for({"uml_requirements": requirements, "components": [], "requirement_mappings": {}})
    names = {item["name"] for item in uml["class"]["classes"]}
    assert {"Order", "Product", "Payment", "Inventory"}.issubset(names)
    assert "Availability" not in names
    assert len(uml["class"]["relations"]) >= 3
    svg = uml_svg_for({"uml": uml})["class"]
    assert svg.count("<path") >= 3
    plantuml = uml_plantuml({"uml": uml})["class"]
    assert " -- " in plantuml
    assert " --> " not in plantuml
