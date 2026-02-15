# -----------------------------------------------------------------------------
# Workflow Nodes
#
# Nodes are orchestration layers that:
#   1. Instantiate or use agents
#   2. Call agent methods
#   3. Return state updates
#
# The new deep research workflow has these phases:
#   init → planning → discovery ←→ tools → deep_research ←→ tools
#                                              ↓
#                     reflection ←─────────────┘
#                         ↓ (sufficient?)
#                    pattern_extraction → synthesis → END
# -----------------------------------------------------------------------------

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage

from state.schema import (
    AgentState,
    ResearchPhase,
    SubQuery,
    AppOpportunity,
    ResearchScratchpad,
)
from agents import logger
from agents.planner import PlannerAgent
from agents.discovery import DiscoveryResearcherAgent
from agents.deep_research import DeepResearcherAgent
from agents.reflection import ReflectionAgent
from agents.pattern_extraction import PatternExtractorAgent
from agents.synthesis import SynthesisAgent
from workflow.helpers import (
    format_scratchpad,
    format_app_scratchpad,
    format_research_plan,
    format_research_summary,
    format_all_apps_for_patterns,
    format_patterns_for_synthesis,
    parse_subqueries_from_response,
    parse_apps_from_response,
    update_app_with_research,
    parse_reflection_response,
    parse_patterns_response,
    generate_default_queries,
    build_json_output,
)


# -----------------------------------------------------------------------------
# Agent Instances
# Lazy initialization to avoid errors when API keys aren't set yet
# -----------------------------------------------------------------------------
_planner_agent = None
_discovery_agent = None
_deep_research_agent = None
_reflection_agent = None
_pattern_extractor_agent = None
_synthesis_agent = None


def get_planner_agent():
    global _planner_agent
    if _planner_agent is None:
        _planner_agent = PlannerAgent()
    return _planner_agent


def get_discovery_agent():
    global _discovery_agent
    if _discovery_agent is None:
        _discovery_agent = DiscoveryResearcherAgent()
    return _discovery_agent


def get_deep_research_agent():
    global _deep_research_agent
    if _deep_research_agent is None:
        _deep_research_agent = DeepResearcherAgent()
    return _deep_research_agent


def get_reflection_agent():
    global _reflection_agent
    if _reflection_agent is None:
        _reflection_agent = ReflectionAgent()
    return _reflection_agent


def get_pattern_extractor_agent():
    global _pattern_extractor_agent
    if _pattern_extractor_agent is None:
        _pattern_extractor_agent = PatternExtractorAgent()
    return _pattern_extractor_agent


def get_synthesis_agent():
    global _synthesis_agent
    if _synthesis_agent is None:
        _synthesis_agent = SynthesisAgent()
    return _synthesis_agent


# -----------------------------------------------------------------------------
# init_node
# Entry point - sets up initial state for the deep research workflow
# -----------------------------------------------------------------------------
async def init_node(state: AgentState) -> Dict[str, Any]:
    """Initialize the workflow with categories from CLI."""
    logger.info("[init] Starting deep research workflow")
    logger.info(f"[init] Categories: {state.get('categories', [])}")
    logger.info(f"[init] Mode: {state.get('mode', 'general')}")

    return {
        "current_phase": ResearchPhase.PLANNING,
        "scratchpad": ResearchScratchpad(),
    }


# -----------------------------------------------------------------------------
# planning_node
# Generates sub-queries from categories using the planner agent
# -----------------------------------------------------------------------------
async def planning_node(state: AgentState) -> Dict[str, Any]:
    """Generate research plan from categories."""
    categories = state.get("categories", [])
    logger.info(f"[planning] Generating plan for {len(categories)} categories")

    try:
        result = await get_planner_agent().plan_research(categories)
        queries = parse_subqueries_from_response(result.content)

        if not queries:
            logger.warning("[planning] Planner returned no queries, using defaults")
            queries = generate_default_queries(categories)

        logger.info(f"[planning] Generated {len(queries)} sub-queries")

        return {
            "research_plan": queries,
            "current_phase": ResearchPhase.DISCOVERY,
        }

    except Exception as e:
        logger.error(f"[planning] Error: {e}")
        return {
            "research_plan": generate_default_queries(categories),
            "current_phase": ResearchPhase.DISCOVERY,
            "errors": [f"Planning error: {str(e)}"],
        }


