# -----------------------------------------------------------------------------
# Reflection Agent
#
# Evaluates if the current research is sufficient.
# Checks app count, data quality, and identifies gaps.
#
# Usage in nodes:
#   from agents.reflection import ReflectionAgent
#   agent = ReflectionAgent()
#   result = await agent.evaluate(research_summary)
# -----------------------------------------------------------------------------

from agents.base import Agent, AgentResponse
from config import REFLECTION_AGENT


class ReflectionAgent(Agent):
    """
    Agent for evaluating research quality.
    Determines if we have enough data to produce a good report.
    """

    def __init__(self):
        super().__init__(REFLECTION_AGENT)

    async def evaluate(self, research_summary: str) -> AgentResponse:
        """
        Evaluate the current state of research.

        Args:
            research_summary: Formatted summary of all apps and their data

        Returns:
            AgentResponse with JSON evaluation
        """
        prompt = f"Evaluate this research:\n\n{research_summary}"
        return await self.run_simple(prompt)
