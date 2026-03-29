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


class TestChatEndpoint:
    def test_chat_returns_202(self):
        app = create_app()
        client = TestClient(app)
        response = client.post("/chat", json={"session_id": "test-1", "message": "Hello"})
        assert response.status_code == 202

    def test_chat_rejects_empty_message(self):
        app = create_app()
        client = TestClient(app)
        response = client.post("/chat", json={"session_id": "test-1", "message": ""})
        assert response.status_code == 422

    def test_chat_rejects_missing_session_id(self):
        app = create_app()
        client = TestClient(app)
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 422

    def test_chat_appends_message_to_session(self):
        app = create_app()
        client = TestClient(app)
        client.post("/chat", json={"session_id": "test-1", "message": "Hello"})
        session = app.state.sessions.get_or_create("test-1")
        assert len(session) >= 1
        assert session[0].content == "Hello"
