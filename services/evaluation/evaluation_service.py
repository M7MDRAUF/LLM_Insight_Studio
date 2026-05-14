"""Facade over task-level metric functions."""

from __future__ import annotations

from typing import Any

from services.evaluation.classification import classification_metrics
from services.evaluation.qa import qa_metrics
from services.evaluation.summarization import summarization_metrics


class EvaluationService:
    """Thin facade so services/routers depend on a single evaluator object."""

    @staticmethod
    def classification(y_true: list[str], y_pred: list[str]) -> dict[str, Any]:
        return classification_metrics(y_true, y_pred)

    @staticmethod
    def summarization(references: list[str], candidates: list[str]) -> dict[str, float]:
        return summarization_metrics(references, candidates)

    @staticmethod
    def qa(
        predictions: list[str],
        ground_truths: list[str],
        contexts: list[str] | None = None,
    ) -> dict[str, float]:
        return qa_metrics(predictions, ground_truths, contexts)
