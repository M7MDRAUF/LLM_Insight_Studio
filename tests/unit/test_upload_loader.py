"""Parametrized tests for the multi-format upload loader."""

from __future__ import annotations

import json

import pytest

from apps.api.core.errors import DatasetValidationError
from services.data.upload_loader import parse_upload


def test_parse_csv_basic() -> None:
    data = b"text,label\nhello,1\nworld,0\n"
    rows, columns = parse_upload("a.csv", data)
    assert columns == ["text", "label"]
    assert rows == [{"text": "hello", "label": "1"}, {"text": "world", "label": "0"}]


def test_parse_jsonl_basic() -> None:
    data = b'{"text": "a"}\n{"text": "b"}\n'
    rows, columns = parse_upload("a.jsonl", data)
    assert columns == ["text"]
    assert rows == [{"text": "a"}, {"text": "b"}]


def test_parse_json_list() -> None:
    payload = json.dumps([{"text": "a"}, {"text": "b"}]).encode()
    rows, columns = parse_upload("a.json", payload)
    assert columns == ["text"]
    assert len(rows) == 2


def test_parse_json_data_envelope() -> None:
    payload = json.dumps({"data": [{"text": "x"}]}).encode()
    rows, columns = parse_upload("a.json", payload)
    assert columns == ["text"]
    assert rows == [{"text": "x"}]


def test_parse_txt_basic() -> None:
    data = b"line one\nline two\n\n"
    rows, columns = parse_upload("a.txt", data)
    assert columns == ["text"]
    assert rows == [{"text": "line one"}, {"text": "line two"}]


@pytest.mark.parametrize(
    ("filename", "data"),
    [
        ("bad.csv", b""),
        ("bad.json", b"not-json"),
        ("bad.json", json.dumps({"foo": 1}).encode()),
        ("bad.jsonl", b'{"ok": 1}\n{not-json\n'),
        ("bad.unknown", b"x"),
        ("", b"x"),
    ],
)
def test_parse_invalid_inputs_raise(filename: str, data: bytes) -> None:
    with pytest.raises(DatasetValidationError):
        parse_upload(filename, data)
