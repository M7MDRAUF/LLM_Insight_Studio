# Backend Instructions

## Scope
Build the API using **FastAPI + Pydantic v2 + service-oriented architecture**.

## Backend Mission
The backend is the **source of truth** for:
- data ingestion,
- experiment orchestration,
- model inference routing,
- evaluation,
- report generation,
- artifact persistence,
- provenance.

## Required Layers
- `routers/`
- `schemas/`
- `services/`
- `repositories/`
- `core/`
- `workers/`

## Router Rules
- Routers validate input/output only.
- Routers do not contain business logic.
- Every route returns typed responses.
- Every route maps internal exceptions to documented API errors.

## Service Rules
Services own business logic.
Recommended services:
- DatasetService
- ExperimentService
- ModelService
- EvaluationService
- ResearchAgentService
- ArtifactService

## Repository Rules
Repositories own persistence and artifact access only.
They must not contain inference logic or business decisions.

## Error Handling Rules
Create explicit exception classes, e.g.:
- `DatasetValidationError`
- `UnsupportedTaskError`
- `ModelProviderError`
- `ExperimentExecutionError`
- `ArtifactWriteError`
- `ReferenceValidationError`

Return consistent error payloads:
```json
{
  "error": {
    "code": "MODEL_PROVIDER_ERROR",
    "message": "The selected model could not be reached.",
    "details": {}
  }
}
```

## API Contract Rules
- Every request/response must be modeled.
- IDs should be UUIDs where appropriate.
- Experiment statuses must be finite and documented.
- Use paginated responses for list endpoints.

## Inference Rules
- All model calls go through provider adapters.
- Record timing for every inference call.
- Capture provider/model/config metadata.
- Implement retries only for transient external failures.
- Never retry validation failures.

## Persistence Rules
Minimum persistence objects:
- dataset manifests,
- experiment records,
- metric bundles,
- artifact manifests,
- report metadata.

## Background Job Rules
- Keep route handlers fast.
- Use a kickoff endpoint and polling/status endpoint.
- Persist job status transitions.
- Store failures with root-cause detail.

## Logging Rules
Log with structured keys:
- request_id
- experiment_id
- dataset_id
- task_lane
- model_id
- duration_ms
- status

## Backend Testing Requirements
- unit tests for services,
- repository tests,
- API contract tests,
- integration tests for experiment lifecycle,
- agent/report pipeline integration tests.

## Forbidden Backend Anti-Patterns
- model calls inside routers,
- storing raw unbounded payloads without validation,
- ad-hoc dicts instead of schemas,
- mixing sync/async carelessly,
- broad except clauses that hide failures.
