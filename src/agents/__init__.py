# -----------------------------------------------------------------------------
# Agents Package
#
# This package contains all agents used in the workflow.
# Each agent encapsulates its own LLM logic and can be called with agent.run()
#
# Usage:
#   from agents import TrendResearchAgent, UserCommunicatorAgent
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
from agents.trend_research import TrendResearchAgent
from agents.user_communicator import UserCommunicatorAgent

__all__ = [
    "Agent",
    "AgentResponse",
    "create_llm",
    "logger",
    "setup_logger",
    "print_markdown",
    "extract_text_content",
    "TrendResearchAgent",
    "UserCommunicatorAgent",
]
