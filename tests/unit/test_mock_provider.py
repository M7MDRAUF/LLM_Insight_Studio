"""Mock inference provider tests."""

from __future__ import annotations

from services.ml.providers.mock import MockProvider


def _provider() -> MockProvider:
    return MockProvider()


def test_mock_classification_is_deterministic() -> None:
    p = _provider()
    out_a = p.classify(["This movie was wonderful and great"], "m")
    out_b = p.classify(["This movie was wonderful and great"], "m")
    assert out_a[0].label == out_b[0].label
    assert out_a[0].label.upper() == "POSITIVE"


def test_mock_classification_negative() -> None:
    outs = _provider().classify(["awful terrible horrible disaster"], "m")
    assert outs[0].label.upper() == "NEGATIVE"


def test_mock_summarization_produces_shorter_text() -> None:
    text = "Sentence one. Sentence two. Sentence three. Sentence four."
    out = _provider().summarize([text], "m")[0]
    assert len(out.summary) <= len(text)


def test_mock_qa_finds_overlap() -> None:
    context = "The quick brown fox jumps over the lazy dog near the river."
    out = _provider().answer(["brown fox"], [context], "m")[0]
    assert "fox" in out.answer.lower()
    assert 0.0 <= out.score <= 1.0
