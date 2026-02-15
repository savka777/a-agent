# -----------------------------------------------------------------------------
# Synthesis Agent
#
# Produces the final Reddit-post-quality report.
# Transforms research data into actionable insights.
#
# Usage in nodes:
#   from agents.synthesis import SynthesisAgent
#   agent = SynthesisAgent()
#   result = await agent.synthesize(data)
# -----------------------------------------------------------------------------

from agents.base import Agent, AgentResponse
from config import SYNTHESIS_AGENT


class SynthesisAgent(Agent):
    """
    Agent for synthesizing research into a final report.
    Creates a comprehensive, actionable report for entrepreneurs.
    """

    def __init__(self):
        super().__init__(SYNTHESIS_AGENT)

    async def synthesize(
        self,
        apps_summary: str,
        patterns_data: str,
        gaps_data: str,
    ) -> AgentResponse:
        """
        Synthesize all research into a final report.

        Args:
            apps_summary: Formatted summary of all apps
            patterns_data: Extracted patterns
            gaps_data: Market gaps identified

        Returns:
            AgentResponse with the final markdown report
        """
        prompt = f"""Create a comprehensive report from this research:

## APPS RESEARCHED
{apps_summary}

## PATTERNS IDENTIFIED
{patterns_data}

## MARKET GAPS
{gaps_data}

Transform this into a Reddit-post-quality report with actionable insights."""

        return await self.run_simple(prompt)
