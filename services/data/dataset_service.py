"""High-level dataset service used by routers and the experiment orchestrator.

Manifests, schemas and previews are persisted in SQLite via
:class:`DatasetRepository`. Canonical records are kept in a bounded in-process
LRU cache keyed by manifest id so repeated experiment runs do not have to
re-parse the source on every request, while still bounding memory.
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import UUID, uuid4

from sqlmodel import Session

from apps.api.core.errors import DatasetValidationError
from apps.api.core.logging import get_logger
from apps.api.core.settings import Settings, get_settings
from apps.api.repositories.datasets import DatasetRepository
from apps.api.repositories.models import DatasetManifestRow
from apps.api.schemas.datasets import (
    DatasetManifest,
    DatasetPreviewResponse,
    DatasetSchemaMapping,
    DatasetSource,
    TaskLane,
)
from services.data.normalize import CanonicalRecord, normalize_records

_RECORDS_CACHE_MAX = 8
_log = get_logger(__name__)


class _RecordsCache:
    """Bounded LRU cache for canonical records, keyed by manifest id."""

    def __init__(self, capacity: int = _RECORDS_CACHE_MAX) -> None:
        self._items: OrderedDict[UUID, list[CanonicalRecord]] = OrderedDict()
        self._capacity = capacity
        self._lock = RLock()

    def get(self, manifest_id: UUID) -> list[CanonicalRecord] | None:
        with self._lock:
            entry = self._items.get(manifest_id)
            if entry is None:
                return None
            self._items.move_to_end(manifest_id)
            return entry

    def put(self, manifest_id: UUID, records: list[CanonicalRecord]) -> None:
        with self._lock:
            self._items[manifest_id] = records
            self._items.move_to_end(manifest_id)
            while len(self._items) > self._capacity:
                self._items.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


_RECORDS_CACHE = _RecordsCache()


class DatasetService:
    """Importing, previewing and retrieving dataset manifests."""

    def __init__(
        self,
        session: Session,
        settings: Settings | None = None,
        repository: DatasetRepository | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.repository = repository or DatasetRepository(session)

    # ----------------------------- public API --------------------------------

    def import_hf(
        self,
        dataset_id: str,
        split: str = "train",
        max_rows: int = 200,
        text_columns: list[str] | None = None,
        label_columns: list[str] | None = None,
    ) -> DatasetManifest:
        from services.data.hf_loader import load_hf_rows

        rows, columns = load_hf_rows(dataset_id, split, max_rows)
        text_cols = text_columns or self._guess_text_columns(columns)
        if not text_cols:
            raise DatasetValidationError(
                "Could not infer a text column; specify text_columns explicitly.",
                {"columns": columns},
            )
        label_cols = label_columns or [c for c in ("label", "labels") if c in columns]
        return self._finalize(
            dataset_id=dataset_id,
            source=DatasetSource.HF,
            rows=rows,
            columns=columns,
            splits=[split],
            schema_mapping=DatasetSchemaMapping(text_columns=text_cols, label_columns=label_cols),
            task_lanes=self._infer_lanes(columns, label_cols),
        )

    def import_upload(
        self,
        filename: str,
        data: bytes,
        text_columns: list[str] | None = None,
        label_columns: list[str] | None = None,
    ) -> DatasetManifest:
        from services.data.upload_loader import parse_upload

        rows, columns = parse_upload(filename, data)
        text_cols = text_columns or self._guess_text_columns(columns)
        if not text_cols:
            raise DatasetValidationError(
                "Could not infer a text column from upload.", {"columns": columns}
            )
        label_cols = label_columns or [c for c in ("label", "labels") if c in columns]
        return self._finalize(
            dataset_id=f"upload:{filename}",
            source=DatasetSource.UPLOAD,
            rows=rows,
            columns=columns,
            splits=["upload"],
            schema_mapping=DatasetSchemaMapping(text_columns=text_cols, label_columns=label_cols),
            task_lanes=self._infer_lanes(columns, label_cols),
        )

    def get_manifest(self, manifest_id: UUID) -> DatasetManifest:
        row = self.repository.get(manifest_id)
        if row is None:
            raise DatasetValidationError(
                f"Unknown dataset manifest: {manifest_id}", {"manifest_id": str(manifest_id)}
            )
        return self._row_to_manifest(row)

    def get_records(self, manifest_id: UUID) -> list[CanonicalRecord]:
        cached = _RECORDS_CACHE.get(manifest_id)
        if cached is not None:
            return cached
        row = self.repository.get(manifest_id)
        if row is None:
            raise DatasetValidationError(
                f"Unknown dataset manifest: {manifest_id}", {"manifest_id": str(manifest_id)}
            )
        # Records are not persisted by design — re-derive from preview rows so
        # downstream lanes can still operate on cold caches without a re-import.
        preview_rows = list(row.preview_json)
        if len(preview_rows) < row.row_count:
            _log.warning(
                "records_cold_start_truncation manifest_id=%s preview_rows=%d row_count=%d",
                manifest_id,
                len(preview_rows),
                row.row_count,
            )
        schema = row.schema_mapping_json
        records = normalize_records(
            preview_rows,
            text_columns=list(schema.get("text_columns", []) or ["text"]),
            label_columns=list(schema.get("label_columns", []) or []),
            question_column=schema.get("question_column"),
            context_column=schema.get("context_column"),
            answer_column=schema.get("answer_column"),
        )
        _RECORDS_CACHE.put(manifest_id, records)
        return records

    def preview(self, manifest_id: UUID, limit: int = 10) -> DatasetPreviewResponse:
        row = self.repository.get(manifest_id)
        if row is None:
            raise DatasetValidationError(
                f"Unknown dataset manifest: {manifest_id}", {"manifest_id": str(manifest_id)}
            )
        return DatasetPreviewResponse(
            manifest_id=manifest_id,
            columns=list(row.schema_mapping_json.get("columns", []) or []),
            rows=list(row.preview_json[:limit]),
            total_rows=row.row_count,
        )

    def list_manifests(self) -> list[DatasetManifest]:
        return [self._row_to_manifest(row) for row in self.repository.list(limit=200)]

    # ----------------------------- helpers -----------------------------------

    @staticmethod
    def _guess_text_columns(columns: list[str]) -> list[str]:
        preferred = [
            "text",
            "sentence",
            "review",
            "comment",
            "content",
            "body",
            "context",
        ]
        found = [c for c in preferred if c in columns]
        return found if found else (columns[:1] if columns else [])

    @staticmethod
    def _infer_lanes(columns: list[str], label_cols: list[str]) -> list[TaskLane]:
        lanes: list[TaskLane] = []
        if label_cols:
            lanes.append(TaskLane.CLASSIFICATION)
        if {"question", "context"}.issubset(set(columns)):
            lanes.append(TaskLane.QA)
        lanes.append(TaskLane.SUMMARIZATION)
        if TaskLane.INSTRUCT not in lanes:
            lanes.append(TaskLane.INSTRUCT)
        return lanes

    def _finalize(
        self,
        *,
        dataset_id: str,
        source: DatasetSource,
        rows: list[dict[str, Any]],
        columns: list[str],
        splits: list[str],
        schema_mapping: DatasetSchemaMapping,
        task_lanes: list[TaskLane],
    ) -> DatasetManifest:
        question_col = "question" if "question" in columns else None
        context_col = "context" if "context" in columns else None
        answer_col = (
            "answers" if "answers" in columns else ("answer" if "answer" in columns else None)
        )

        records = normalize_records(
            rows,
            text_columns=schema_mapping.text_columns,
            label_columns=schema_mapping.label_columns,
            question_column=question_col,
            context_column=context_col,
            answer_column=answer_col,
        )
        if not records:
            raise DatasetValidationError(
                "No usable records after normalization.", {"rows_in": len(rows)}
            )

        manifest_id = uuid4()
        preview = [{"row_id": r.row_id, "text": r.text, "label": r.label} for r in records[:20]]
        schema_payload: dict[str, Any] = {
            **schema_mapping.model_dump(mode="json"),
            "columns": columns,
            "question_column": question_col,
            "context_column": context_col,
            "answer_column": answer_col,
        }
        row = DatasetManifestRow(
            id=manifest_id,
            dataset_id=dataset_id,
            source=source.value,
            task_lanes_json=[l.value for l in task_lanes],
            splits_json=list(splits),
            schema_mapping_json=schema_payload,
            row_count=len(records),
            preview_json=preview,
            created_at=datetime.now(tz=UTC),
        )
        self.repository.create(row)
        _RECORDS_CACHE.put(manifest_id, records)
        return self._row_to_manifest(row)

    @staticmethod
    def _row_to_manifest(row: DatasetManifestRow) -> DatasetManifest:
        schema = row.schema_mapping_json
        return DatasetManifest(
            id=row.id,
            dataset_id=row.dataset_id,
            source=DatasetSource(row.source),
            task_lanes=[TaskLane(t) for t in row.task_lanes_json],
            splits=list(row.splits_json),
            schema_mapping=DatasetSchemaMapping(
                text_columns=list(schema.get("text_columns", []) or []),
                label_columns=list(schema.get("label_columns", []) or []),
                question_column=schema.get("question_column"),
                context_column=schema.get("context_column"),
                answer_column=schema.get("answer_column"),
            ),
            row_count=row.row_count,
            license=row.license,
            snapshot=row.snapshot,
            created_at=row.created_at.isoformat(),
        )


def reset_dataset_memory() -> None:
    """Test helper — wipe the bounded record cache."""
    _RECORDS_CACHE.clear()
