"""Filesystem-backed artifact persistence."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID

from apps.api.core.errors import ArtifactReadError, ArtifactWriteError, NotFoundError
from apps.api.core.settings import Settings, get_settings


class ArtifactService:
    """Write and read report/experiment artifacts under ``artifacts/``."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.settings.ensure_directories()

    # ---------------- experiments ---------------- #

    def save_experiment(self, experiment_id: UUID, payload: dict[str, Any]) -> Path:
        path = self.settings.artifacts_experiments_dir / f"{experiment_id}.json"
        return self._write_json(path, payload)

    def load_experiment(self, experiment_id: UUID) -> dict[str, Any]:
        path = self.settings.artifacts_experiments_dir / f"{experiment_id}.json"
        return self._read_json(path)

    # ---------------- reports ---------------- #

    def save_report(
        self, report_id: UUID, markdown: str, *, sidecar: dict[str, Any] | None = None
    ) -> Path:
        md_path = self.settings.artifacts_reports_dir / f"{report_id}.md"
        try:
            self._atomic_write_bytes(md_path, markdown.encode("utf-8"))
        except OSError as exc:
            raise ArtifactWriteError(
                f"Failed to write report {report_id}: {exc}", {"path": str(md_path)}
            ) from exc
        if sidecar is not None:
            self._write_json(md_path.with_suffix(".json"), sidecar)
        return md_path

    def load_report(self, report_id: UUID) -> str:
        path = self.settings.artifacts_reports_dir / f"{report_id}.md"
        if not path.exists():
            raise NotFoundError(f"Report not found: {report_id}", {"report_id": str(report_id)})
        return path.read_text(encoding="utf-8")

    def report_path(self, report_id: UUID) -> Path:
        return self.settings.artifacts_reports_dir / f"{report_id}.md"

    # ---------------- internals ---------------- #

    @classmethod
    def _write_json(cls, path: Path, payload: dict[str, Any]) -> Path:
        try:
            data = json.dumps(payload, indent=2, default=str).encode("utf-8")
            cls._atomic_write_bytes(path, data)
        except OSError as exc:
            raise ArtifactWriteError(
                f"Failed to write artifact: {exc}", {"path": str(path)}
            ) from exc
        return path

    @staticmethod
    def _atomic_write_bytes(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write to a sibling temp file then rename for crash-safe persistence.
        fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise NotFoundError(f"Artifact not found: {path.name}", {"path": str(path)})
        try:
            data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            return data
        except (OSError, json.JSONDecodeError) as exc:
            raise ArtifactReadError(
                f"Failed to read artifact: {exc}", {"path": str(path)}
            ) from exc
