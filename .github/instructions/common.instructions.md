# Common Repository Instructions

These instructions apply to **all AI-generated code** in this repository.

## Purpose
This repo builds **LLM Insight Studio**, a research-grade full-stack app for comparing multiple LLM/model families on NLP tasks using Hugging Face-first tooling.

## Non-Negotiable Architecture Rules
1. Frontend and backend must remain separated.
2. Browser code must never directly call Hugging Face model providers.
3. Backend must expose typed API routes.
4. Long-running jobs must be orchestrated via service/workers, never inside route handlers beyond kickoff/monitoring.
5. All outputs that influence research results must be persisted as artifacts.
6. Any report claim must be traceable to data, metrics, or references.

## Engineering Rules
- Prefer small, composable modules.
- Prefer explicit schemas over dynamic dict passing.
- Do not introduce new frameworks without a documented reason.
- Do not duplicate types across layers if a shared schema package exists.
- Every feature must include tests and error handling.
- Every new environment variable must be documented.

## Code Quality Rules
- Type everything.
- Keep pure logic in testable functions.
- Separate orchestration from I/O.
- Avoid “god services”.
- No business logic in UI components.
- No silent catch blocks.
- Use structured logging.

## Pull Request Requirements
A PR is incomplete if it lacks any of the following when applicable:
- implementation,
- tests,
- docs update,
- API schema update,
- error states,
- loading states,
- accessibility review,
- artifact/provenance handling.

## Definition of Done
A task is done only if:
1. the feature works,
2. tests pass,
3. docs match behavior,
4. no cross-layer violations exist,
5. logs and error messages are meaningful,
6. the feature supports reproducibility if it touches experiments or reports.
