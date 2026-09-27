from fastapi.testclient import TestClient

import config
from main import app


def test_api_requires_token_when_configured(monkeypatch):
    monkeypatch.setattr(config, "API_TOKEN", "secret-123")
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200  # health check stays public
        assert client.get("/api/stats").status_code == 401
        assert client.get("/api/stats", headers={"Authorization": "Bearer wrong"}).status_code == 401
        assert client.get("/api/stats", headers={"Authorization": "Bearer secret-123"}).status_code == 200


def test_question_length_is_limited():
    with TestClient(app) as client:
        response = client.post("/api/runs", json={"input": "x" * 501, "version": "v1"})
        assert response.status_code == 422
