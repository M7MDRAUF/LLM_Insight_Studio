"""Allowlisted agent tools.

Each tool is a plain callable with a documented signature so it can be wired
into smolagents ``ToolCallingAgent`` or invoked directly by backend code.
Tools never perform shell/filesystem writes outside artifact directories.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from apps.api.schemas.agent import AgentReferenceItem
from apps.api.schemas.datasets import TaskLane
from services.agent.references import (
    DEFAULT_REFERENCES,
    curate_references,
    validate_references,
)
from services.data.presets import DATASET_PRESETS


@dataclass(frozen=True)
class AgentTool:
    name: str
    description: str
    fn: Callable[..., Any]


def _search_hf_datasets(
    query: str, task: str | None = None, limit: int = 5
) -> list[dict[str, str]]:
    """Return curated dataset presets matching ``query`` and optional ``task``."""
    query_l = (query or "").lower()
    task_l = (task or "").lower()
    rows: list[dict[str, str]] = []
    for key, preset in DATASET_PRESETS.items():
        haystack = f"{key} {preset.dataset_id} {preset.description}".lower()
        if query_l and query_l not in haystack:
            continue
        if task_l and preset.task.value != task_l:
            continue
        rows.append(
            {
                "key": key,
                "dataset_id": preset.dataset_id,
                "task": preset.task.value,
                "default_split": preset.default_split,
                "description": preset.description,
            }
        )
        if len(rows) >= limit:
            break
    return rows


def _get_dataset_info(dataset_id: str) -> dict[str, Any]:
    for preset in DATASET_PRESETS.values():
        if preset.dataset_id == dataset_id:
            return {
                "dataset_id": preset.dataset_id,
                "task": preset.task.value,
                "default_split": preset.default_split,
                "text_column": preset.text_column,
                "label_column": preset.label_column,
                "description": preset.description,
            }
    return {
        "dataset_id": dataset_id,
        "status": "unknown-dataset",
        "note": "Not in curated preset list.",
    }


def _search_hf_models(query: str, task: str | None = None, limit: int = 5) -> list[dict[str, str]]:
    catalogue = [
        {"model_id": "distilbert-base-uncased-finetuned-sst-2-english", "task": "classification"},
        {"model_id": "cardiffnlp/twitter-roberta-base-sentiment-latest", "task": "classification"},
        {"model_id": "google/flan-t5-base", "task": "summarization"},
        {"model_id": "google-t5/t5-small", "task": "summarization"},
        {"model_id": "deepset/roberta-base-squad2", "task": "qa"},
        {"model_id": "distilbert-base-cased-distilled-squad", "task": "qa"},
        {"model_id": "Qwen/Qwen2.5-7B-Instruct", "task": "instruct"},
        {"model_id": "mistralai/Mistral-7B-Instruct-v0.3", "task": "instruct"},
    ]
    query_l = (query or "").lower()
    task_l = (task or "").lower()
    rows: list[dict[str, str]] = []
    for row in catalogue:
        if query_l and query_l not in row["model_id"].lower():
            continue
        if task_l and row["task"] != task_l:
            continue
        rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def _get_model_card(model_id: str) -> dict[str, str]:
    return {
        "model_id": model_id,
        "card_url": f"https://huggingface.co/{model_id}",
        "note": "Model card URL only. The agent must not fabricate card content.",
    }


def _fetch_official_doc(url: str) -> dict[str, str]:
    known = {str(r.url).rstrip("/") for r in DEFAULT_REFERENCES}
    status = "known" if url.rstrip("/") in known else "external"
    return {"url": url, "status": status}


def _collect_references(
    task_lanes: list[str],
    max_items: int = 12,
    hints: list[str] | None = None,
) -> list[dict[str, Any]]:
    lanes = [TaskLane(l) for l in task_lanes if l in {t.value for t in TaskLane}]
    refs = curate_references(lanes, max_items=max_items, extra_hints=hints)
    validate_references(refs)
    return [r.model_dump(mode="json") for r in refs]


def _validate_references_tool(refs: list[dict[str, Any]]) -> dict[str, Any]:
    items = [AgentReferenceItem.model_validate(r) for r in refs]
    validate_references(items)
    return {"status": "ok", "count": len(items)}


AGENT_TOOLS: list[AgentTool] = [
    AgentTool(
        name="search_hf_datasets",
        description="Search curated Hugging Face dataset presets by keyword and task.",
        fn=_search_hf_datasets,
    ),
    AgentTool(
        name="get_dataset_info",
        description="Return metadata for a known Hugging Face dataset.",
        fn=_get_dataset_info,
    ),
    AgentTool(
        name="search_hf_models",
        description="Search a small curated list of task-compatible models.",
        fn=_search_hf_models,
    ),
    AgentTool(
        name="get_model_card",
        description="Return the canonical model card URL for a model id.",
        fn=_get_model_card,
    ),
    AgentTool(
        name="fetch_official_doc",
        description="Confirm whether a documentation URL is in the approved catalogue.",
        fn=_fetch_official_doc,
    ),
    AgentTool(
        name="collect_references",
        description="Curate a validated reference list for the given task lanes.",
        fn=_collect_references,
    ),
    AgentTool(
        name="validate_references",
        description="Validate a reference list for schema and duplicates.",
        fn=_validate_references_tool,
    ),
]
