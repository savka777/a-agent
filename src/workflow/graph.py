# -----------------------------------------------------------------------------
# Workflow Graph
#
# Defines the LangGraph state machine for deep research.
#
# Flow:
#   init → planning → discovery ←→ discovery_tools
#                         ↓
#                    deep_research ←→ deep_research_tools
#                         ↓
#                    reflection
#                    ↓ (sufficient?)
#        (no) ← discovery    or    pattern_extraction → (yes)
#                                        ↓
#                                    synthesis → END
# -----------------------------------------------------------------------------

import os
from typing import List

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from state.schema import AgentState, ResearchPhase, create_init_state
from agents.tools import DISCOVERY_TOOLS, DEEP_RESEARCH_TOOLS, RESEARCH_TOOLS

from workflow.nodes import (
    init_node,
    planning_node,
    discovery_node,
    deep_research_node,
    reflection_node,
    pattern_extraction_node,
    synthesis_node,
    # Legacy nodes
    research_node,
    user_output_node,
)
from workflow.routing import (
    route_after_discovery,
    route_after_deep_research,
    route_after_reflection,
    check_discovery_tools,
    check_deep_research_tools,
    check_more_apps_to_research,
    check_research_sufficient,
    # Legacy routing
    should_use_tools,
)

# Optional: Braintrust logging
try:
    from braintrust import init_logger
    from braintrust_langchain import BraintrustCallbackHandler, set_global_handler

    def setup_braintrust():
        api_key = os.getenv("BRAINTRUST_API_KEY")
        if api_key:
            init_logger(project="alphy-deep-research", api_key=api_key)
            handler = BraintrustCallbackHandler()
            set_global_handler(handler)
except ImportError:
    def setup_braintrust():
        pass


# =============================================================================
# TOOL NODE WRAPPER FUNCTIONS
# These wrap ToolNode to use phase-specific message keys
# =============================================================================

# Create tool nodes once
_discovery_tool_node = ToolNode(DISCOVERY_TOOLS)
_deep_research_tool_node = ToolNode(DEEP_RESEARCH_TOOLS)


async def discovery_tools_node(state: AgentState):
    """
    Execute tools for discovery phase.
    Maps discovery_messages to/from the standard messages key.
    """
    # Get discovery messages
    messages = state.get("discovery_messages", [])

    if not messages:
        return {"discovery_messages": []}

    # Create a temporary state with messages for ToolNode
    temp_state = {"messages": messages}

    # Run the ToolNode
    result = await _discovery_tool_node.ainvoke(temp_state)

    # Map back to discovery_messages
    return {"discovery_messages": result.get("messages", [])}


async def deep_research_tools_node(state: AgentState):
    """
    Execute tools for deep research phase.
    Maps deep_research_messages to/from the standard messages key.
    """
    # Get deep research messages
    messages = state.get("deep_research_messages", [])

    if not messages:
        return {"deep_research_messages": []}

    # Create a temporary state with messages for ToolNode
    temp_state = {"messages": messages}

    # Run the ToolNode
    result = await _deep_research_tool_node.ainvoke(temp_state)

    # Map back to deep_research_messages
    return {"deep_research_messages": result.get("messages", [])}


# =============================================================================
# DEEP RESEARCH GRAPH
# =============================================================================

