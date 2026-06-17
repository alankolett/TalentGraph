from fastapi.testclient import TestClient

from api.main import create_app
from common.settings import Settings


def test_health_returns_200() -> None:
    app = create_app(Settings())
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
