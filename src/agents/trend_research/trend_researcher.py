# -----------------------------------------------------------------------------
# Trend Research Agent
#
# This agent handles App Store trend research.
# It uses web search tools to find trending apps and compile reports.
#
# Usage in nodes:
#   from agents.trend_research import TrendResearchAgent
#   agent = TrendResearchAgent()
#   result = await agent.run(state)
# -----------------------------------------------------------------------------

from agents.base import Agent, AgentResponse
from config import APP_TRENDS_ANALYZER


class TrendResearchAgent(Agent):
    """
    Agent for researching App Store trends.
    Uses the APP_TRENDS_ANALYZER config which includes web search tools.
    """

    def __init__(self):
        super().__init__(APP_TRENDS_ANALYZER)

    # -------------------------------------------------------------------------
    # Override run() if you need custom behavior for this specific agent.
    # For now, the base class run() handles everything we need.
    # -------------------------------------------------------------------------

    # Example of how you might add custom behavior:
    #
    # async def run(self, state, input_key="user_request", messages_key="messages"):
    #     # custom pre-processing here
    #     result = await super().run(state, input_key, messages_key)
    #     # custom post-processing here
    #     return result
