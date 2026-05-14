"""Prometheus /metrics smoke test."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_metrics_exposes_prometheus_text(client: TestClient) -> None:
    r = client.get("/metrics")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    body = r.text
    assert "studio_datasets_total" in body
    assert 'studio_experiments_total{status="queued"}' in body
    assert "studio_jobs_in_flight" in body
