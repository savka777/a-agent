# -----------------------------------------------------------------------------
# Deep Researcher Agent
#
# Goes deep on ONE app at a time.
# Researches revenue, differentiation, growth strategy, and clone difficulty.
#
# Usage in nodes:
#   from agents.deep_research import DeepResearcherAgent
#   agent = DeepResearcherAgent()
#   result = await agent.run(state)
# -----------------------------------------------------------------------------

from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage
from agents.base import Agent, AgentResponse, create_llm, logger
from config import DEEP_RESEARCHER


class DeepResearcherAgent(Agent):
    """
    Agent for deep research on a specific app.
    Gets revenue data, differentiation angles, and clone lessons.
    """

    def __init__(self):
        super().__init__(DEEP_RESEARCHER)

    def get_prompt_for_app(self, app_name: str, scratchpad_text: str = "") -> str:
        """
        Generate a customized system prompt for researching a specific app.
        """
        base_prompt = self.config.system_prompt.replace(
            "[APP_NAME_PLACEHOLDER]",
            app_name
        )

        if scratchpad_text:
            base_prompt += f"\n\n--- SCRATCHPAD ---\n{scratchpad_text}"

        return base_prompt

    async def research_app(
        self,
        app_name: str,
        app_description: str = "",
        scratchpad_text: str = "",
    ) -> AgentResponse:
        """
        Start deep research on a specific app.

        Args:
            app_name: Name of the app to research
            app_description: Brief description (if known)
            scratchpad_text: Formatted scratchpad with prior searches

        Returns:
            AgentResponse with first LLM call results
        """
        system_prompt = self.get_prompt_for_app(app_name, scratchpad_text)

        user_input = f"Research this app: {app_name}"
        if app_description:
            user_input += f"\n\nKnown info: {app_description}"

        logger.info(f"[{self.name}] starting research on: {app_name}")

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input),
        ]

        response = await self.llm.ainvoke(messages)

        has_tool_calls = False
        if hasattr(response, "tool_calls") and response.tool_calls:
            has_tool_calls = True
            tool_names = [tc.get("name", "unknown") for tc in response.tool_calls]
            logger.info(f"[{self.name}] requesting tools: {tool_names}")

        from agents.base import extract_text_content
        content = extract_text_content(response.content)

        return AgentResponse(
            messages=messages + [response],
            content=content,
            has_tool_calls=has_tool_calls,
            is_first_call=True,
        )
