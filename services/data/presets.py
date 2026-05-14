"""Curated benchmark dataset presets."""

from __future__ import annotations

from dataclasses import dataclass

from apps.api.schemas.datasets import TaskLane


@dataclass(frozen=True)
class DatasetPreset:
    dataset_id: str
    task: TaskLane
    default_split: str
    text_column: str
    label_column: str | None = None
    description: str = ""


DATASET_PRESETS: dict[str, DatasetPreset] = {
    "rotten_tomatoes": DatasetPreset(
        dataset_id="cornell-movie-review-data/rotten_tomatoes",
        task=TaskLane.CLASSIFICATION,
        default_split="train",
        text_column="text",
        label_column="label",
        description="Binary movie review sentiment.",
    ),
    "squad": DatasetPreset(
        dataset_id="rajpurkar/squad",
        task=TaskLane.QA,
        default_split="validation",
        text_column="context",
        description="Extractive question answering benchmark.",
    ),
    "billsum": DatasetPreset(
        dataset_id="billsum",
        task=TaskLane.SUMMARIZATION,
        default_split="train",
        text_column="text",
        description="US congressional bill summarization dataset.",
    ),
}
