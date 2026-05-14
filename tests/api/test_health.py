"""Health endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_live(client: TestClient) -> None:
    r = client.get("/api/v1/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready(client: TestClient) -> None:
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "ok"
    assert payload["inference_provider"] in {"mock", "transformers"}
