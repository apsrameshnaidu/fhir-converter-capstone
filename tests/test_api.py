import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
SAMPLES = Path(__file__).resolve().parent.parent / "data" / "sample"


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_templates() -> None:
    response = client.get("/templates/ccda")
    assert response.status_code == 200
    assert "CCD" in response.json()["templates"]

    assert client.get("/templates/hl7v2").status_code == 422


def test_convert_ccda() -> None:
    xml = (SAMPLES / "ccda" / "CCD.ccda").read_text(encoding="utf-8")
    response = client.post("/convert/ccda", json={"template_name": "CCD", "data": xml})
    assert response.status_code == 200
    assert response.json()["resourceType"] == "Bundle"


def test_convert_ccda_unknown_template() -> None:
    response = client.post("/convert/ccda", json={"template_name": "Nope", "data": "<x/>"})
    assert response.status_code == 404


def test_convert_stu3() -> None:
    resource = json.loads((SAMPLES / "stu3" / "Condition.json").read_text(encoding="utf-8"))
    response = client.post(
        "/convert/stu3", json={"template_name": "Condition", "data": resource}
    )
    assert response.status_code == 200
    assert response.json()["resourceType"] == "Condition"


def test_convert_stu3_invalid_json() -> None:
    response = client.post("/convert/stu3", json={"template_name": "Condition", "data": "{bad"})
    assert response.status_code == 422
