# LLM Insight Studio — Operations Runbook

A short, dependable handbook for running the studio in dev and small-scale
deployments. The system targets a single VM / desktop with one API process.

## Architecture at a glance

```
Browser (Next.js)  ──HTTP──▶  FastAPI app
                                ├─ Routers (datasets / experiments / agent / compare / reports / artifacts / metrics)
                                ├─ Services (dataset, experiment, evaluation, model, artifact, agent)
                                ├─ Repositories (SQLModel, SQLite)
                                └─ JobRunner (anyio.to_thread + threading.Event cancel flag)
                                        ▲
                                        └─ run_experiment(experiment_id, cancel_event, settings)
```

Everything lives in process. Experiments persist in `artifacts/studio.db`;
artifacts (JSON / Markdown) live under `artifacts/`.

## Environment variables

| Variable               | Default                                       | Purpose                                                  |
| ---------------------- | --------------------------------------------- | -------------------------------------------------------- |
| `INFERENCE_PROVIDER`   | `mock`                                        | `mock` for offline / CI; `transformers` for real models. |
| `DATABASE_URL`         | `sqlite:///<repo>/artifacts/studio.db`        | Override for ephemeral DBs (tests use tmp paths).        |
| `ARTIFACTS_DIR`        | `<repo>/artifacts`                            | Where reports/experiments JSON & markdown are written.   |
| `ALLOWED_ORIGINS`      | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated CORS allowlist.                          |
| `MAX_UPLOAD_BYTES`     | `52428800` (50 MiB)                           | Hard cap on dataset upload size.                         |
| `EXPERIMENT_TIMEOUT_S` | `600`                                         | Watchdog: stale-heartbeat triggers FAILED.               |
| `LOG_LEVEL`            | `INFO`                                        | App log level.                                           |
| `HF_TOKEN`             | _(unset)_                                     | Optional Hugging Face access token.                      |

## Running locally

```pwsh
# 1. Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
uvicorn apps.api.main:app --reload

# 2. Frontend
cd apps\web
npm install
npm run dev
```

Backend listens on `:8000`; frontend on `:3000`.

## Health & observability

| Endpoint              | Purpose                                                                        |
| --------------------- | ------------------------------------------------------------------------------ |
| `GET /api/v1/health`  | Liveness probe (returns `{"status":"ok"}`).                                    |
| `GET /metrics`        | Prometheus-style text exposition (datasets, experiments by status, in-flight). |
| `X-Request-ID` header | Round-tripped on every response; correlates request logs.                      |

Every request logs `method=… path=… status=… duration_ms=… request_id=…`.

## Operational concerns

### Job runner

- Lives in `services/jobs/runner.py`.
- One global `JobRunner` per process; cleaned up in FastAPI lifespan shutdown.
- Cancellation is **co-operative**: the worker polls `cancel_event.is_set()`
  between task lanes. A long-running single lane can therefore take up to a
  full lane to react.

### Heartbeat watchdog

- `ExperimentService.get_status` checks `last_heartbeat` against
  `EXPERIMENT_TIMEOUT_S`. If a `RUNNING` experiment has had no heartbeat in
  longer than the timeout it is auto-failed with `watchdog: heartbeat
timeout`.
- Workers refresh the heartbeat between lanes via
  `ExperimentRepository.touch_heartbeat`.

### Uploads

- Streamed in 1 MiB chunks; aborted with `DATASET_VALIDATION_ERROR` once the
  configured size cap is exceeded.
- Content-Type must be in `services/data/upload_loader.ALLOWED_CONTENT_TYPES`
  when the client supplies one.

### Artifact persistence

- Writes are atomic: a sibling `tempfile.mkstemp` file is fsynced and
  `os.replace`d into place — partial files cannot survive a crash.

### Records cache

- `DatasetService` caches up to 8 manifests' canonical records (LRU). On a
  cold cache the service re-normalizes from `preview_json` (max 20 rows) so
  experiments still run, but the returned record set will be smaller. To
  guarantee full fidelity after a restart, re-import the dataset.

## Common operations

### Run the test suite

```pwsh
python -m pytest -q
python -m pytest --cov=apps --cov=services --cov-report=term-missing
```

### Static analysis & security

```pwsh
ruff check .
ruff format --check .
mypy .
bandit -r apps services
pip-audit
vulture apps services
```

### Reset state

Delete `artifacts/` and re-create:

```pwsh
Remove-Item -Recurse -Force artifacts
mkdir artifacts
```

The next API start re-creates the schema and subfolders.

### Cancel a stuck experiment

```pwsh
curl -X POST http://localhost:8000/api/v1/experiments/<id>/cancel
```

## Failure modes

| Symptom                                                    | Likely cause                                   | Remedy                                                         |
| ---------------------------------------------------------- | ---------------------------------------------- | -------------------------------------------------------------- |
| `EXPERIMENT_EXECUTION_ERROR: Unknown experiment`           | Stale UUID after `artifacts/` reset.           | Re-create the experiment.                                      |
| Status stays `running`, then flips to `failed` w/ watchdog | Worker crashed before completing.              | Check API logs for the exception trace.                        |
| `DATASET_VALIDATION_ERROR: Upload exceeds…`                | Upload over `MAX_UPLOAD_BYTES`.                | Slim the upload or raise the cap.                              |
| Empty preview / record set                                 | Ingest produced no records after normalization | Verify `text_columns` are correct.                             |
| 502 / `MODEL_PROVIDER_ERROR`                               | Real model provider unavailable.               | Re-check `INFERENCE_PROVIDER`/`HF_TOKEN`; fall back to `mock`. |
