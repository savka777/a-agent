from state.schema import AgentState


def should_use_tools(state: AgentState) -> str:
    """Check if the last AI message has tool calls.
    Routes to 'tools' if yes, 'user_communication' if no."""

    messages = state.get('messages', [])
    if not messages:
        return 'user_communication'

    last_message = messages[-1]

    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return 'tools'

    return 'user_communication'
