# -----------------------------------------------------------------------------
# User Communicator Agent
#
# This agent formats research outputs into user-friendly briefings.
# It takes raw research data and presents it in a clean, readable format.
#
# Usage in nodes:
#   from agents.user_communicator import UserCommunicatorAgent
#   agent = UserCommunicatorAgent()
#   result = await agent.run_simple(research_data)
# -----------------------------------------------------------------------------

from agents.base import Agent, AgentResponse
from config import USER_COMMUNICATOR


class UserCommunicatorAgent(Agent):
    """
    Agent for formatting research outputs for the user.
    Uses the USER_COMMUNICATOR config (no tools, just formatting).
    """

    def __init__(self):
        super().__init__(USER_COMMUNICATOR)

    async def format_research(self, research_output: str) -> AgentResponse:
        """
        Convenience method for formatting research output.
        Uses run_simple since this is a one-shot call without state management.

        Args:
            research_output: Raw research data from the trend researcher

        Returns:
            AgentResponse with the formatted briefing
        """
        if not research_output:
            # return a response indicating no data
            return AgentResponse(
                messages=[],
                content="No research data available.",
                has_tool_calls=False,
                is_first_call=True,
            )

        return await self.run_simple(research_output)
