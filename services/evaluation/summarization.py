"""Lightweight ROUGE-style overlap metrics (pure python)."""

from __future__ import annotations

import re
from collections import Counter


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", text.lower())


def _ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    if n <= 0 or n > len(tokens):
        return []
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def _lcs_length(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        curr = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = curr
    return prev[-1]


def _rouge_n(reference: str, candidate: str, n: int) -> float:
    ref_tokens = _tokenize(reference)
    cand_tokens = _tokenize(candidate)
    ref_ngrams = Counter(_ngrams(ref_tokens, n))
    cand_ngrams = Counter(_ngrams(cand_tokens, n))
    if not ref_ngrams or not cand_ngrams:
        return 0.0
    overlap = sum((ref_ngrams & cand_ngrams).values())
    return overlap / sum(ref_ngrams.values())


def _rouge_l(reference: str, candidate: str) -> float:
    ref_tokens = _tokenize(reference)
    cand_tokens = _tokenize(candidate)
    if not ref_tokens or not cand_tokens:
        return 0.0
    lcs = _lcs_length(ref_tokens, cand_tokens)
    recall = lcs / len(ref_tokens)
    precision = lcs / len(cand_tokens)
    if recall + precision == 0:
        return 0.0
    return 2 * recall * precision / (recall + precision)


def summarization_metrics(references: list[str], candidates: list[str]) -> dict[str, float]:
    """Compute mean ROUGE-1, ROUGE-2, and ROUGE-L (F1)."""
    if len(references) != len(candidates):
        raise ValueError("references and candidates must be the same length")
    if not references:
        return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0, "support": 0}

    r1 = [_rouge_n(r, c, 1) for r, c in zip(references, candidates, strict=True)]
    r2 = [_rouge_n(r, c, 2) for r, c in zip(references, candidates, strict=True)]
    rl = [_rouge_l(r, c) for r, c in zip(references, candidates, strict=True)]
    n = float(len(references))
    return {
        "rouge1": round(sum(r1) / n, 6),
        "rouge2": round(sum(r2) / n, 6),
        "rougeL": round(sum(rl) / n, 6),
        "support": len(references),
    }