# -----------------------------------------------------------------------------
# discovery_node
# Executes the research plan to find app candidates
# -----------------------------------------------------------------------------
async def discovery_node(state: AgentState) -> Dict[str, Any]:
    """Execute discovery research to find apps."""
    plan = state.get("research_plan", [])
    scratchpad = state.get("scratchpad", ResearchScratchpad())
    existing_apps = state.get("discovered_apps", [])
    discovery_messages = state.get("discovery_messages", [])

    logger.info(f"[discovery] Starting with {len(existing_apps)} existing apps, {len(discovery_messages)} messages")

    # Check if this is first call or continuation
    is_first_call = len(discovery_messages) == 0

    # Check if we have tool results that need processing
    has_tool_results = False
    if discovery_messages:
        # Check if last message is a tool result
        last_msg = discovery_messages[-1]
        if hasattr(last_msg, 'type') and last_msg.type == 'tool':
            has_tool_results = True
        elif hasattr(last_msg, 'name'):  # ToolMessage has a name attribute
            has_tool_results = True

    if is_first_call:
        # Build the initial prompt with plan and scratchpad
        plan_text = format_research_plan(plan)
        scratchpad_text = format_scratchpad(scratchpad, existing_apps)

        prompt = f"""{plan_text}

{scratchpad_text}

INSTRUCTIONS:
1. Execute 3-5 searches from the plan above using the available tools
2. After each search, analyze the results for indie/viral apps
3. When you have found 8-10 promising apps, output your findings as JSON

Start by executing the first search query."""

        result = await get_discovery_agent().run({
            "user_request": prompt,
            "messages": [],
        })
    elif has_tool_results:
        # After tool results, prompt agent to continue or compile
        logger.info("[discovery] Processing tool results")

        # Add a follow-up message to guide the agent
        follow_up = HumanMessage(content="""Good, I received the search results above.

Please do ONE of the following:
1. If you need more data, execute another search query from the plan
2. If you have enough data (found 8+ indie apps), compile your findings into JSON format:
```json
[
  {"name": "AppName", "developer": "Dev", "category": "cat", "description": "...", "why_interesting": "..."}
]
```

What would you like to do?""")

        messages_with_followup = discovery_messages + [follow_up]

        result = await get_discovery_agent().run({
            "user_request": "",
            "messages": messages_with_followup,
        })
    else:
        # Regular continuation
        result = await get_discovery_agent().run({
            "user_request": "",
            "messages": discovery_messages,
        })

    # Check for tool calls
    if result.has_tool_calls:
        logger.info("[discovery] Agent requesting tools")
        return {
            "discovery_messages": result.messages,
            "current_phase": ResearchPhase.DISCOVERY,
        }

    # No tool calls - try to parse discovered apps
    new_apps = parse_apps_from_response(result.content)
    logger.info(f"[discovery] Found {len(new_apps)} new apps from agent response")

    # If no apps found but we have tool results, try to extract from message history
    if not new_apps and discovery_messages:
        logger.info("[discovery] Attempting to extract apps from tool results")
        new_apps = extract_apps_from_messages(discovery_messages)
        logger.info(f"[discovery] Extracted {len(new_apps)} apps from message history")

    # Update scratchpad with executed queries
    updated_scratchpad = ResearchScratchpad(
        executed_queries=scratchpad.executed_queries + [q.query for q in plan if not q.executed],
        key_findings=scratchpad.key_findings,
        gaps_identified=scratchpad.gaps_identified,
        iteration_count=scratchpad.iteration_count + 1,
    )

    return {
        "discovered_apps": new_apps,
        "scratchpad": updated_scratchpad,
        "discovery_messages": result.messages,
        "current_phase": ResearchPhase.DEEP_RESEARCH,
    }


def extract_apps_from_messages(messages) -> List[AppOpportunity]:
    """
    Extract app names and URLs from tool result messages as a fallback.
    Looks for app names mentioned in search results along with their source URLs.
    """
    apps = []
    app_names_found = set()

    for msg in messages:
        content = ""
        if hasattr(msg, 'content'):
            if isinstance(msg.content, str):
                content = msg.content
            elif isinstance(msg.content, list):
                content = " ".join(str(c) for c in msg.content)

        # Parse search results which have Title/URL/Content format
        current_url = ""
        lines = content.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()

            # Capture URL for the current result
            if line.startswith('URL:') or line.startswith('Source:'):
                current_url = line.split(':', 1)[1].strip() if ':' in line else ""

            # Look for "Title:" lines from search results
            if line.startswith('Title:'):
                title = line.replace('Title:', '').strip()

                # Extract potential app name (first part before common separators)
                for sep in [' - ', ' | ', ' : ', ' – ', ' — ']:
                    if sep in title:
                        potential_name = title.split(sep)[0].strip()
                        # Filter out generic terms
                        skip_terms = [
                            'the', 'best', 'top', 'new', 'app', 'apps', 'review',
                            'download', 'free', 'how', 'what', 'why', '2024', '2025', '2026'
                        ]
                        if len(potential_name) > 2 and potential_name.lower() not in skip_terms:
                            if potential_name not in app_names_found:
                                app_names_found.add(potential_name)
                                apps.append(AppOpportunity(
                                    name=potential_name,
                                    why_viral="Found in trending search results",
                                    sources=[current_url] if current_url else [],
                                ))
                        break

    return apps[:15]  # Limit to 15 apps


