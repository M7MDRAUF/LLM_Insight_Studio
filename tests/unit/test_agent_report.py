"""Tests for the report writer and reference catalogue."""

from __future__ import annotations

import pytest
from pydantic import HttpUrl

from apps.api.core.errors import ReferenceValidationError
from apps.api.schemas.agent import AgentReferenceItem
from apps.api.schemas.datasets import TaskLane
from services.agent.references import (
    DEFAULT_REFERENCES,
    curate_references,
    validate_references,
)
from services.agent.report_writer import render_report_markdown


def test_default_references_are_validated() -> None:
    assert len(DEFAULT_REFERENCES) >= 10
    validate_references(DEFAULT_REFERENCES)


def test_curate_prefers_matching_tasks() -> None:
    refs = curate_references([TaskLane.CLASSIFICATION], max_items=5)
    assert len(refs) == 5
    assert any("distilbert" in str(r.url).lower() for r in refs)


def test_validate_rejects_duplicates() -> None:
    dup = DEFAULT_REFERENCES[0]
    with pytest.raises(ReferenceValidationError):
        validate_references([dup, dup])


def test_report_markdown_contains_sections() -> None:
    sample = AgentReferenceItem(
        title="HF Datasets",
        url=HttpUrl("https://huggingface.co/docs/datasets/index"),
        type="docs",
        why_it_matters="Needed for dataset loading.",
    )
    md = render_report_markdown(
        title="T",
        objective="obj",
        dataset_ids=["ds"],
        model_ids=["m"],
        methodology="meth",
        metrics_by_lane={"classification": {"f1_macro": 0.8, "latency_ms": 1.0, "model_id": "m"}},
        findings=["finding 1"],
        limitations=["limit 1"],
        references=[sample],
        experiment_id="exp",
    )
    for heading in (
        "# T",
        "## Objective",
        "## Selected Datasets",
        "## Selected Models",
        "## Methodology",
        "## Evaluation Metrics",
        "## References",
        "## Provenance Appendix",
    ):
        assert heading in md
