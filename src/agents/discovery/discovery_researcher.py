# -----------------------------------------------------------------------------
# Discovery Researcher Agent
#
# Finds app candidates from web searches.
# Uses scratchpad to track what's been searched and avoid redundancy.
#
# Usage in nodes:
#   from agents.discovery import DiscoveryResearcherAgent
#   agent = DiscoveryResearcherAgent()
#   result = await agent.run(state)
# -----------------------------------------------------------------------------

from agents.base import Agent, AgentResponse
from config import DISCOVERY_RESEARCHER


class DiscoveryResearcherAgent(Agent):
    """
    Agent for discovering indie app opportunities.
    Searches across multiple sources and compiles a list of app candidates.
    """

    def __init__(self):
        super().__init__(DISCOVERY_RESEARCHER)

    # Uses base class run() for multi-turn with tools
    # The scratchpad is injected into the prompt via the node
