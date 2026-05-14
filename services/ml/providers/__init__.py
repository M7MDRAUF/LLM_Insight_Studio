"""Inference provider implementations."""

from __future__ import annotations

from apps.api.core.errors import ModelProviderError
from apps.api.core.settings import Settings
from services.ml.providers.base import InferenceProvider
from services.ml.providers.mock import MockProvider

__all__ = ["InferenceProvider", "MockProvider", "build_provider"]


def build_provider(name: str, *, settings: Settings) -> InferenceProvider:
    """Factory that returns a provider instance by name.

    ``mock`` always works and is used in tests and first-run demos.
    ``transformers`` lazy-imports the real Hugging Face pipelines.
    """
    normalized = name.lower().strip()
    if normalized == "mock":
        return MockProvider()
    if normalized == "transformers":
        from services.ml.providers.transformers_provider import TransformersProvider

        return TransformersProvider(hf_token=settings.hf_token)
    raise ModelProviderError(
        f"Unknown inference provider: {name}",
        {"provider": name, "supported": ["mock", "transformers"]},
    )
