# AI Agent Instructions

## Mission
Implement a **safe, reference-grounded research agent** that helps with dataset discovery, reference collection, experiment planning, and markdown report writing.

## Recommended Framework
Use **Hugging Face smolagents**.

## Default Agent Type
Use `ToolCallingAgent` by default.
Reason:
- safer,
- structured,
- easier to validate,
- lower bug/conflict rate for AI-generated code.

Only use `CodeAgent` in a sandboxed environment for advanced optional workflows.

## Agent Responsibilities
1. search benchmark datasets,
2. inspect dataset metadata,
3. search/select models,
4. fetch official docs / model cards,
5. draft experiment plan,
6. draft report sections,
7. compile references,
8. validate citations and provenance.

## Mandatory Tooling Pattern
Each tool must have:
- a clear docstring,
- input schema,
- output schema,
- failure contract,
- logging.

## Minimum Tool Set
- `search_hf_datasets`
- `get_dataset_info`
- `search_hf_models`
- `get_model_card`
- `fetch_official_doc`
- `write_markdown_report`
- `validate_references`
- `save_experiment_plan`

## Grounding Rules
- The agent must never invent references.
- The agent must never cite a dataset it did not inspect.
- The agent must never claim benchmark results unless those results exist in experiment artifacts.
- When uncertain, the agent must mark uncertainty explicitly.

## Report Rules
Every report must contain:
- objective,
- selected datasets,
- selected models,
- methodology,
- metrics,
- findings,
- limitations,
- references,
- provenance appendix.

## Tool Execution Rules
- Use allowlisted tools only.
- No shell tool.
- No filesystem writes outside artifact/report directories.
- No network calls except documented data/reference tools.

## Agent Memory Rules
- Persist only task-relevant state.
- Do not leak secrets.
- Do not store large raw datasets in memory when not needed.
- Prefer IDs and paths over whole payload duplication.

## Validation Pipeline
Before a report is finalized:
1. validate dataset references,
2. validate model references,
3. validate that findings map to metrics or evidence,
4. validate presence of limitations,
5. validate provenance footer.

## Failure Handling
If a tool fails:
- return structured failure,
- do not continue pretending success,
- request fallback action or mark incomplete section.

## Forbidden Anti-Patterns
- hallucinated citations,
- Markdown reports with dead links and no validation,
- direct arbitrary code execution,
- mixing unverified claims with verified claims without labels.