# -----------------------------------------------------------------------------
# deep_research_node
# Deep dives on ONE app at a time
# -----------------------------------------------------------------------------
async def deep_research_node(state: AgentState) -> Dict[str, Any]:
    """Deep research on the current app."""
    apps = state.get("discovered_apps", [])
    current_index = state.get("current_app_index", 0)
    scratchpad = state.get("scratchpad", ResearchScratchpad())
    deep_messages = state.get("deep_research_messages", [])

    # Check if we've researched all apps
    if current_index >= len(apps):
        logger.info("[deep_research] All apps researched, moving to reflection")
        return {
            "current_phase": ResearchPhase.REFLECTION,
            "deep_research_messages": [],  # Clear for next round
        }

    current_app = apps[current_index]
    is_first_call = len(deep_messages) == 0

    logger.info(f"[deep_research] Researching app {current_index + 1}/{len(apps)}: {current_app.name}")

    if is_first_call:
        # Start fresh research on this app
        scratchpad_text = format_app_scratchpad(current_app, [])

        result = await get_deep_research_agent().research_app(
            app_name=current_app.name,
            app_description=current_app.why_viral,
            scratchpad_text=scratchpad_text,
        )
    else:
        # Continue with existing messages (after tool execution)
        result = await get_deep_research_agent().run({
            "user_request": "",
            "messages": deep_messages,
        })

    # Check for tool calls
    if result.has_tool_calls:
        logger.info(f"[deep_research] Agent requesting tools for {current_app.name}")
        return {
            "deep_research_messages": result.messages,
            "current_phase": ResearchPhase.DEEP_RESEARCH,
        }

    # No tool calls - update app with research and move to next
    updated_app = update_app_with_research(current_app, result.content)

    # Create updated apps list
    updated_apps = apps.copy()
    updated_apps[current_index] = updated_app

    logger.info(f"[deep_research] Completed research on {current_app.name}")

    return {
        "discovered_apps": updated_apps,
        "current_app_index": current_index + 1,
        "deep_research_messages": [],  # Clear for next app
        "current_phase": ResearchPhase.DEEP_RESEARCH,  # Loop to next app
    }


# -----------------------------------------------------------------------------
# reflection_node
# Evaluates if research is sufficient
# -----------------------------------------------------------------------------
async def reflection_node(state: AgentState) -> Dict[str, Any]:
    """Evaluate research quality and decide if more is needed."""
    apps = state.get("discovered_apps", [])
    scratchpad = state.get("scratchpad", ResearchScratchpad())

    logger.info(f"[reflection] Evaluating {len(apps)} apps")

    # Format research summary for evaluation
    summary = format_research_summary(apps)

    try:
        result = await get_reflection_agent().evaluate(summary)
        evaluation = parse_reflection_response(result.content)

        is_sufficient = evaluation.get("is_sufficient", False)
        apps_needing_research = evaluation.get("apps_needing_more_research", [])
        suggested_queries = evaluation.get("suggested_queries", [])
        reasoning = evaluation.get("reasoning", "")

        logger.info(f"[reflection] Sufficient: {is_sufficient}, Reasoning: {reasoning[:100]}")

        # If not sufficient and we haven't iterated too many times, go back to discovery
        if not is_sufficient and scratchpad.iteration_count < 3:
            logger.info("[reflection] Research insufficient, requesting more discovery")

            # Add suggested queries to the plan
            new_queries = [SubQuery(query=q, purpose="fill gap") for q in suggested_queries]

            return {
                "is_research_sufficient": False,
                "reflection_feedback": reasoning,
                "apps_needing_more_research": apps_needing_research,
                "research_plan": new_queries,
                "scratchpad": ResearchScratchpad(
                    executed_queries=scratchpad.executed_queries,
                    key_findings=scratchpad.key_findings,
                    gaps_identified=apps_needing_research,
                    iteration_count=scratchpad.iteration_count + 1,
                ),
                "current_phase": ResearchPhase.DISCOVERY,
                "discovery_messages": [],  # Clear for new round
            }

        # Research is sufficient or we've iterated enough
        return {
            "is_research_sufficient": True,
            "reflection_feedback": reasoning,
            "current_phase": ResearchPhase.PATTERN_EXTRACTION,
        }

    except Exception as e:
        logger.error(f"[reflection] Error: {e}")
        # On error, proceed anyway
        return {
            "is_research_sufficient": True,
            "reflection_feedback": f"Error during reflection: {str(e)}",
            "errors": [f"Reflection error: {str(e)}"],
            "current_phase": ResearchPhase.PATTERN_EXTRACTION,
        }


