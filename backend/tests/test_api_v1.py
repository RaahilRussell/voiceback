from fastapi.testclient import TestClient

from app.api.v1 import API_VERSION
from app.main import app
from app.schemas.health import HealthResponse

client = TestClient(app)


def test_v1_health_returns_typed_payload() -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    # Round-trips through the declared schema, proving the payload is typed.
    model = HealthResponse(**response.json())
    assert model.status == "ok"
    assert model.version == API_VERSION


def test_v1_health_rejects_unknown_method() -> None:
    response = client.post("/v1/health")
    assert response.status_code == 405
