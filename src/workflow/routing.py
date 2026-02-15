# -----------------------------------------------------------------------------
# Workflow Routing
#
# Routing functions that determine the next node based on state.
# These implement the conditional edges in the workflow graph.
#
# Flow:
#   init → planning → discovery ←→ tools → deep_research ←→ tools
#                                              ↓
#                     reflection ←─────────────┘
#                         ↓ (sufficient?)
#                    pattern_extraction → synthesis → END
# -----------------------------------------------------------------------------

from typing import Literal
from state.schema import AgentState, ResearchPhase


# =============================================================================
# DISCOVERY PHASE ROUTING
# =============================================================================

def route_after_discovery(state: AgentState) -> Literal["discovery_tools", "deep_research"]:
    """
    Route after discovery node.
    - If agent requested tools -> go to discovery_tools
    - Otherwise -> proceed to deep_research
    """
    discovery_messages = state.get("discovery_messages", [])

    if not discovery_messages:
        return "deep_research"

    last_message = discovery_messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "discovery_tools"

    return "deep_research"


# =============================================================================
# DEEP RESEARCH PHASE ROUTING
# =============================================================================

def route_after_deep_research(state: AgentState) -> Literal["deep_research_tools", "deep_research", "reflection"]:
    """
    Route after deep_research node.
    - If agent requested tools -> go to deep_research_tools
    - If more apps to research -> loop back to deep_research
    - If all apps done -> go to reflection
    """
    deep_messages = state.get("deep_research_messages", [])
    apps = state.get("discovered_apps", [])
    current_index = state.get("current_app_index", 0)
    current_phase = state.get("current_phase")

    # Check if we should go to reflection
    if current_phase == ResearchPhase.REFLECTION:
        return "reflection"

    # Check for tool calls
    if deep_messages:
        last_message = deep_messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "deep_research_tools"

    # Check if more apps to research
    if current_index < len(apps):
        return "deep_research"

    return "reflection"


# =============================================================================
# REFLECTION PHASE ROUTING
# =============================================================================

def route_after_reflection(state: AgentState) -> Literal["discovery", "pattern_extraction"]:
    """
    Route after reflection node.
    - If research is insufficient -> back to discovery
    - If sufficient -> proceed to pattern_extraction
    """
    is_sufficient = state.get("is_research_sufficient", False)
    current_phase = state.get("current_phase")

    # If phase was set to discovery, go back to discovery
    if current_phase == ResearchPhase.DISCOVERY:
        return "discovery"

    # Default to pattern extraction if sufficient
    if is_sufficient:
        return "pattern_extraction"

    # If not sufficient but phase wasn't set to discovery, continue anyway
    return "pattern_extraction"


# =============================================================================
# GENERIC TOOL CHECK (for ToolNode edges)
# =============================================================================

def should_use_tools(state: AgentState) -> Literal["tools", "user_communication"]:
    """
    Legacy routing for old workflow.
    Check if the last AI message has tool calls.
    Routes to 'tools' if yes, 'user_communication' if no.
    """
    messages = state.get("messages", [])
    if not messages:
        return "user_communication"

    last_message = messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "user_communication"


def check_discovery_tools(state: AgentState) -> Literal["discovery_tools", "deep_research"]:
    """
    Check if discovery agent requested tools.
    """
    discovery_messages = state.get("discovery_messages", [])

    if not discovery_messages:
        return "deep_research"

    last_message = discovery_messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "discovery_tools"

    return "deep_research"


def check_deep_research_tools(state: AgentState) -> Literal["deep_research_tools", "check_more_apps"]:
    """
    Check if deep research agent requested tools.
    """
    deep_messages = state.get("deep_research_messages", [])

    if not deep_messages:
        return "check_more_apps"

    last_message = deep_messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "deep_research_tools"

    return "check_more_apps"


def check_more_apps_to_research(state: AgentState) -> Literal["deep_research", "reflection"]:
    """
    Check if there are more apps to research.
    """
    apps = state.get("discovered_apps", [])
    current_index = state.get("current_app_index", 0)
    current_phase = state.get("current_phase")

    # If phase is already reflection, go there
    if current_phase == ResearchPhase.REFLECTION:
        return "reflection"

    # If more apps to research
    if current_index < len(apps):
        return "deep_research"

    return "reflection"


def check_research_sufficient(state: AgentState) -> Literal["discovery", "pattern_extraction"]:
    """
    Check if research is sufficient after reflection.
    """
    is_sufficient = state.get("is_research_sufficient", False)
    current_phase = state.get("current_phase")

    if current_phase == ResearchPhase.DISCOVERY:
        return "discovery"

    if is_sufficient or current_phase == ResearchPhase.PATTERN_EXTRACTION:
        return "pattern_extraction"

    # Default to pattern extraction
    return "pattern_extraction"
