# DevOps and Security Instructions

## Mission
Keep the project easy to run locally in VS Code while maintaining clean secrets handling, reproducibility, and reliable startup.

## Local Development Expectations
- Frontend and backend should start independently.
- Environment variables must be documented.
- Provide seed/demo data or benchmark presets.
- Startup errors must clearly explain missing dependencies/tokens.

## Environment Variables (minimum)
- `HF_TOKEN` (optional or required depending on selected models)
- `API_HOST`
- `API_PORT`
- `WEB_ORIGIN`
- `ARTIFACTS_DIR`
- `DATABASE_URL`
- `DEFAULT_CLASSIFICATION_MODEL`
- `DEFAULT_SUMMARIZATION_MODEL`
- `DEFAULT_QA_MODEL`
- `DEFAULT_INSTRUCT_MODEL`

## Secret Handling Rules
- Never commit `.env`.
- Never expose tokens to the browser.
- Never print full tokens in logs.

## Runtime Profiles
### Development
- verbose logging
- local SQLite
- lightweight models
- hot reload

### Demo
- stable seeded data
- deterministic parameters
- optional precomputed artifacts

## Artifact Storage Rules
- store reports under `artifacts/reports/`
- store charts under `artifacts/charts/`
- store experiment JSON under `artifacts/experiments/`
- keep manifests and indexes discoverable

## Observability Rules
- request IDs
- experiment IDs
- model IDs in logs
- structured JSON logs preferred

## Security Rules
- validate uploads strictly,
- sanitize filenames,
- cap request sizes,
- allowlist agent tools,
- no arbitrary code execution in default mode.

## Deployment Readiness Checklist
- environment documented,
- models configurable,
- CORS configured,
- health endpoints available,
- startup checks validate directories and model config.
