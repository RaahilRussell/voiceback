from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_typed_payload() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert set(body.keys()) == {"status", "environment", "version"}
    assert body["version"] == "0.1.0"
