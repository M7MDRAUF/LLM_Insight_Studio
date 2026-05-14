"""Research agent orchestrating tools, plan drafts, and report writing."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Session

from apps.api.core.errors import ExperimentExecutionError
from apps.api.core.settings import Settings, get_settings
from apps.api.repositories.experiments import ExperimentRepository
from apps.api.repositories.models import ReportRow
from apps.api.repositories.reports import ReportRepository
from apps.api.schemas.agent import (
    AgentReferenceItem,
    ResearchPlanRequest,
    ResearchPlanResponse,
    ResearchReportRequest,
    ResearchReportResponse,
)
from apps.api.schemas.datasets import TaskLane
from apps.api.schemas.experiments import MetricsByLane
from services.agent.references import curate_references, validate_references
from services.agent.report_writer import render_report_markdown
from services.artifacts.artifact_service import ArtifactService
from services.ml.defaults import default_model_for


class ResearchAgent:
    """smolagents-compatible research agent with deterministic tool-backed logic."""

    def __init__(
        self,
        session: Session,
        settings: Settings | None = None,
        artifacts: ArtifactService | None = None,
        experiments: ExperimentRepository | None = None,
        reports: ReportRepository | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.artifacts = artifacts or ArtifactService(self.settings)
        self.experiments = experiments or ExperimentRepository(session)
        self.reports = reports or ReportRepository(session)

    # ------------------ planning ------------------ #

    def build_plan(self, request: ResearchPlanRequest) -> ResearchPlanResponse:
        refs = curate_references(
            list(request.task_lanes),
            max_items=self.settings.agent_max_references,
            extra_hints=list(request.dataset_hints) + list(request.model_hints),
        )
        validate_references(refs)

        lanes_md = "\n".join(f"- **{l.value}**" for l in request.task_lanes)
        hint_md = (
            "\n".join(f"- {h}" for h in request.dataset_hints)
            if request.dataset_hints
            else "- _none provided_"
        )
        plan = (
            f"# Research Plan: {request.topic}\n\n"
            f"## Task Lanes\n{lanes_md}\n\n"
            f"## Dataset Hints\n{hint_md}\n\n"
            "## Methodology\n"
            "1. Import candidate datasets via the dataset service.\n"
            "2. Execute each task lane on a stratified sample.\n"
            "3. Compute quality and latency metrics per lane.\n"
            "4. Curate references and validate provenance.\n"
            "5. Render a markdown report using the canonical template.\n\n"
            "## Evaluation\n"
            "- Classification: macro F1, precision, recall.\n"
            "- Summarization: ROUGE-1/2/L.\n"
            "- QA: Exact Match, token F1, evidence hit rate.\n"
        )
        return ResearchPlanResponse(plan_markdown=plan, references=refs)

    # ------------------ report writing ------------------ #

    def write_report(self, request: ResearchReportRequest) -> ResearchReportResponse:
        experiment_row = self.experiments.get(request.experiment_id)
        if experiment_row is None:
            raise ExperimentExecutionError(
                f"Unknown experiment: {request.experiment_id}",
                {"experiment_id": str(request.experiment_id)},
            )

        # Honor the report.enabled flag set when the experiment was created.
        report_opts = experiment_row.params_json.get("report") or {}
        if report_opts.get("enabled") is False:
            raise ExperimentExecutionError(
                "Report generation was disabled for this experiment.",
                {
                    "experiment_id": str(request.experiment_id),
                    "report_enabled": False,
                },
            )

        lanes = [TaskLane(t) for t in experiment_row.task_lanes_json]
        models_overrides = experiment_row.models_json
        model_ids = [models_overrides.get(l.value) or default_model_for(l) for l in lanes]
        dataset_ids = [str(experiment_row.dataset_manifest_id)]

        references: list[AgentReferenceItem] = []
        if request.include_references:
            references = curate_references(lanes, max_items=self.settings.agent_max_references)
            validate_references(references)

        metrics = MetricsByLane.model_validate(experiment_row.metrics_json or {})
        metrics_map: dict[str, dict[str, object] | None] = {
            "classification": dict(metrics.classification) if metrics.classification else None,
            "summarization": dict(metrics.summarization) if metrics.summarization else None,
            "qa": dict(metrics.qa) if metrics.qa else None,
            "instruct": dict(metrics.instruct) if metrics.instruct else None,
        }
        findings = self._derive_findings(metrics_map)

        markdown = render_report_markdown(
            title=f"LLM Insight Studio Report — {experiment_row.id}",
            objective=(
                "Compare three LLM/model families across the selected NLP task lanes "
                "and document reproducible findings for the source dataset."
            ),
            dataset_ids=dataset_ids,
            model_ids=model_ids,
            methodology=(
                "Each task lane ran a single deterministic inference pass over the sampled "
                "records. Metrics were computed with the repository's pure-Python implementations "
                "which mirror Hugging Face `evaluate` definitions."
            ),
            metrics_by_lane={k: v for k, v in metrics_map.items() if v is not None},
            findings=findings,
            limitations=[
                "Results reflect the sampled subset only; large-scale behaviour may differ.",
                "The mock provider is deterministic — swap to the transformers provider for benchmark claims.",
            ],
            references=references,
            experiment_id=str(experiment_row.id),
        )

        report_id = uuid4()
        path = self.artifacts.save_report(
            report_id,
            markdown,
            sidecar={
                "experiment_id": str(experiment_row.id),
                "generated_at": datetime.now(tz=UTC).isoformat(),
                "references": [r.model_dump(mode="json") for r in references],
            },
        )
        report_row = ReportRow(
            id=report_id,
            experiment_id=experiment_row.id,
            path=str(path),
            reference_count=len(references),
            references_json=[r.model_dump(mode="json") for r in references],
        )
        self.reports.create(report_row)
        return ResearchReportResponse(
            report_id=report_id,
            path=str(path),
            reference_count=len(references),
        )

    # ------------------ helpers ------------------ #

    @staticmethod
    def _default_model_for(lane: TaskLane) -> str:
        return default_model_for(lane)

    @staticmethod
    def _derive_findings(
        metrics: dict[str, dict[str, object] | None],
    ) -> list[str]:
        findings: list[str] = []
        clf = metrics.get("classification") or {}
        if clf.get("f1_macro") is not None:
            findings.append(f"Classification macro F1 on the sampled subset was {clf['f1_macro']}.")
        summ = metrics.get("summarization") or {}
        if summ.get("rougeL") is not None:
            findings.append(
                f"Summarization ROUGE-L reached {summ['rougeL']} against the source text baseline."
            )
        qa = metrics.get("qa") or {}
        if qa.get("exact_match") is not None:
            findings.append(f"QA exact-match was {qa['exact_match']} with F1 {qa.get('f1', '-')}.")
        if not findings:
            findings.append("No metric bundles were produced for this experiment.")
        return findings


def reset_report_store() -> None:
    """Test helper retained for backwards compatibility (no-op now)."""
    return None
