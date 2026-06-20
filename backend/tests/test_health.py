"""Smoke tests for the FastAPI app (no external services required)."""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_liveness() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "env" in body
