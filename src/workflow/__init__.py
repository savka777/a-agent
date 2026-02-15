# -----------------------------------------------------------------------------
# Workflow Package
#
# Contains the LangGraph workflow definition, nodes, routing, and helpers.
# -----------------------------------------------------------------------------

from workflow.graph import (
    # New deep research workflow
    create_deep_research_graph,
    get_deep_research_graph,
    run_workflow,
    # Legacy workflow
    create_app_graph,
    compile_workflow,
    get_compiled_graph,
    run_legacy_workflow,
)

from workflow.nodes import (
    # New nodes
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
    should_use_tools,
)

from workflow.logging import (
    AlphyLogger,
    get_logger,
    set_debug,
)

__all__ = [
    # Graph
    "create_deep_research_graph",
    "get_deep_research_graph",
    "run_workflow",
    "create_app_graph",
    "compile_workflow",
    "get_compiled_graph",
    "run_legacy_workflow",
    # Nodes
    "init_node",
    "planning_node",
    "discovery_node",
    "deep_research_node",
    "reflection_node",
    "pattern_extraction_node",
    "synthesis_node",
    "research_node",
    "user_output_node",
    # Routing
    "route_after_discovery",
    "route_after_deep_research",
    "route_after_reflection",
    "check_discovery_tools",
    "check_deep_research_tools",
    "check_more_apps_to_research",
    "check_research_sufficient",
    "should_use_tools",
    # Logging
    "AlphyLogger",
    "get_logger",
    "set_debug",
]
