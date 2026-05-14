"""Typed API request/response schemas (Pydantic v2)."""

from apps.api.schemas.agent import (
    AgentReferenceItem,
    ResearchPlanRequest,
    ResearchPlanResponse,
    ResearchReportRequest,
    ResearchReportResponse,
)
from apps.api.schemas.common import ErrorResponse, PaginatedResponse
from apps.api.schemas.compare import CompareRequest, CompareResponse, CompareRow
from apps.api.schemas.datasets import (
    DatasetImportHFRequest,
    DatasetManifest,
    DatasetPreviewResponse,
    DatasetSchemaMapping,
    TaskLane,
)
from apps.api.schemas.experiments import (
    ExperimentCreateRequest,
    ExperimentResult,
    ExperimentStatus,
    ExperimentStatusResponse,
    ExperimentSummary,
    GenerationParams,
    SamplingConfig,
)
from apps.api.schemas.reports import ReportMeta, ReportPayload

__all__ = [
    "AgentReferenceItem",
    "CompareRequest",
    "CompareResponse",
    "CompareRow",
    "DatasetImportHFRequest",
    "DatasetManifest",
    "DatasetPreviewResponse",
    "DatasetSchemaMapping",
    "ErrorResponse",
    "ExperimentCreateRequest",
    "ExperimentResult",
    "ExperimentStatus",
    "ExperimentStatusResponse",
    "ExperimentSummary",
    "GenerationParams",
    "PaginatedResponse",
    "ReportMeta",
    "ReportPayload",
    "ResearchPlanRequest",
    "ResearchPlanResponse",
    "ResearchReportRequest",
    "ResearchReportResponse",
    "SamplingConfig",
    "TaskLane",
]
