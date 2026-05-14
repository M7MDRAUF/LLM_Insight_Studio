"""Application settings loaded from environment variables.

Uses ``pydantic-settings`` so every configuration field is typed and documented.
All filesystem paths are anchored at the repository root so the runtime is
indifferent to the process current working directory.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

InferenceProviderName = Literal["mock", "transformers"]

# Anchor relative defaults at the repository root (…/apps/api/core/settings.py → repo root).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ARTIFACTS_DIR = _REPO_ROOT / "artifacts"
_DEFAULT_DB_PATH = _DEFAULT_ARTIFACTS_DIR / "studio.db"


class Settings(BaseSettings):
    """Runtime configuration for the API and services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    api_host: str = "0.0.0.0"  # nosec B104
    api_port: int = 8000
    log_level: str = "INFO"

    # CORS — comma-separated list of allowed origins for the browser app.
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
    )

    # Persistence — defaults are absolute paths anchored to the repo root.
    database_url: str = f"sqlite:///{_DEFAULT_DB_PATH.as_posix()}"
    artifacts_dir: Path = _DEFAULT_ARTIFACTS_DIR

    # Hugging Face
    hf_token: str | None = None

    # Default models
    default_classification_model: str = "distilbert-base-uncased-finetuned-sst-2-english"
    default_summarization_model: str = "google/flan-t5-base"
    default_qa_model: str = "deepset/roberta-base-squad2"
    default_instruct_model: str = "Qwen/Qwen2.5-7B-Instruct"

    # Inference
    inference_provider: InferenceProviderName = "mock"

    # Agent
    agent_enabled: bool = True
    agent_max_references: int = Field(default=25, ge=1, le=200)

    # Safety / runtime guards
    max_upload_bytes: int = Field(default=50 * 1024 * 1024, ge=1024, le=1024 * 1024 * 1024)
    experiment_timeout_s: int = Field(default=600, ge=1, le=24 * 3600)
    enable_rate_limit: bool = False

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            parts = [v.strip() for v in value.split(",") if v.strip()]
            return parts or ["http://localhost:3000"]
        return value

    @field_validator("artifacts_dir", mode="after")
    @classmethod
    def _resolve_artifacts(cls, value: Path) -> Path:
        return value if value.is_absolute() else (_REPO_ROOT / value).resolve()

    @property
    def artifacts_reports_dir(self) -> Path:
        return self.artifacts_dir / "reports"

    @property
    def artifacts_experiments_dir(self) -> Path:
        return self.artifacts_dir / "experiments"

    @property
    def artifacts_charts_dir(self) -> Path:
        return self.artifacts_dir / "charts"

    def ensure_directories(self) -> None:
        """Create artifact directories if missing. Safe to call multiple times."""
        for path in (
            self.artifacts_dir,
            self.artifacts_reports_dir,
            self.artifacts_experiments_dir,
            self.artifacts_charts_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
