"""QA metrics: exact match, token-level F1, evidence hit rate."""

from __future__ import annotations

import re
import string
from collections import Counter


def _normalize(text: str) -> str:
    text = text.lower()
    text = "".join(ch for ch in text if ch not in set(string.punctuation))
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def _f1_score(pred: str, truth: str) -> float:
    pred_tokens = _normalize(pred).split()
    truth_tokens = _normalize(truth).split()
    if not pred_tokens and not truth_tokens:
        return 1.0
    if not pred_tokens or not truth_tokens:
        return 0.0
    common = Counter(pred_tokens) & Counter(truth_tokens)
    overlap = sum(common.values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(pred_tokens)
    recall = overlap / len(truth_tokens)
    return 2 * precision * recall / (precision + recall)


def qa_metrics(
    predictions: list[str],
    ground_truths: list[str],
    contexts: list[str] | None = None,
) -> dict[str, float]:
    """Compute EM, F1, and optional evidence hit rate.

    Evidence hit rate is the fraction of predictions whose normalized string
    appears inside the normalized context.
    """
    if len(predictions) != len(ground_truths):
        raise ValueError("predictions and ground_truths must be the same length")
    if not predictions:
        return {"exact_match": 0.0, "f1": 0.0, "evidence_hit_rate": 0.0, "support": 0}

    em_total = 0
    f1_total = 0.0
    evidence_hits = 0
    for idx, (pred, truth) in enumerate(zip(predictions, ground_truths, strict=True)):
        if _normalize(pred) == _normalize(truth):
            em_total += 1
        f1_total += _f1_score(pred, truth)
        if contexts is not None and idx < len(contexts):
            norm_ctx = _normalize(contexts[idx])
            norm_pred = _normalize(pred)
            if norm_pred and norm_pred in norm_ctx:
                evidence_hits += 1

    n = float(len(predictions))
    result = {
        "exact_match": round(em_total / n, 6),
        "f1": round(f1_total / n, 6),
        "support": len(predictions),
    }
    if contexts is not None:
        result["evidence_hit_rate"] = round(evidence_hits / n, 6)
    else:
        result["evidence_hit_rate"] = 0.0
    return result
