"""End-to-end experiment flow via the HTTP surface."""

from __future__ import annotations

import io

from fastapi.testclient import TestClient


def _import_upload(client: TestClient) -> str:
    csv = "text,label\nI love this,1\nI hate this,0\nGreat movie,1\nTerrible film,0\n"
    resp = client.post(
        "/api/v1/datasets/import/upload",
        files={"file": ("tiny.csv", io.BytesIO(csv.encode()), "text/csv")},
        data={"text_columns": "text", "label_columns": "label"},
    )
    assert resp.status_code == 201, resp.text
    return str(resp.json()["id"])


def test_upload_preview_and_experiment(client: TestClient) -> None:
    manifest_id = _import_upload(client)

    preview = client.get(f"/api/v1/datasets/{manifest_id}/preview").json()
    assert preview["total_rows"] == 4
    assert preview["columns"] == ["text", "label"]

    create = client.post(
        "/api/v1/experiments",
        json={
            "dataset_manifest_id": manifest_id,
            "task_lanes": ["classification"],
            "sampling": {"max_rows": 4, "strategy": "head", "seed": 1},
        },
    )
    assert create.status_code == 202, create.text
    exp_id = create.json()["experiment_id"]

    # BackgroundTasks in TestClient run after response — poll the result.
    result = client.get(f"/api/v1/experiments/{exp_id}/result").json()
    assert result["status"] == "completed", result
    assert result["metrics"]["classification"]["model_id"]


def test_unknown_experiment_returns_typed_error(client: TestClient) -> None:
    r = client.get("/api/v1/experiments/00000000-0000-0000-0000-000000000000/result")
    assert r.status_code == 500
    body = r.json()
    assert body["error"]["code"] == "EXPERIMENT_EXECUTION_ERROR"
