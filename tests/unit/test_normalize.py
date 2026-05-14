"""Unit tests for the normalization helpers."""

from __future__ import annotations

from services.data.normalize import chunk_text, normalize_records


def test_normalize_records_strips_and_drops_empty() -> None:
    rows = [
        {"text": "  Hello  world\u00a0"},
        {"text": "  "},
        {"text": "Another row"},
    ]
    records = normalize_records(rows, text_columns=["text"])
    # NBSP (\u00a0) is NFKC-normalised to a regular space, but run-compression is not performed.
    assert records[0].text.startswith("Hello") and records[0].text.endswith("world")
    assert records[1].text == "Another row"
    assert [r.row_id for r in records] == ["row-0", "row-2"]


def test_normalize_records_with_labels() -> None:
    rows = [{"text": "good", "label": 1}, {"text": "bad", "label": 0}]
    records = normalize_records(rows, text_columns=["text"], label_columns=["label"])
    assert [r.label for r in records] == ["1", "0"]


def test_chunk_text_splits_paragraphs() -> None:
    text = "A" * 300 + "\n\n" + "B" * 300
    chunks = chunk_text(text, max_chars=250)
    assert len(chunks) >= 2
    assert all(len(c) <= 250 for c in chunks)


def test_chunk_text_short_input() -> None:
    assert chunk_text("hi", max_chars=100) == ["hi"]
