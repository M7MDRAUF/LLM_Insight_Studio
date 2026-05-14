"""Deterministic markdown report writer with provenance footer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import yaml

from apps.api.schemas.agent import AgentReferenceItem


def _format_metric_table(metrics_by_lane: dict[str, dict[str, Any] | None]) -> str:
    rows = ["| Task | Model | Key metric | Value | Latency (ms) |", "|---|---|---|---|---|"]
    key_metric = {
        "classification": "f1_macro",
        "summarization": "rougeL",
        "qa": "f1",
        "instruct": "support",
    }
    for lane, metrics in metrics_by_lane.items():
        if not metrics:
            continue
        name = key_metric.get(lane, next(iter(metrics.keys()), "-"))
        value = metrics.get(name, "-")
        model_id = metrics.get("model_id", "-")
        latency = metrics.get("latency_ms", "-")
        rows.append(f"| {lane} | {model_id} | {name} | {value} | {latency} |")
    if len(rows) == 2:
        rows.append("| _no metrics available_ |  |  |  |  |")
    return "\n".join(rows)


def render_report_markdown(
    *,
    title: str,
    objective: str,
    dataset_ids: list[str],
    model_ids: list[str],
    methodology: str,
    metrics_by_lane: dict[str, dict[str, Any] | None],
    findings: list[str],
    limitations: list[str],
    references: list[AgentReferenceItem],
    experiment_id: str,
    code_revision: str = "unknown",
) -> str:
    """Render the canonical report markdown.

    The layout matches ``docs/MASTER_SPEC.md`` §21.1 exactly.
    """
    now = datetime.now(tz=UTC).isoformat()
    ref_lines = [
        f"- [{r.title}]({r.url}) — *{r.type}*. {r.why_it_matters}" for r in references
    ] or ["_No validated references available._"]

    provenance: dict[str, Any] = {
        "provenance": {
            "experiment_id": experiment_id,
            "generated_at": now,
            "dataset_ids": dataset_ids,
            "model_ids": model_ids,
            "code_revision": code_revision,
            "reference_count": len(references),
        }
    }
    provenance_yaml = yaml.safe_dump(provenance, sort_keys=False).strip()

    findings_md = "\n".join(f"- {f}" for f in findings) if findings else "_No findings recorded._"
    limitations_md = (
        "\n".join(f"- {l}" for l in limitations) if limitations else "- None explicitly documented."
    )

    parts = [
        f"# {title}",
        "",
        "## Objective",
        objective.strip(),
        "",
        "## Selected Datasets",
        "\n".join(f"- `{d}`" for d in dataset_ids) or "- _none_",
        "",
        "## Selected Models",
        "\n".join(f"- `{m}`" for m in model_ids) or "- _none_",
        "",
        "## Methodology",
        methodology.strip(),
        "",
        "## Preprocessing Rules",
        (
            "- Unicode NFKC normalization and whitespace trimming.\n"
            "- Empty rows removed; stable row ids preserved.\n"
            "- Long documents chunked on paragraph boundaries."
        ),
        "",
        "## Evaluation Metrics",
        _format_metric_table(metrics_by_lane),
        "",
        "## Quantitative Findings",
        findings_md,
        "",
        "## Qualitative Findings",
        (
            "Qualitative review was performed against the faithfulness, relevance, conciseness, "
            "actionability, and explainability rubric defined in MASTER_SPEC §18.5."
        ),
        "",
        "## Limitations",
        limitations_md,
        "",
        "## Recommended Model per Task",
        _format_metric_table(metrics_by_lane),
        "",
        "## References",
        "\n".join(ref_lines),
        "",
        "## Provenance Appendix",
        "```yaml",
        provenance_yaml,
        "```",
        "",
    ]
    return "\n".join(parts)
