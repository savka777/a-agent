import os
import logging
from typing import List, Optional, Any, Callable
from dataclasses import dataclass
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from config.settings import get_model_id


# -----------------------------------------------------------------------------
# Logger Setup
#
# Simple logger that outputs to stdout with timestamps.
# Usage: logger.info("message"), logger.debug("message"), etc.
# -----------------------------------------------------------------------------
def setup_logger(name: str = "agents", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)

    # avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # create stdout handler
    handler = logging.StreamHandler()
    handler.setLevel(level)

    # format: [timestamp] [level] [name] message
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# global logger instance
logger = setup_logger()


# -----------------------------------------------------------------------------
# print_markdown - pretty print markdown in the console
#
# Uses the rich library to render markdown with colors, formatting, etc.
# -----------------------------------------------------------------------------
def print_markdown(text: str, title: str = None) -> None:
    """
    Pretty print markdown text in the console.
    Uses rich library for colors and formatting.

    Args:
        text: Markdown text to print
        title: Optional title to display above the markdown
    """
    try:
        from rich.console import Console
        from rich.markdown import Markdown
        from rich.panel import Panel

        # force_terminal=True ensures colors work in all environments
        console = Console(force_terminal=True)

        md = Markdown(text)

        if title:
            # wrap in a panel with title and green border
            console.print(Panel(md, title=title, border_style="green"))
        else:
            console.print(md)

        # add spacing after output
        console.print()

    except ImportError:
        # fallback if rich is not installed
        if title:
            print(f"\n=== {title} ===\n")
        print(text)


# -----------------------------------------------------------------------------
# extract_text_content - helper to get plain text from LLM responses
#
# Gemini sometimes returns structured content blocks like:
#   [{'type': 'text', 'text': '...', 'extras': {'signature': '...'}}]
#
# This function extracts just the text, handling both string and list formats.
# -----------------------------------------------------------------------------
def extract_text_content(content) -> str:
    """
    Extract plain text from LLM response content.
    Handles both string responses and structured content blocks.
    """
    # if it's already a string, return it
    if isinstance(content, str):
        return content

    # if it's a list of content blocks, extract text from each
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict):
                # get 'text' field from structured block
                if "text" in block:
                    text_parts.append(block["text"])
            elif isinstance(block, str):
                text_parts.append(block)
        return "\n".join(text_parts)

    # fallback: convert to string
    return str(content) if content else ""


# -----------------------------------------------------------------------------
# Response object returned by Agent.run()
# Contains everything the node needs to update state
# -----------------------------------------------------------------------------
@dataclass
class AgentResponse:
    messages: List[BaseMessage]      # full message history including response
    content: str                      # the text content of the response
    has_tool_calls: bool              # whether response contains tool calls
    is_first_call: bool               # whether this was the first call (for debugging)


# -----------------------------------------------------------------------------
# create_llm - factory function for creating LLM client
# kept separate so it can be used standalone if needed
# -----------------------------------------------------------------------------
def create_llm(
    model: str = "gemini-3-pro",
    tools: Optional[List[Callable]] = None,
) -> ChatGoogleGenerativeAI:
    model_id = get_model_id(model)

    llm = ChatGoogleGenerativeAI(
        model=model_id,
        google_api_key=os.environ.get("GEMINI_API_KEY"),
    )

    if tools:
        llm = llm.bind_tools(tools)

    return llm


# -----------------------------------------------------------------------------
# Agent Base Class
#
# This is the core abstraction. Each agent:
#   - Has a config (model, tools, system prompt)
#   - Knows how to run itself (handles message building, LLM calls)
#   - Returns a clean AgentResponse for the node to use
#
# Nodes become thin orchestration layers that just call agent.run()
# -----------------------------------------------------------------------------
class Agent:
    def __init__(self, config: Any):
        """
        Initialize agent with config.
        Config should have: model, tools, system_prompt, name
        """
        self.config = config
        self.name = config.name
        self.llm = create_llm(config.model, config.tools)
        logger.debug(f"[{self.name}] initialized with model: {config.model}")

    async def run(
        self,
        state: dict,
        input_key: str = "user_request",
        messages_key: str = "messages",
    ) -> AgentResponse:
        """
        Main entry point for running the agent.

        Handles:
          - First call vs continuation (checks if messages exist in state)
          - Building message list with system prompt
          - Calling the LLM
          - Packaging response

        Args:
            state: The current workflow state dict
            input_key: Which state key to use for user input (default: "user_request")
            messages_key: Which state key holds message history (default: "messages")

        Returns:
            AgentResponse with messages, content, and tool call info
        """
        # check if this is first call or continuation
        existing_messages = state.get(messages_key, [])
        is_first_call = len(existing_messages) == 0

        if is_first_call:
            logger.info(f"[{self.name}] starting (first call)")
        else:
            logger.info(f"[{self.name}] continuing (message count: {len(existing_messages)})")

        # build messages based on whether first call or not
        if is_first_call:
            messages = self._build_initial_messages(state, input_key)
        else:
            messages = existing_messages

        # call the LLM
        logger.debug(f"[{self.name}] calling LLM...")
        response = await self.llm.ainvoke(messages)
        logger.debug(f"[{self.name}] LLM response received")

        # build the new message list
        if is_first_call:
            new_messages = messages + [response]
        else:
            # just the response - state has a reducer that will append
            new_messages = [response]

        # check for tool calls
        has_tool_calls = False
        if hasattr(response, "tool_calls") and response.tool_calls:
            has_tool_calls = True
            tool_names = [tc.get("name", "unknown") for tc in response.tool_calls]
            logger.info(f"[{self.name}] requesting tools: {tool_names}")

        # get content (might be empty string if tool call)
        # use helper to extract text from structured content blocks
        content = extract_text_content(response.content)

        if not has_tool_calls:
            # truncate content for logging
            preview = content[:100] + "..." if len(content) > 100 else content
            logger.info(f"[{self.name}] completed with response: {preview}")

        return AgentResponse(
            messages=new_messages,
            content=content,
            has_tool_calls=has_tool_calls,
            is_first_call=is_first_call,
        )

    def _build_initial_messages(self, state: dict, input_key: str) -> List[BaseMessage]:
        """
        Build the initial message list for first call.
        Includes system prompt and user input.
        """
        user_input = state.get(input_key, "")

        messages = [
            SystemMessage(content=self.config.system_prompt),
            HumanMessage(content=user_input),
        ]

        return messages

    async def run_simple(
        self,
        input_text: str,
        system_prompt_override: Optional[str] = None,
    ) -> AgentResponse:
        """
        Simplified run for one-shot calls without state management.
        Useful for agents that don't need multi-turn conversation.

        Args:
            input_text: The input to send to the LLM
            system_prompt_override: Optional override for system prompt

        Returns:
            AgentResponse with the result
        """
        logger.info(f"[{self.name}] run_simple called")

        system_prompt = system_prompt_override or self.config.system_prompt

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=input_text),
        ]

        logger.debug(f"[{self.name}] calling LLM...")
        response = await self.llm.ainvoke(messages)

        has_tool_calls = False
        if hasattr(response, "tool_calls") and response.tool_calls:
            has_tool_calls = True

        # use helper to extract text from structured content blocks
        content = extract_text_content(response.content)

        preview = content[:100] + "..." if len(content) > 100 else content
        logger.info(f"[{self.name}] run_simple completed: {preview}")

        return AgentResponse(
            messages=messages + [response],
            content=content,
            has_tool_calls=has_tool_calls,
            is_first_call=True,
        )
