from typing import TypedDict, Annotated, List, Dict, Any
from operator import add
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    user_request: str
    messages: Annotated[List[BaseMessage], add_messages]
    research_outputs: str
    errors: Annotated[List[str], add]
    retry_count: int
    output_to_user: str
    current_stage: str


def create_init_state(user_request: str) -> AgentState:
    return AgentState(
        user_request=user_request,
        messages=[],
        research_outputs="",
        errors=[],
        retry_count=0,
        output_to_user="",
        current_stage="",
    )
