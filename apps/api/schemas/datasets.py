"""Dataset-related request and response schemas."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from apps.api.schemas.common import APIModel


class TaskLane(StrEnum):
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    QA = "qa"
    INSTRUCT = "instruct"


class DatasetSource(StrEnum):
    HF = "hf"
    UPLOAD = "upload"


class DatasetSchemaMapping(APIModel):
    text_columns: list[str] = Field(default_factory=list, min_length=1)
    label_columns: list[str] = Field(default_factory=list)
    question_column: str | None = None
    context_column: str | None = None
    answer_column: str | None = None


class DatasetManifest(APIModel):
    id: UUID
    dataset_id: str
    source: DatasetSource
    task_lanes: list[TaskLane] = Field(default_factory=list)
    splits: list[str] = Field(default_factory=list)
    schema_mapping: DatasetSchemaMapping
    row_count: int = Field(ge=0)
    license: str | None = None
    snapshot: str | None = None
    created_at: str


class DatasetPreviewResponse(APIModel):
    manifest_id: UUID
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int = Field(ge=0)


class DatasetImportHFRequest(APIModel):
    dataset_id: str = Field(min_length=1, max_length=200)
    split: str = Field(default="train", min_length=1, max_length=64)
    max_rows: int = Field(default=200, ge=1, le=10_000)
    text_columns: list[str] | None = None
    label_columns: list[str] | None = None


class DatasetUploadMeta(APIModel):
    filename: str
    size_bytes: int = Field(ge=0)
    content_type: str | None = None
