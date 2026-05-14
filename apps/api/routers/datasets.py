"""Dataset routes: import (HF + upload), preview, list."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

from apps.api.core.deps import get_dataset_service
from apps.api.core.errors import DatasetValidationError
from apps.api.core.settings import get_settings
from apps.api.schemas.datasets import (
    DatasetImportHFRequest,
    DatasetManifest,
    DatasetPreviewResponse,
)
from services.data.dataset_service import DatasetService
from services.data.upload_loader import ALLOWED_CONTENT_TYPES

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/import/hf", response_model=DatasetManifest, status_code=201)
def import_hf_dataset(
    payload: DatasetImportHFRequest,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetManifest:
    return service.import_hf(
        dataset_id=payload.dataset_id,
        split=payload.split,
        max_rows=payload.max_rows,
        text_columns=payload.text_columns,
        label_columns=payload.label_columns,
    )


@router.post("/import/upload", response_model=DatasetManifest, status_code=201)
async def import_upload_dataset(
    file: UploadFile = File(...),
    text_columns: str | None = Form(default=None),
    label_columns: str | None = Form(default=None),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetManifest:
    settings = get_settings()
    max_bytes = settings.max_upload_bytes
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise DatasetValidationError(
            f"Unsupported content-type: {content_type or '(none)'}",
            {"content_type": content_type, "allowed": sorted(ALLOWED_CONTENT_TYPES)},
        )

    # Stream the upload while enforcing a hard size cap to avoid OOM/DoS.
    # Reject *before* appending so at most one full chunk is resident in memory.
    chunks: list[bytes] = []
    total = 0
    chunk_size = 1 << 20  # 1 MiB
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        if total + len(chunk) > max_bytes:
            raise DatasetValidationError(
                "Upload exceeds the configured maximum size.",
                {"limit_bytes": max_bytes, "received_bytes": total + len(chunk)},
            )
        total += len(chunk)
        chunks.append(chunk)
    data = b"".join(chunks)

    text_cols = [c.strip() for c in text_columns.split(",") if c.strip()] if text_columns else None
    label_cols = (
        [c.strip() for c in label_columns.split(",") if c.strip()] if label_columns else None
    )
    safe_filename = (file.filename or "upload.bin").replace("\\", "/").split("/")[-1]
    return service.import_upload(
        filename=safe_filename,
        data=data,
        text_columns=text_cols,
        label_columns=label_cols,
    )


@router.get("", response_model=list[DatasetManifest])
def list_datasets(
    service: DatasetService = Depends(get_dataset_service),
) -> list[DatasetManifest]:
    return service.list_manifests()


@router.get("/{manifest_id}", response_model=DatasetManifest)
def get_dataset(
    manifest_id: UUID,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetManifest:
    return service.get_manifest(manifest_id)


@router.get("/{manifest_id}/preview", response_model=DatasetPreviewResponse)
def preview_dataset(
    manifest_id: UUID,
    limit: int = 10,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetPreviewResponse:
    return service.preview(manifest_id, limit=limit)
