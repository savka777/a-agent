# -----------------------------------------------------------------------------
# Planner Agent
#
# Decomposes research goals into targeted sub-queries.
# Takes categories and produces a list of specific searches to execute.
#
# Usage in nodes:
#   from agents.planner import PlannerAgent
#   agent = PlannerAgent()
#   result = await agent.run_simple(categories_text)
# -----------------------------------------------------------------------------

from agents.base import Agent, AgentResponse
from config import PLANNER_AGENT


class PlannerAgent(Agent):
    """
    Agent for planning research queries.
    Decomposes high-level categories into specific sub-queries for discovery.
    """

    def __init__(self):
        super().__init__(PLANNER_AGENT)

    async def plan_research(self, categories: list[str]) -> AgentResponse:
        """
        Generate a research plan for the given categories.

        Args:
            categories: List of app categories to research

        Returns:
            AgentResponse with JSON-formatted sub-queries
        """
        categories_text = ", ".join(categories)
        prompt = f"Generate research sub-queries for these app categories: {categories_text}"
        return await self.run_simple(prompt)
