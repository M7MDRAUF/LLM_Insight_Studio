"""Provider protocol and normalized inference output types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ClassificationOutput:
    label: str
    score: float
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SummarizationOutput:
    summary: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QAOutput:
    answer: str
    score: float
    start: int | None = None
    end: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationOutput:
    text: str
    raw: dict[str, Any] = field(default_factory=dict)


class InferenceProvider(Protocol):
    """Provider-neutral inference interface."""

    name: str

    def classify(
        self, texts: list[str], model_id: str, **kwargs: Any
    ) -> list[ClassificationOutput]: ...

    def summarize(
        self, texts: list[str], model_id: str, **kwargs: Any
    ) -> list[SummarizationOutput]: ...

    def answer(
        self, questions: list[str], contexts: list[str], model_id: str, **kwargs: Any
    ) -> list[QAOutput]: ...

    def generate(
        self, prompts: list[str], model_id: str, **kwargs: Any
    ) -> list[GenerationOutput]: ...
