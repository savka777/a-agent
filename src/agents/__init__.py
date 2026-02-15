# -----------------------------------------------------------------------------
# Agents Package
#
# This package contains all agents used in the workflow.
# Each agent encapsulates its own LLM logic and can be called with agent.run()
#
# Usage:
#   from agents import PlannerAgent, DiscoveryResearcherAgent
#   from agents.base import Agent, AgentResponse
# -----------------------------------------------------------------------------

from agents.base import (
    Agent,
    AgentResponse,
    create_llm,
    logger,
    setup_logger,
    print_markdown,
    extract_text_content,
)

# New deep research agents
from agents.planner import PlannerAgent
from agents.discovery import DiscoveryResearcherAgent
from agents.deep_research import DeepResearcherAgent
from agents.reflection import ReflectionAgent
from agents.pattern_extraction import PatternExtractorAgent
from agents.synthesis import SynthesisAgent

# Legacy agents
from agents.trend_research import TrendResearchAgent
from agents.user_communicator import UserCommunicatorAgent

__all__ = [
    # Base classes
    "Agent",
    "AgentResponse",
    "create_llm",
    "logger",
    "setup_logger",
    "print_markdown",
    "extract_text_content",
    # New agents
    "PlannerAgent",
    "DiscoveryResearcherAgent",
    "DeepResearcherAgent",
    "ReflectionAgent",
    "PatternExtractorAgent",
    "SynthesisAgent",
    # Legacy agents
    "TrendResearchAgent",
    "UserCommunicatorAgent",
]
