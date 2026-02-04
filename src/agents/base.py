import os
import time
from pydantic import BaseModel
from typing import List, Optional, Any, Callable
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import get_model_id


# Used in run_agent, to return structed results....
class AgentResults(BaseModel):
    success: bool
    output: Optional[Any] = None
    raw_output: Optional[str] = None
    error: Optional[str] = None
    agent_name: str = ""
    execution_time_ms: int = 0
    tool_calls: List[str] = []

# creating the client LLM -> gemini 3 pro
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


async def run_agent(
    agent_name: str,
    prompt: str,
    tools: Optional[List[Callable]] = None,
    model: str = "gemini-3-pro",
    system_prompt: Optional[str] = None,
    timeout_seconds: int = 60,
) -> AgentResults:
    start_time = time.time()

    try:
        llm = create_llm(model=model, tools=tools)

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        response = await llm.ainvoke(messages)

        elapsed_ms = int((time.time() - start_time) * 1000)

        return AgentResults(
            success=True,
            raw_output=response.content,
            output=response.content,
            agent_name=agent_name,
            execution_time_ms=elapsed_ms,
        )

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return AgentResults(
            success=False,
            error=str(e),
            agent_name=agent_name,
            execution_time_ms=elapsed_ms,
        )
