"""Record normalization utilities (deterministic, no ML deps)."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CanonicalRecord:
    """Canonical shape consumed by downstream task pipelines."""

    row_id: str
    text: str
    label: str | None = None
    question: str | None = None
    context: str | None = None
    answer: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)


def _clean(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    text = unicodedata.normalize("NFKC", text)
    return text.strip()


def _first_non_empty(row: dict[str, Any], columns: list[str]) -> str | None:
    for col in columns:
        value = row.get(col)
        if value is None:
            continue
        cleaned = _clean(str(value))
        if cleaned:
            return cleaned
    return None


def normalize_records(
    rows: list[dict[str, Any]],
    *,
    text_columns: list[str],
    label_columns: list[str] | None = None,
    question_column: str | None = None,
    context_column: str | None = None,
    answer_column: str | None = None,
    id_prefix: str = "row",
) -> list[CanonicalRecord]:
    """Normalize a list of raw rows into :class:`CanonicalRecord` items.

    Rules:
        - rows with an empty text field are dropped,
        - all strings are Unicode-normalized (NFKC) and stripped,
        - original row order is preserved,
        - stable row ids use ``{id_prefix}-{index}`` if none provided.
    """
    label_columns = label_columns or []
    out: list[CanonicalRecord] = []
    for idx, raw in enumerate(rows):
        if not isinstance(raw, dict):
            continue
        text = _first_non_empty(raw, text_columns)
        if not text:
            continue
        label = _first_non_empty(raw, label_columns) if label_columns else None
        question = (
            _clean(str(raw[question_column]))
            if question_column and raw.get(question_column)
            else None
        )
        context = (
            _clean(str(raw[context_column])) if context_column and raw.get(context_column) else None
        )
        answer = (
            _clean(str(raw[answer_column])) if answer_column and raw.get(answer_column) else None
        )
        row_id = str(raw.get("id") or raw.get("row_id") or f"{id_prefix}-{idx}")
        out.append(
            CanonicalRecord(
                row_id=row_id,
                text=text,
                label=label,
                question=question,
                context=context,
                answer=answer,
                extras={k: v for k, v in raw.items() if k not in {"id", "row_id"}},
            )
        )
    return out


def chunk_text(text: str, max_chars: int = 2_000) -> list[str]:
    """Split long text into chunks of ``max_chars`` on paragraph boundaries."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if len(text) <= max_chars:
        return [text]
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        candidate = f"{buf}\n\n{para}" if buf else para
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
        # Fallback: hard split for very long paragraphs.
        remainder = para
        while len(remainder) > max_chars:
            chunks.append(remainder[:max_chars])
            remainder = remainder[max_chars:]
        buf = remainder
    if buf:
        chunks.append(buf)
    return chunks
