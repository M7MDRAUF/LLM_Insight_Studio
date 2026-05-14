# Data and ML Instructions

## Mission
Create a reproducible, Hugging Face-first ML and dataset layer that supports benchmark evaluation and demo inference with minimal surprises.

## Required Libraries
- `transformers`
- `datasets`
- `evaluate`
- `huggingface_hub`
- optional: `accelerate`
- optional: `sentence-transformers`

## Data Layer Responsibilities
- import Hugging Face datasets,
- import local files,
- normalize schemas,
- chunk long documents,
- preserve row identity,
- cache processed subsets,
- expose consistent structures to downstream services.

## ML Layer Responsibilities
- wrap task-specific model pipelines,
- standardize outputs,
- support batching,
- measure latency,
- capture config metadata,
- expose deterministic result formats.

## Canonical Task Wrappers
Implement wrappers with stable outputs:
- `run_classification(...)`
- `run_summarization(...)`
- `run_extractive_qa(...)`
- `run_instruct_analysis(...)`

## Model Wrapper Rules
- Validate model-task compatibility before execution.
- Enforce truncation/windowing strategy per task.
- Return normalized output objects.
- Include raw output in debug mode only.

## Dataset Wrapper Rules
- Dataset manifests must include source, split, text columns, label columns, and row counts.
- Uploaded files must be converted into canonical records.
- Long text must be chunked with stable references to original row ids.

## Evaluation Rules
### Classification
Compute:
- accuracy
- precision
- recall
- F1
- confusion matrix

### Summarization
Compute:
- ROUGE-1
- ROUGE-2
- ROUGE-L

### QA
Compute:
- EM
- F1
- evidence hit rate (custom)

## Reproducibility Rules
For every experiment persist:
- dataset id/source,
- sample strategy,
- row count,
- model id,
- provider,
- inference settings,
- metrics,
- timestamp.

## Caching Rules
- Cache normalized datasets by manifest hash.
- Cache expensive inference outputs if configuration matches exactly.
- Invalidate cache on model id or preprocessing changes.

## Anti-Patterns (Forbidden)
- changing schemas mid-pipeline,
- silently dropping rows,
- mixing benchmark and uploaded data without tagging provenance,
- returning task-specific weird shapes with no normalization.
