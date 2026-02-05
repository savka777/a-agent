# -----------------------------------------------------------------------------
# Workflow Nodes
#
# Nodes are thin orchestration layers. They:
#   1. Instantiate or use agents
#   2. Call agent.run(state)
#   3. Return state updates
#
# All the LLM logic (message building, tool checking, etc.) lives in the Agent
# base class. This keeps nodes clean and focused on orchestration.
# -----------------------------------------------------------------------------

from typing import Dict, Any
from state.schema import AgentState
from agents.trend_research import TrendResearchAgent
from agents.user_communicator import UserCommunicatorAgent


# -----------------------------------------------------------------------------
# Agent Instances
#
# Create agents once at module level so they can be reused across calls.
# Each agent is initialized with its config (model, tools, system prompt).
# -----------------------------------------------------------------------------
trend_research_agent = TrendResearchAgent()
user_communicator_agent = UserCommunicatorAgent()


# -----------------------------------------------------------------------------
# init_node
# Entry point for the workflow. Sets up initial state.
# -----------------------------------------------------------------------------
async def init_node(state: AgentState) -> Dict[str, Any]:
    # state is passed by langgraph but not needed here
    _ = state
    return {
        "current_stage": "init_complete"
    }


# -----------------------------------------------------------------------------
# research_node
#
# Uses the TrendResearchAgent to research app trends.
# The agent handles all the LLM logic internally.
#
# Flow:
#   - First call: agent builds messages with system prompt + user request
#   - Continuation: agent uses existing messages from state
#   - If response has tool calls: return messages only (tools node will execute)
#   - If no tool calls: return messages + research_outputs (done researching)
# -----------------------------------------------------------------------------
async def research_node(state: AgentState) -> Dict[str, Any]:
    # run the agent - all LLM logic is encapsulated inside
    result = await trend_research_agent.run(state)

    # if agent requested tool calls, just update messages
    # the routing function will send us to the tools node
    if result.has_tool_calls:
        return {"messages": result.messages}

    # no tool calls means research is complete
    # update messages and store the research output
    return {
        "messages": result.messages,
        "research_outputs": result.content
    }


# -----------------------------------------------------------------------------
# user_output_node
#
# Uses the UserCommunicatorAgent to format research into a user briefing.
# This is a simple one-shot call (no tools, no multi-turn).
# -----------------------------------------------------------------------------
async def user_output_node(state: AgentState) -> Dict[str, Any]:
    research_outputs = state.get("research_outputs", "")

    # handle empty research output
    if not research_outputs:
        print("user_output_node: received empty research output")
        return {"output_to_user": "No research data available."}

    try:
        # use the convenience method for formatting
        result = await user_communicator_agent.format_research(research_outputs)
        return {"output_to_user": result.content}

    except Exception as e:
        print("user_output_node error:", e)
        return {"output_to_user": "Failed to generate output."}


# -----------------------------------------------------------------------------
# Example: Multi-Agent Node
#
# This shows how clean a node with multiple agents would look.
# Each agent call is just one line - no LLM boilerplate repeated.
#
# async def complex_analysis_node(state: AgentState) -> Dict[str, Any]:
#     # run multiple agents in sequence
#     research = await trend_research_agent.run(state)
#
#     # pass research output to another agent
#     analysis = await analysis_agent.run_simple(research.content)
#
#     # and another
#     summary = await summary_agent.run_simple(analysis.content)
#
#     return {
#         "research_outputs": research.content,
#         "analysis": analysis.content,
#         "summary": summary.content,
#     }
# -----------------------------------------------------------------------------
