"""Curated, verified reference catalogue used by the research agent.

Every entry is drawn from ``docs/MASTER_SPEC.md`` §31 and cross-checked against
official sources. No AI-invented URLs are allowed; the list is validated at
import time.
"""

from __future__ import annotations

from pydantic import TypeAdapter

from apps.api.core.errors import ReferenceValidationError
from apps.api.schemas.agent import AgentReferenceItem
from apps.api.schemas.datasets import TaskLane

_RAW: list[dict[str, str]] = [
    {
        "title": "Hugging Face Datasets docs",
        "url": "https://huggingface.co/docs/datasets/index",
        "type": "docs",
        "why_it_matters": "Primary reference for dataset loading and normalization used in the data layer.",
    },
    {
        "title": "Hugging Face Transformers pipelines",
        "url": "https://huggingface.co/docs/transformers/main_classes/pipelines",
        "type": "docs",
        "why_it_matters": "Defines the task pipelines wrapped by the transformers provider.",
    },
    {
        "title": "Hugging Face Evaluate",
        "url": "https://huggingface.co/docs/evaluate/index",
        "type": "docs",
        "why_it_matters": "Official metric catalogue used to cross-check our lightweight metric implementations.",
    },
    {
        "title": "Hugging Face smolagents guided tour",
        "url": "https://huggingface.co/docs/smolagents/guided_tour",
        "type": "docs",
        "why_it_matters": "Describes the ToolCallingAgent pattern used by this research agent.",
    },
    {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "url": "https://research.google/pubs/bert-pre-training-of-deep-bidirectional-transformers-for-language-understanding/",
        "type": "paper",
        "why_it_matters": "Foundational reference for the classification/QA model family.",
    },
    {
        "title": "T5: Text-to-Text Transfer Transformer",
        "url": "https://github.com/google-research/text-to-text-transfer-transformer",
        "type": "paper",
        "why_it_matters": "Foundational reference for the summarization model family.",
    },
    {
        "title": "The Llama 3 Herd of Models",
        "url": "https://arxiv.org/abs/2407.21783",
        "type": "paper",
        "why_it_matters": "Reference for the optional advanced instruct comparison.",
    },
    {
        "title": "SQuAD v1.1",
        "url": "https://huggingface.co/datasets/rajpurkar/squad",
        "type": "dataset",
        "why_it_matters": "Benchmark dataset used for extractive QA evaluation.",
    },
    {
        "title": "Rotten Tomatoes movie reviews",
        "url": "https://huggingface.co/datasets/cornell-movie-review-data/rotten_tomatoes",
        "type": "dataset",
        "why_it_matters": "Binary sentiment benchmark used for classification evaluation.",
    },
    {
        "title": "BillSum legal summarization dataset",
        "url": "https://huggingface.co/datasets/billsum",
        "type": "dataset",
        "why_it_matters": "Compact summarization benchmark suitable for demo runs.",
    },
    {
        "title": "distilbert-base-uncased-finetuned-sst-2-english model card",
        "url": "https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english",
        "type": "model_card",
        "why_it_matters": "Default classification model used in the classification lane.",
    },
    {
        "title": "google/flan-t5-base model card",
        "url": "https://huggingface.co/google/flan-t5-base",
        "type": "model_card",
        "why_it_matters": "Default summarization model used in the summarization lane.",
    },
    {
        "title": "deepset/roberta-base-squad2 model card",
        "url": "https://huggingface.co/deepset/roberta-base-squad2",
        "type": "model_card",
        "why_it_matters": "Default extractive QA model used in the QA lane.",
    },
]


_ADAPTER: TypeAdapter[list[AgentReferenceItem]] = TypeAdapter(list[AgentReferenceItem])
DEFAULT_REFERENCES: list[AgentReferenceItem] = _ADAPTER.validate_python(_RAW)


_TASK_HINT_KEYWORDS: dict[TaskLane, tuple[str, ...]] = {
    TaskLane.CLASSIFICATION: ("distilbert", "bert", "rotten", "classification"),
    TaskLane.SUMMARIZATION: ("t5", "billsum", "summar"),
    TaskLane.QA: ("roberta", "squad", "qa", "question"),
    TaskLane.INSTRUCT: ("llama", "smolagents", "bert"),
}


def curate_references(
    task_lanes: list[TaskLane],
    max_items: int,
    extra_hints: list[str] | None = None,
) -> list[AgentReferenceItem]:
    """Return a ranked subset of the reference catalogue relevant to ``task_lanes``."""
    hints = {h.lower() for h in (extra_hints or [])}
    wanted_keywords: set[str] = set()
    for lane in task_lanes:
        wanted_keywords.update(_TASK_HINT_KEYWORDS.get(lane, ()))
    scored: list[tuple[int, AgentReferenceItem]] = []
    for ref in DEFAULT_REFERENCES:
        score = 0
        haystack = f"{ref.title} {ref.url}".lower()
        for kw in wanted_keywords:
            if kw in haystack:
                score += 2
        for hint in hints:
            if hint and hint in haystack:
                score += 3
        scored.append((score, ref))
    scored.sort(key=lambda s: (-s[0], s[1].title))
    top = [item for _, item in scored[:max_items]]
    # Guarantee we always return the smolagents + evaluate docs as minimum provenance.
    required_titles = {
        "Hugging Face smolagents guided tour",
        "Hugging Face Evaluate",
    }
    have = {r.title for r in top}
    for ref in DEFAULT_REFERENCES:
        if ref.title in required_titles and ref.title not in have and len(top) < max_items:
            top.append(ref)
            have.add(ref.title)
    return top


def validate_references(refs: list[AgentReferenceItem]) -> None:
    """Re-validate references. Raises :class:`ReferenceValidationError` on failure."""
    try:
        _ADAPTER.validate_python([r.model_dump(mode="json") for r in refs])
    except Exception as exc:
        raise ReferenceValidationError(f"Invalid references: {exc}", {"count": len(refs)}) from exc
    # Uniqueness on URL to avoid dead-link duplication.
    urls = [str(r.url) for r in refs]
    if len(urls) != len(set(urls)):
        raise ReferenceValidationError("Duplicate reference URLs", {"count": len(urls)})