# -----------------------------------------------------------------------------
# pattern_extraction_node
# Finds patterns across all apps
# -----------------------------------------------------------------------------
async def pattern_extraction_node(state: AgentState) -> Dict[str, Any]:
    """Extract patterns from all researched apps."""
    apps = state.get("discovered_apps", [])

    logger.info(f"[pattern_extraction] Analyzing {len(apps)} apps for patterns")

    # Format all apps for pattern analysis
    apps_summary = format_all_apps_for_patterns(apps)

    try:
        result = await get_pattern_extractor_agent().extract_patterns(apps_summary)
        patterns, gaps, best_opportunities = parse_patterns_response(result.content)

        logger.info(f"[pattern_extraction] Found {len(patterns)} patterns, {len(gaps)} gaps")

        return {
            "cross_app_patterns": patterns,
            "gaps": gaps,
            "current_phase": ResearchPhase.SYNTHESIS,
        }

    except Exception as e:
        logger.error(f"[pattern_extraction] Error: {e}")
        return {
            "cross_app_patterns": [],
            "gaps": [],
            "errors": [f"Pattern extraction error: {str(e)}"],
            "current_phase": ResearchPhase.SYNTHESIS,
        }


# -----------------------------------------------------------------------------
# synthesis_node
# Produces the final report
# -----------------------------------------------------------------------------
async def synthesis_node(state: AgentState) -> Dict[str, Any]:
    """Synthesize all research into final report."""
    apps = state.get("discovered_apps", [])
    patterns = state.get("cross_app_patterns", [])
    gaps = state.get("gaps", [])
    categories = state.get("categories", [])
    mode = state.get("mode", "general")

    logger.info("[synthesis] Creating final report")

    # Format data for synthesis
    apps_summary = format_all_apps_for_patterns(apps)
    patterns_text, gaps_text = format_patterns_for_synthesis(patterns, gaps)

    try:
        result = await get_synthesis_agent().synthesize(
            apps_summary=apps_summary,
            patterns_data=patterns_text,
            gaps_data=gaps_text,
        )

        # Build JSON output
        json_output = build_json_output(
            mode=mode,
            categories=categories,
            apps=apps,
            patterns=patterns,
            gaps=gaps,
            best_opportunities={},  # Extracted during pattern phase
        )

        logger.info("[synthesis] Report complete")

        return {
            "output_to_user": result.content,
            "json_output": json_output,
            "current_phase": ResearchPhase.SYNTHESIS,
        }

    except Exception as e:
        logger.error(f"[synthesis] Error: {e}")
        return {
            "output_to_user": f"Error generating report: {str(e)}",
            "json_output": {},
            "errors": [f"Synthesis error: {str(e)}"],
        }


# -----------------------------------------------------------------------------
# Legacy nodes (for backwards compatibility)
# -----------------------------------------------------------------------------
from agents.trend_research import TrendResearchAgent
from agents.user_communicator import UserCommunicatorAgent

_trend_research_agent = None
_user_communicator_agent = None


def get_trend_research_agent():
    global _trend_research_agent
    if _trend_research_agent is None:
        _trend_research_agent = TrendResearchAgent()
    return _trend_research_agent


def get_user_communicator_agent():
    global _user_communicator_agent
    if _user_communicator_agent is None:
        _user_communicator_agent = UserCommunicatorAgent()
    return _user_communicator_agent


async def research_node(state: AgentState) -> Dict[str, Any]:
    """Legacy research node for old workflow."""
    result = await get_trend_research_agent().run(state)

    if result.has_tool_calls:
        return {"messages": result.messages}

    return {
        "messages": result.messages,
        "research_outputs": result.content
    }


async def user_output_node(state: AgentState) -> Dict[str, Any]:
    """Legacy output node for old workflow."""
    research_outputs = state.get("research_outputs", "")

    if not research_outputs:
        return {"output_to_user": "No research data available."}

    try:
        result = await get_user_communicator_agent().format_research(research_outputs)
        return {"output_to_user": result.content}
    except Exception as e:
        logger.error(f"user_output_node error: {e}")
        return {"output_to_user": "Failed to generate output."}
