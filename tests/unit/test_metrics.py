"""Evaluation metric tests."""

from __future__ import annotations

from services.evaluation.classification import classification_metrics
from services.evaluation.qa import qa_metrics
from services.evaluation.summarization import summarization_metrics


def test_classification_metrics_perfect() -> None:
    m = classification_metrics(["a", "b", "a"], ["a", "b", "a"])
    assert m["accuracy"] == 1.0
    assert m["f1_macro"] == 1.0


def test_classification_metrics_imperfect() -> None:
    m = classification_metrics(["a", "b", "a", "b"], ["a", "a", "a", "b"])
    assert 0.0 < float(m["accuracy"]) < 1.0  # type: ignore[arg-type]
    assert 0.0 < float(m["f1_macro"]) <= 1.0  # type: ignore[arg-type]


def test_summarization_metrics_identical() -> None:
    m = summarization_metrics(["the cat sat"], ["the cat sat"])
    assert m["rouge1"] == 1.0
    assert m["rougeL"] == 1.0


def test_summarization_metrics_disjoint() -> None:
    m = summarization_metrics(["alpha beta gamma"], ["xx yy zz"])
    assert m["rouge1"] == 0.0


def test_qa_metrics_exact_and_f1() -> None:
    m = qa_metrics(["paris"], ["Paris"], ["Paris is the capital of France."])
    assert m["exact_match"] == 1.0
    assert m["f1"] == 1.0
    assert m["evidence_hit_rate"] == 1.0


def test_qa_metrics_partial() -> None:
    m = qa_metrics(["big apple"], ["apple"], ["apple is a fruit"])
    assert 0.0 < m["f1"] < 1.0
