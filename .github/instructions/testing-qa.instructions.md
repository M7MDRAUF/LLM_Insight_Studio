# Testing and QA Instructions

## Mission
Prevent fragile demos, regression bugs, and research-invalid outputs.

## Required Testing Layers
1. Unit tests
2. Integration tests
3. API contract tests
4. E2E tests
5. Golden artifact tests for stable demo flows

## Unit Test Coverage Targets
- dataset normalization functions,
- schema mappers,
- model wrapper validators,
- metric calculators,
- report section builders,
- reference validators.

## Integration Test Targets
- import dataset -> create manifest,
- create experiment -> run pipelines -> persist artifacts,
- agent collects references -> writes markdown -> validation passes.

## API Contract Testing
- verify all route schemas,
- validate error responses,
- test invalid payloads,
- test unsupported models/tasks.

## E2E Scenarios
1. Upload CSV → map schema → run classification → view metrics.
2. Run summarization preset → open report.
3. Ask interactive question → see evidence panel.
4. Compare two/three models → view table.

## Golden Artifact Tests
Store small stable fixtures and compare:
- report outline,
- metrics json shape,
- chart data schema,
- evidence snippet structure.

## Manual QA Checklist
- Can the demo be run from a clean machine?
- Are model selection fallbacks explained?
- Are error messages understandable by a non-engineer?
- Are exported artifacts complete and readable?
- Is provenance present in final report?

## Bug Severity Guidance
- P0: demo blocked / corrupted results / invalid provenance
- P1: major feature broken / wrong metrics / broken report export
- P2: UI/UX regression / minor validation gaps
- P3: cosmetic issues
