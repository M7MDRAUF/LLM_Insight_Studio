"""Experiment lifecycle: cancel semantics + watchdog timeout."""

from __future__ import annotations

import io
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.core.db import session_scope
from apps.api.repositories.experiments import ExperimentRepository
from apps.api.repositories.models import ExperimentRow
from apps.api.schemas.experiments import ExperimentStatus


def _seed_dataset(client: TestClient) -> str:
    csv = "text,label\nfoo,1\nbar,0\n"
    resp = client.post(
        "/api/v1/datasets/import/upload",
        files={"file": ("t.csv", io.BytesIO(csv.encode()), "text/csv")},
        data={"text_columns": "text", "label_columns": "label"},
    )
    assert resp.status_code == 201, resp.text
    return str(resp.json()["id"])


def test_cancel_unknown_experiment_returns_typed_error(client: TestClient) -> None:
    r = client.post("/api/v1/experiments/00000000-0000-0000-0000-000000000000/cancel")
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "EXPERIMENT_EXECUTION_ERROR"


def test_cancel_after_completion_is_noop(client: TestClient) -> None:
    manifest_id = _seed_dataset(client)
    create = client.post(
        "/api/v1/experiments",
        json={
            "dataset_manifest_id": manifest_id,
            "task_lanes": ["classification"],
            "sampling": {"max_rows": 2},
        },
    )
    exp_id = create.json()["experiment_id"]
    # Drive the run to completion.
    result = client.get(f"/api/v1/experiments/{exp_id}/result").json()
    assert result["status"] == "completed"

    # Cancel after completion must be a no-op and preserve the terminal status.
    after = client.post(f"/api/v1/experiments/{exp_id}/cancel")
    assert after.status_code == 200
    assert after.json()["status"] == "completed"


def test_watchdog_marks_stale_running_experiment_as_failed(client: TestClient) -> None:
    """A RUNNING row with a stale heartbeat must be flipped to FAILED on /status."""
    from uuid import UUID, uuid4

    # Seed a real dataset manifest so the FK constraint is satisfied.
    manifest_id = UUID(_seed_dataset(client))

    exp_id = uuid4()
    stale_heartbeat = datetime.now(tz=UTC) - timedelta(hours=2)
    with session_scope() as session:
        repo = ExperimentRepository(session)
        repo.create(
            ExperimentRow(
                id=exp_id,
                dataset_manifest_id=manifest_id,
                task_lanes_json=["classification"],
                models_json={},
                params_json={"sampling": {}, "generation": {}, "report": {}},
                status=ExperimentStatus.RUNNING.value,
                progress=0.5,
                message="running",
                last_heartbeat=stale_heartbeat,
            )
        )

    resp = client.get(f"/api/v1/experiments/{exp_id}/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "failed"
    assert "watchdog" in (body["message"] or "").lower()