def create_deep_research_graph() -> StateGraph:
    """
    Create the deep research workflow graph.

    Flow:
    init → planning → discovery ←→ discovery_tools
                          ↓
                     deep_research ←→ deep_research_tools
                          ↓
                     reflection
                     ↓ (sufficient?)
         (no) ← discovery    or    pattern_extraction → (yes)
                                         ↓
                                     synthesis → END
    """
    setup_braintrust()

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("init", init_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("discovery", discovery_node)
    workflow.add_node("discovery_tools", discovery_tools_node)
    workflow.add_node("deep_research", deep_research_node)
    workflow.add_node("deep_research_tools", deep_research_tools_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("pattern_extraction", pattern_extraction_node)
    workflow.add_node("synthesis", synthesis_node)

    # Set entry point
    workflow.set_entry_point("init")

    # Linear edges
    workflow.add_edge("init", "planning")
    workflow.add_edge("planning", "discovery")

    # Discovery phase: discovery ←→ discovery_tools
    workflow.add_conditional_edges(
        "discovery",
        check_discovery_tools,
        {
            "discovery_tools": "discovery_tools",
            "deep_research": "deep_research",
        }
    )
    workflow.add_edge("discovery_tools", "discovery")

    # Deep research phase: deep_research ←→ deep_research_tools → check more apps
    workflow.add_conditional_edges(
        "deep_research",
        check_deep_research_tools,
        {
            "deep_research_tools": "deep_research_tools",
            "check_more_apps": "check_more_apps",
        }
    )
    workflow.add_edge("deep_research_tools", "deep_research")

    # Add a virtual node for checking if more apps need research
    workflow.add_node("check_more_apps", lambda state: {})
    workflow.add_conditional_edges(
        "check_more_apps",
        check_more_apps_to_research,
        {
            "deep_research": "deep_research",
            "reflection": "reflection",
        }
    )

    # Reflection phase: either back to discovery or to pattern extraction
    workflow.add_conditional_edges(
        "reflection",
        check_research_sufficient,
        {
            "discovery": "discovery",
            "pattern_extraction": "pattern_extraction",
        }
    )

    # Final phases
    workflow.add_edge("pattern_extraction", "synthesis")
    workflow.add_edge("synthesis", END)

    return workflow


# =============================================================================
# LEGACY GRAPH (for backwards compatibility)
# =============================================================================

def create_app_graph() -> StateGraph:
    """
    Legacy graph for simple research workflow.
    init → research ←→ tools → user_communication → END
    """
    setup_braintrust()

    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("init", init_node)
    workflow.add_node("research", research_node)
    workflow.add_node("tools", ToolNode(RESEARCH_TOOLS))
    workflow.add_node("user_communication", user_output_node)

    # Edges
    workflow.set_entry_point("init")
    workflow.add_edge("init", "research")
    workflow.add_conditional_edges("research", should_use_tools)
    workflow.add_edge("tools", "research")
    workflow.add_edge("user_communication", END)

    return workflow


# =============================================================================
# COMPILATION
# =============================================================================

# Cache compiled graphs
_deep_research_graph = None
_legacy_graph = None


def get_deep_research_graph():
    """Get or create the deep research graph."""
    global _deep_research_graph
    if _deep_research_graph is None:
        graph = create_deep_research_graph()
        _deep_research_graph = graph.compile()
    return _deep_research_graph


def get_compiled_graph():
    """Get or create the legacy graph."""
    global _legacy_graph
    if _legacy_graph is None:
        graph = create_app_graph()
        _legacy_graph = graph.compile()
    return _legacy_graph


# Legacy aliases
compile_workflow = lambda: create_app_graph().compile()
compiled_graph = None


# =============================================================================
# WORKFLOW EXECUTION
# =============================================================================

async def run_workflow(
    categories: List[str],
    mode: str = "general",
    debug: bool = False,
) -> AgentState:
    """
    Run the deep research workflow.

    Args:
        categories: List of app categories to research
        mode: "general" or "targeted"
        debug: Enable verbose logging

    Returns:
        Final state with output_to_user and json_output
    """
    initial_state = create_init_state(
        categories=categories,
        mode=mode,
        debug=debug,
    )

    graph = get_deep_research_graph()

    if debug:
        print(graph.get_graph().draw_ascii())

    final_state = await graph.ainvoke(initial_state)
    return final_state


async def run_legacy_workflow(user_query: str) -> AgentState:
    """
    Run the legacy simple research workflow.
    Kept for backwards compatibility.
    """
    from state.schema import AgentState as LegacyState

    initial_state = {
        "user_request": user_query,
        "messages": [],
        "research_outputs": "",
        "errors": [],
        "retry_count": 0,
        "output_to_user": "",
        "categories": [],
        "mode": "legacy",
        "discovery_messages": [],
        "deep_research_messages": [],
        "current_phase": ResearchPhase.INIT,
        "research_plan": [],
        "discovered_apps": [],
        "current_app_index": 0,
        "scratchpad": None,
        "is_research_sufficient": False,
        "reflection_feedback": "",
        "apps_needing_more_research": [],
        "cross_app_patterns": [],
        "gaps": [],
        "json_output": {},
        "debug": False,
    }

    graph = get_compiled_graph()
    print(graph.get_graph().draw_ascii())

    final_state = await graph.ainvoke(initial_state)
    return final_state
