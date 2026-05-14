"""Task-level model service: validates, batches, and times inference calls."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from apps.api.core.errors import ModelProviderError, UnsupportedTaskError
from apps.api.core.logging import get_logger
from apps.api.schemas.datasets import TaskLane
from services.ml.providers.base import (
    ClassificationOutput,
    GenerationOutput,
    InferenceProvider,
    QAOutput,
    SummarizationOutput,
)


@dataclass
class TimedResult:
    """Wraps a pipeline output with timing information."""

    latency_ms: float
    outputs: list[Any]
    model_id: str
    task: TaskLane


class ModelService:
    """Orchestrates provider calls per task lane with timing + validation."""

    def __init__(self, provider: InferenceProvider) -> None:
        self.provider = provider
        self._log = get_logger(__name__, provider=provider.name)

    # ---------------------- task wrappers ---------------------- #

    def run_classification(self, texts: list[str], model_id: str, **kwargs: Any) -> TimedResult:
        self._require_texts(texts)
        outputs = self._timed(
            lambda: self.provider.classify(texts, model_id, **kwargs),
            model_id=model_id,
            task=TaskLane.CLASSIFICATION,
        )
        return outputs

    def run_summarization(self, texts: list[str], model_id: str, **kwargs: Any) -> TimedResult:
        self._require_texts(texts)
        return self._timed(
            lambda: self.provider.summarize(texts, model_id, **kwargs),
            model_id=model_id,
            task=TaskLane.SUMMARIZATION,
        )

    def run_extractive_qa(
        self,
        questions: list[str],
        contexts: list[str],
        model_id: str,
        **kwargs: Any,
    ) -> TimedResult:
        if not questions or len(questions) != len(contexts):
            raise ModelProviderError(
                "questions and contexts must be non-empty and the same length",
                {"q": len(questions), "c": len(contexts)},
            )
        return self._timed(
            lambda: self.provider.answer(questions, contexts, model_id, **kwargs),
            model_id=model_id,
            task=TaskLane.QA,
        )

    def run_instruct(self, prompts: list[str], model_id: str, **kwargs: Any) -> TimedResult:
        self._require_texts(prompts)
        return self._timed(
            lambda: self.provider.generate(prompts, model_id, **kwargs),
            model_id=model_id,
            task=TaskLane.INSTRUCT,
        )

    def dispatch(
        self,
        task: TaskLane,
        *,
        texts: list[str] | None = None,
        questions: list[str] | None = None,
        contexts: list[str] | None = None,
        model_id: str,
        **kwargs: Any,
    ) -> TimedResult:
        if task is TaskLane.CLASSIFICATION:
            return self.run_classification(texts or [], model_id, **kwargs)
        if task is TaskLane.SUMMARIZATION:
            return self.run_summarization(texts or [], model_id, **kwargs)
        if task is TaskLane.QA:
            return self.run_extractive_qa(questions or [], contexts or [], model_id, **kwargs)
        if task is TaskLane.INSTRUCT:
            return self.run_instruct(texts or [], model_id, **kwargs)
        raise UnsupportedTaskError(f"Unsupported task lane: {task}", {"task": task})

    # ---------------------- helpers ---------------------- #

    @staticmethod
    def _require_texts(texts: list[str]) -> None:
        if not texts:
            raise ModelProviderError("texts must be a non-empty list", {"count": 0})

    def _timed(
        self,
        fn: Any,
        *,
        model_id: str,
        task: TaskLane,
    ) -> TimedResult:
        start = time.perf_counter()
        try:
            outputs = fn()
        except ModelProviderError:
            raise
        except Exception as exc:
            raise ModelProviderError(
                f"Inference failed for {task.value}/{model_id}: {exc}",
                {"task": task.value, "model_id": model_id},
            ) from exc
        duration_ms = (time.perf_counter() - start) * 1000.0
        self._log.info(
            "inference_call task=%s model=%s duration_ms=%.2f",
            task.value,
            model_id,
            duration_ms,
        )
        return TimedResult(
            latency_ms=duration_ms,
            outputs=list(outputs),
            model_id=model_id,
            task=task,
        )


__all__ = [
    "ClassificationOutput",
    "GenerationOutput",
    "ModelService",
    "QAOutput",
    "SummarizationOutput",
    "TimedResult",
]
