from typing import TypedDict, Annotated, List, Dict, Any, Optional
from dataclasses import dataclass, field
from operator import add
from enum import Enum
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


# -----------------------------------------------------------------------------
# Research Phase Enum
# Tracks where we are in the deep research pipeline
# -----------------------------------------------------------------------------
class ResearchPhase(str, Enum):
    INIT = "init"
    PLANNING = "planning"
    DISCOVERY = "discovery"
    DEEP_RESEARCH = "deep_research"
    REFLECTION = "reflection"
    PATTERN_EXTRACTION = "pattern_extraction"
    SYNTHESIS = "synthesis"


# -----------------------------------------------------------------------------
# SubQuery - A planned search query
# -----------------------------------------------------------------------------
@dataclass
class SubQuery:
    query: str
    purpose: str  # e.g., "find viral apps", "get revenue data"
    executed: bool = False
    results: str = ""


# -----------------------------------------------------------------------------
# AppOpportunity - Structured data for a single app
# -----------------------------------------------------------------------------
@dataclass
class AppOpportunity:
    name: str
    developer: str = ""
    category: str = ""
    revenue_estimate: str = ""
    downloads_estimate: str = ""
    rating: float = 0.0
    review_count: int = 0
    clone_difficulty: int = 0  # 1-5 scale
    opportunity_score: float = 0.0
    hook_feature: str = ""
    differentiation_angle: str = ""
    why_viral: str = ""
    growth_strategy: str = ""
    mvp_features: List[str] = field(default_factory=list)
    skip_features: List[str] = field(default_factory=list)
    trend_timing: str = ""  # rising, stable, declining
    clone_lessons: str = ""
    sources: List[str] = field(default_factory=list)
    raw_research: str = ""  # raw research data for this app
    research_complete: bool = False


# -----------------------------------------------------------------------------
# ResearchScratchpad - Tracks what's been searched to avoid redundancy
# -----------------------------------------------------------------------------
@dataclass
class ResearchScratchpad:
    executed_queries: List[str] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    gaps_identified: List[str] = field(default_factory=list)
    iteration_count: int = 0


# -----------------------------------------------------------------------------
# Pattern - Cross-app pattern extracted during analysis
# -----------------------------------------------------------------------------
@dataclass
class Pattern:
    name: str
    description: str
    examples: List[str] = field(default_factory=list)
    how_to_apply: str = ""


# -----------------------------------------------------------------------------
# Custom reducers for accumulating lists
# -----------------------------------------------------------------------------
def add_apps(existing: List[AppOpportunity], new: List[AppOpportunity]) -> List[AppOpportunity]:
    """Reducer that accumulates apps, avoiding duplicates by name."""
    if not existing:
        existing = []
    if not new:
        return existing
    existing_names = {app.name.lower() for app in existing}
    for app in new:
        if app.name.lower() not in existing_names:
            existing.append(app)
            existing_names.add(app.name.lower())
    return existing


def merge_scratchpad(existing: ResearchScratchpad, new: ResearchScratchpad) -> ResearchScratchpad:
    """Reducer that merges scratchpad state."""
    if not existing:
        return new if new else ResearchScratchpad()
    if not new:
        return existing

    return ResearchScratchpad(
        executed_queries=existing.executed_queries + [q for q in new.executed_queries if q not in existing.executed_queries],
        key_findings=existing.key_findings + [f for f in new.key_findings if f not in existing.key_findings],
        gaps_identified=new.gaps_identified if new.gaps_identified else existing.gaps_identified,
        iteration_count=max(existing.iteration_count, new.iteration_count),
    )


# -----------------------------------------------------------------------------
# AgentState - The full state schema for the deep research workflow
# -----------------------------------------------------------------------------
class AgentState(TypedDict):
    # Core workflow state
    user_request: str
    categories: List[str]  # Selected categories to research
    mode: str  # "targeted" or "general"

    # Message history for LLM context
    messages: Annotated[List[BaseMessage], add_messages]

    # Phase-specific message histories (for parallel deep research)
    discovery_messages: Annotated[List[BaseMessage], add_messages]
    deep_research_messages: Annotated[List[BaseMessage], add_messages]

    # Current workflow phase
    current_phase: ResearchPhase

    # Planning output
    research_plan: List[SubQuery]

    # Discovery output
    discovered_apps: Annotated[List[AppOpportunity], add_apps]

    # Deep research tracking
    current_app_index: int  # Which app we're currently researching
    scratchpad: Annotated[ResearchScratchpad, merge_scratchpad]

    # Reflection output
    is_research_sufficient: bool
    reflection_feedback: str
    apps_needing_more_research: List[str]

    # Pattern extraction output
    cross_app_patterns: List[Pattern]
    gaps: List[str]

    # Final outputs
    output_to_user: str  # Markdown report
    json_output: Dict[str, Any]  # Structured JSON output

    # Error handling
    errors: Annotated[List[str], add]
    retry_count: int

    # Debug logging
    debug: bool


# -----------------------------------------------------------------------------
# Factory function to create initial state
# -----------------------------------------------------------------------------
def create_init_state(
    categories: List[str],
    mode: str = "general",
    debug: bool = False,
) -> AgentState:
    """Create initial state for the deep research workflow."""
    return AgentState(
        user_request="",
        categories=categories,
        mode=mode,
        messages=[],
        discovery_messages=[],
        deep_research_messages=[],
        current_phase=ResearchPhase.INIT,
        research_plan=[],
        discovered_apps=[],
        current_app_index=0,
        scratchpad=ResearchScratchpad(),
        is_research_sufficient=False,
        reflection_feedback="",
        apps_needing_more_research=[],
        cross_app_patterns=[],
        gaps=[],
        output_to_user="",
        json_output={},
        errors=[],
        retry_count=0,
        debug=debug,
    )
