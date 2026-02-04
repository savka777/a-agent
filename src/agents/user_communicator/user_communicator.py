from config import USER_COMMUNICATOR
from agents.base import run_agent, AgentResults


# async def run_user_communicator(
#     research_output: str,
# ) -> AgentResults:

#     prompt = (
#         "Here is the raw research data from today's App Store trend analysis:\n\n"
#         f"{research_output}\n\n"
#         "Format this into a clean, concise daily briefing for the user."
#     )

#     results = await run_agent(
#         agent_name=USER_COMMUNICATOR.name,
#         prompt=prompt,
#         tools=USER_COMMUNICATOR.tools,
#         system_prompt=USER_COMMUNICATOR.system_prompt,
#         timeout_seconds=USER_COMMUNICATOR.timeout_seconds,
#     )

#     return results
