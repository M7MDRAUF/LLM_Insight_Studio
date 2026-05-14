"""Hugging Face transformers provider (lazy, optional)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from apps.api.core.errors import ModelProviderError
from services.ml.providers.base import (
    ClassificationOutput,
    GenerationOutput,
    InferenceProvider,  # noqa: F401 - exported for type checkers
    QAOutput,
    SummarizationOutput,
)


@lru_cache(maxsize=16)
def _pipeline(task: str, model_id: str) -> Any:
    try:
        from transformers import pipeline  # pyright: ignore[reportMissingImports]
    except ImportError as exc:  # pragma: no cover
        raise ModelProviderError(
            "transformers is not installed. Install the 'ml' extra.",
            {"task": task, "model_id": model_id},
        ) from exc
    try:
        return pipeline(task=task, model=model_id)  # type: ignore[call-overload, unused-ignore]
    except Exception as exc:
        raise ModelProviderError(
            f"Failed to load pipeline for {task}/{model_id}: {exc}",
            {"task": task, "model_id": model_id},
        ) from exc


class TransformersProvider:
    """Real Hugging Face transformers-based provider."""

    name = "transformers"

    def __init__(self, hf_token: str | None = None) -> None:
        # Token is used transparently by HF libs via env; we keep the reference
        # for explicit error messages only.
        self.hf_token = hf_token

    def classify(
        self, texts: list[str], model_id: str, **kwargs: Any
    ) -> list[ClassificationOutput]:
        pipe = _pipeline("text-classification", model_id)
        raws = pipe(texts)
        if isinstance(raws, dict):  # single input case
            raws = [raws]
        return [
            ClassificationOutput(
                label=str(r.get("label", "")),
                score=float(r.get("score", 0.0)),
                raw=dict(r),
            )
            for r in raws
        ]

    def summarize(
        self, texts: list[str], model_id: str, **kwargs: Any
    ) -> list[SummarizationOutput]:
        pipe = _pipeline("summarization", model_id)
        raws = pipe(
            texts,
            max_length=int(kwargs.get("max_length", 160)),
            min_length=int(kwargs.get("min_length", 30)),
            truncation=True,
        )
        if isinstance(raws, dict):
            raws = [raws]
        return [
            SummarizationOutput(summary=str(r.get("summary_text", "")), raw=dict(r)) for r in raws
        ]

    def answer(
        self,
        questions: list[str],
        contexts: list[str],
        model_id: str,
        **kwargs: Any,
    ) -> list[QAOutput]:
        if len(questions) != len(contexts):
            raise ValueError("questions and contexts must be the same length")
        pipe = _pipeline("question-answering", model_id)
        inputs = [{"question": q, "context": c} for q, c in zip(questions, contexts, strict=True)]
        raws = pipe(inputs)
        if isinstance(raws, dict):
            raws = [raws]
        return [
            QAOutput(
                answer=str(r.get("answer", "")),
                score=float(r.get("score", 0.0)),
                start=r.get("start"),
                end=r.get("end"),
                raw=dict(r),
            )
            for r in raws
        ]

    def generate(self, prompts: list[str], model_id: str, **kwargs: Any) -> list[GenerationOutput]:
        pipe = _pipeline("text-generation", model_id)
        raws = pipe(
            prompts,
            max_new_tokens=int(kwargs.get("max_new_tokens", 128)),
            do_sample=bool(kwargs.get("do_sample", False)),
            temperature=float(kwargs.get("temperature", 0.2)),
        )
        if isinstance(raws, dict):
            raws = [[raws]]
        if raws and isinstance(raws[0], dict):
            raws = [[r] for r in raws]
        out: list[GenerationOutput] = []
        for group in raws:
            first: dict[str, Any] = group[0] if group else {}  # pyright: ignore[reportAssignmentType]
            text = str(first.get("generated_text", ""))
            out.append(GenerationOutput(text=text, raw=dict(first)))
        return out
