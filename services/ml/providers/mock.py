"""Deterministic mock provider — no model downloads, safe for CI and demos."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from services.ml.providers.base import (
    ClassificationOutput,
    GenerationOutput,
    QAOutput,
    SummarizationOutput,
)

_POSITIVE_WORDS = frozenset(
    {
        "good",
        "great",
        "love",
        "amazing",
        "excellent",
        "happy",
        "fantastic",
        "best",
        "nice",
        "awesome",
    }
)
_NEGATIVE_WORDS = frozenset(
    {"bad", "worst", "hate", "terrible", "awful", "angry", "slow", "broken", "poor", "sad"}
)


def _score_sentiment(text: str) -> tuple[str, float]:
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    pos = sum(1 for t in tokens if t in _POSITIVE_WORDS)
    neg = sum(1 for t in tokens if t in _NEGATIVE_WORDS)
    if pos == neg == 0:
        digest = hashlib.sha256(text.encode("utf-8")).digest()[0]
        label = "POSITIVE" if digest % 2 == 0 else "NEGATIVE"
        return label, 0.55
    if pos >= neg:
        return "POSITIVE", min(0.99, 0.5 + 0.1 * (pos - neg + 1))
    return "NEGATIVE", min(0.99, 0.5 + 0.1 * (neg - pos + 1))


def _naive_summary(text: str, max_chars: int = 240) -> str:
    text = " ".join(text.split())
    if not text:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = ""
    for s in sentences:
        if len(out) + len(s) + 1 > max_chars:
            break
        out = f"{out} {s}".strip() if out else s
    return out or text[:max_chars]


def _extractive_answer(question: str, context: str) -> tuple[str, float, int, int]:
    if not context:
        return "", 0.0, 0, 0
    q_tokens = {t.lower() for t in re.findall(r"\w+", question) if len(t) > 2}
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", context) if s]
    best_sentence = sentences[0] if sentences else context[:200]
    best_score = 0.0
    for s in sentences:
        tokens = {t.lower() for t in re.findall(r"\w+", s)}
        overlap = len(q_tokens & tokens)
        if overlap > best_score:
            best_score = float(overlap)
            best_sentence = s
    start = context.find(best_sentence)
    end = start + len(best_sentence) if start >= 0 else 0
    confidence = min(0.95, 0.4 + 0.1 * best_score)
    return best_sentence.strip(), confidence, max(0, start), max(0, end)


class MockProvider:
    """Fully deterministic provider for tests and offline demos."""

    name = "mock"

    def classify(
        self, texts: list[str], model_id: str, **kwargs: Any
    ) -> list[ClassificationOutput]:
        results: list[ClassificationOutput] = []
        for t in texts:
            label, score = _score_sentiment(t)
            results.append(
                ClassificationOutput(
                    label=label,
                    score=score,
                    raw={"model_id": model_id, "provider": self.name},
                )
            )
        return results

    def summarize(
        self, texts: list[str], model_id: str, **kwargs: Any
    ) -> list[SummarizationOutput]:
        max_chars = int(kwargs.get("max_chars", 240))
        return [
            SummarizationOutput(
                summary=_naive_summary(t, max_chars=max_chars),
                raw={"model_id": model_id, "provider": self.name},
            )
            for t in texts
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
        out: list[QAOutput] = []
        for q, ctx in zip(questions, contexts, strict=True):
            text, score, start, end = _extractive_answer(q, ctx)
            out.append(
                QAOutput(
                    answer=text,
                    score=score,
                    start=start,
                    end=end,
                    raw={"model_id": model_id, "provider": self.name},
                )
            )
        return out

    def generate(self, prompts: list[str], model_id: str, **kwargs: Any) -> list[GenerationOutput]:
        max_chars = int(kwargs.get("max_chars", 320))
        outputs: list[GenerationOutput] = []
        for p in prompts:
            preview = _naive_summary(p, max_chars=max_chars)
            text = f"[mock:{model_id}] {preview}" if preview else f"[mock:{model_id}]"
            outputs.append(
                GenerationOutput(text=text, raw={"model_id": model_id, "provider": self.name})
            )
        return outputs
