"""Test health check endpoint."""

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Test GET /health returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    assert data["data"]["status"] == "ok"
