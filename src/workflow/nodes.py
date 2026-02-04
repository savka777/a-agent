from state.schema import AgentState
from agents.base import create_llm
from config import APP_TRENDS_ANALYZER, USER_COMMUNICATOR
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any


async def init_node(state: AgentState) -> Dict[str, Any]:
    return {
        'current_stage': 'init_complete'
    }

# research node, uses apps trend analyzer
async def research_node(state: AgentState) -> Dict[str, Any]:
    # get config parameters
    MODEL = APP_TRENDS_ANALYZER.model
    TOOLS = APP_TRENDS_ANALYZER.tools
    SYS_PROMPT = APP_TRENDS_ANALYZER.system_prompt

    # create client
    llm = create_llm(MODEL, TOOLS)

    # check state, IF state is empty, this is first call
    messages = state.get('messages', [])
    first_call = not messages

    # first call - build initial messages
    if first_call: # not False = true
        messages = [
            SystemMessage(content=SYS_PROMPT),
            HumanMessage(content=state.get('user_request', 'What is the top trending apps today?')),
        ]

    # call LLM to get response
    response = await llm.ainvoke(messages)

    # on first call, include initial messages; otherwise just append the response
    if first_call:
        new_messages = messages + [response]
    else:
        new_messages = [response] # has reducer so this is fine (check schema for messages and below return statement)

    # check if response was not a tool call, will call tool node otherwise
    if not response.tool_calls:
        return {
            'messages': new_messages,
            'research_outputs': response.content
        }

    return {'messages': new_messages}

async def user_output_node(state: AgentState) -> Dict[str, Any]:
    MODEL = USER_COMMUNICATOR.model
    SYS_PROMPT = USER_COMMUNICATOR.system_prompt

    research_outputs = state.get('research_outputs', '')

    if not research_outputs:
        print('user node received empty research output')
        return {'output_to_user': 'No research data available.'}

    try:
        llm = create_llm(MODEL, tools=None)

        # ainvoke expects messages, not a raw string
        messages = [
            SystemMessage(content=SYS_PROMPT),
            HumanMessage(content=research_outputs),
        ]
        response = await llm.ainvoke(messages)

        return {'output_to_user': response.content}

    except Exception as e:
        print('user node error:', e)
        return {'output_to_user': 'Failed to generate output.'}
        
