"""Tests for FastAPI endpoints."""

from fastapi.testclient import TestClient

from stock_adviser.api.app import create_app


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
