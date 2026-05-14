"""Research agent routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.api.core.deps import get_research_agent
from apps.api.schemas.agent import (
    ResearchPlanRequest,
    ResearchPlanResponse,
    ResearchReportRequest,
    ResearchReportResponse,
)
from services.agent.research_agent import ResearchAgent

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/plan", response_model=ResearchPlanResponse)
def plan(
    payload: ResearchPlanRequest,
    agent: ResearchAgent = Depends(get_research_agent),
) -> ResearchPlanResponse:
    return agent.build_plan(payload)


@router.post("/report", response_model=ResearchReportResponse, status_code=201)
def report(
    payload: ResearchReportRequest,
    agent: ResearchAgent = Depends(get_research_agent),
) -> ResearchReportResponse:
    return agent.write_report(payload)
