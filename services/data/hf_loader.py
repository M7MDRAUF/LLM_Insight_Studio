"""Hugging Face dataset loader (lazy import)."""

from __future__ import annotations

from typing import Any

from apps.api.core.errors import DatasetValidationError


def load_hf_rows(
    dataset_id: str, split: str, max_rows: int
) -> tuple[list[dict[str, Any]], list[str]]:
    """Load up to ``max_rows`` records from a Hugging Face dataset.

    Returns ``(rows, column_names)``. Raises :class:`DatasetValidationError`
    if the dataset cannot be loaded.
    """
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - covered only when ml extra missing
        raise DatasetValidationError(
            "The 'datasets' package is not installed. Install the 'ml' extra.",
            {"dataset_id": dataset_id},
        ) from exc

    try:
        ds = load_dataset(dataset_id, split=f"{split}[:{max_rows}]")  # nosec B615
    except Exception as exc:
        raise DatasetValidationError(
            f"Could not load dataset '{dataset_id}' split '{split}': {exc}",
            {"dataset_id": dataset_id, "split": split},
        ) from exc

    columns: list[str] = list(ds.column_names)
    rows: list[dict[str, Any]] = [dict(row) for row in ds]
    return rows, columns
