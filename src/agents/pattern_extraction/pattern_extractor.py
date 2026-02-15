# -----------------------------------------------------------------------------
# Pattern Extractor Agent
#
# Finds patterns across all researched apps.
# Identifies what works, what's missing, and best opportunities.
#
# Usage in nodes:
#   from agents.pattern_extraction import PatternExtractorAgent
#   agent = PatternExtractorAgent()
#   result = await agent.extract_patterns(apps_summary)
# -----------------------------------------------------------------------------

from agents.base import Agent, AgentResponse
from config import PATTERN_EXTRACTOR


class PatternExtractorAgent(Agent):
    """
    Agent for extracting cross-app patterns.
    Analyzes trends, gaps, and opportunities across all researched apps.
    """

    def __init__(self):
        super().__init__(PATTERN_EXTRACTOR)

    async def extract_patterns(self, apps_summary: str) -> AgentResponse:
        """
        Extract patterns from all researched apps.

        Args:
            apps_summary: Formatted summary of all apps with their data

        Returns:
            AgentResponse with JSON patterns, gaps, and best opportunities
        """
        prompt = f"Analyze these apps and extract patterns:\n\n{apps_summary}"
        return await self.run_simple(prompt)
