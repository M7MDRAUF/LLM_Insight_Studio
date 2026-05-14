"""AI research agent: tools, report writer, and orchestrator."""

from services.agent.references import (
    DEFAULT_REFERENCES,
    curate_references,
    validate_references,
)
from services.agent.report_writer import render_report_markdown
from services.agent.research_agent import ResearchAgent
from services.agent.tools import AGENT_TOOLS, AgentTool

__all__ = [
    "AGENT_TOOLS",
    "DEFAULT_REFERENCES",
    "AgentTool",
    "ResearchAgent",
    "curate_references",
    "render_report_markdown",
    "validate_references",
]
