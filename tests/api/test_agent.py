"""Agent endpoint tests."""

from __future__ import annotations

import io

from fastapi.testclient import TestClient


def test_agent_plan(client: TestClient) -> None:
    r = client.post(
        "/api/v1/agent/plan",
        json={"topic": "sentiment models", "task_lanes": ["classification"]},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "Research Plan" in data["plan_markdown"]
    assert len(data["references"]) >= 1


def test_agent_report_requires_experiment(client: TestClient) -> None:
    csv = "text,label\nI love this,1\nI hate this,0\n"
    manifest_id = client.post(
        "/api/v1/datasets/import/upload",
        files={"file": ("t.csv", io.BytesIO(csv.encode()), "text/csv")},
        data={"text_columns": "text", "label_columns": "label"},
    ).json()["id"]
    exp_id = client.post(
        "/api/v1/experiments",
        json={
            "dataset_manifest_id": manifest_id,
            "task_lanes": ["classification"],
            "sampling": {"max_rows": 2, "strategy": "head", "seed": 1},
        },
    ).json()["experiment_id"]
    # result endpoint runs background task to completion synchronously under TestClient
    client.get(f"/api/v1/experiments/{exp_id}/result")

    r = client.post(
        "/api/v1/agent/report",
        json={"experiment_id": exp_id, "include_references": True},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["reference_count"] >= 1
    assert body["report_id"]
