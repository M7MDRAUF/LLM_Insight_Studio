"""Agent /report end-to-end: enabled (default) vs disabled report flag."""

from __future__ import annotations

import io

from fastapi.testclient import TestClient


def _seed_dataset(client: TestClient) -> str:
    csv = "text,label\nfoo,1\nbar,0\n"
    resp = client.post(
        "/api/v1/datasets/import/upload",
        files={"file": ("t.csv", io.BytesIO(csv.encode()), "text/csv")},
        data={"text_columns": "text", "label_columns": "label"},
    )
    assert resp.status_code == 201, resp.text
    return str(resp.json()["id"])


def _create_experiment(client: TestClient, manifest_id: str, *, report_enabled: bool) -> str:
    payload = {
        "dataset_manifest_id": manifest_id,
        "task_lanes": ["classification"],
        "sampling": {"max_rows": 2},
        "report": {"enabled": report_enabled, "include_references": True},
    }
    create = client.post("/api/v1/experiments", json=payload)
    assert create.status_code == 202, create.text
    return str(create.json()["experiment_id"])


def test_report_e2e_enabled_produces_markdown(client: TestClient) -> None:
    manifest_id = _seed_dataset(client)
    exp_id = _create_experiment(client, manifest_id, report_enabled=True)
    assert client.get(f"/api/v1/experiments/{exp_id}/result").json()["status"] == "completed"

    r = client.post(
        "/api/v1/agent/report",
        json={"experiment_id": exp_id, "include_references": True},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["report_id"]
    assert body["reference_count"] >= 1


def test_report_e2e_disabled_is_rejected(client: TestClient) -> None:
    manifest_id = _seed_dataset(client)
    exp_id = _create_experiment(client, manifest_id, report_enabled=False)
    assert client.get(f"/api/v1/experiments/{exp_id}/result").json()["status"] == "completed"

    r = client.post(
        "/api/v1/agent/report",
        json={"experiment_id": exp_id, "include_references": True},
    )
    assert r.status_code == 500
    body = r.json()
    assert body["error"]["code"] == "EXPERIMENT_EXECUTION_ERROR"
    assert "disabled" in body["error"]["message"].lower()
