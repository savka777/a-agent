# -----------------------------------------------------------------------------
# Workflow Helpers
#
# Utility functions for formatting data, parsing LLM responses,
# and managing the scratchpad across workflow phases.
# -----------------------------------------------------------------------------

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from state.schema import (
    SubQuery,
    AppOpportunity,
    ResearchScratchpad,
    Pattern,
)


# =============================================================================
# SCRATCHPAD FORMATTING
# =============================================================================

def format_scratchpad(scratchpad: ResearchScratchpad, apps: List[AppOpportunity] = None) -> str:
    """
    Format the scratchpad for injection into agent prompts.
    Shows what's been done to avoid redundancy.
    """
    lines = ["=== RESEARCH SCRATCHPAD ==="]

    # Executed queries
    if scratchpad.executed_queries:
        lines.append("\n📋 QUERIES ALREADY EXECUTED (don't repeat):")
        for q in scratchpad.executed_queries[-20:]:  # Last 20 queries
            lines.append(f"  - {q}")

    # Apps found so far
    if apps:
        lines.append(f"\n🎯 APPS FOUND SO FAR ({len(apps)} total):")
        for app in apps:
            status = "✅ deep researched" if app.research_complete else "⏳ needs deep research"
            lines.append(f"  - {app.name} ({app.category}) [{status}]")

    # Key findings
    if scratchpad.key_findings:
        lines.append("\n💡 KEY FINDINGS:")
        for finding in scratchpad.key_findings[-10:]:
            lines.append(f"  - {finding}")

    # Gaps identified
    if scratchpad.gaps_identified:
        lines.append("\n🕳️ GAPS TO FILL:")
        for gap in scratchpad.gaps_identified:
            lines.append(f"  - {gap}")

    lines.append(f"\n📊 Research iteration: {scratchpad.iteration_count}")

    return "\n".join(lines)


def format_app_scratchpad(app: AppOpportunity, queries_executed: List[str]) -> str:
    """
    Format scratchpad for deep research on a specific app.
    """
    lines = [f"=== SCRATCHPAD FOR {app.name} ==="]

    if queries_executed:
        lines.append("\n📋 QUERIES ALREADY EXECUTED FOR THIS APP:")
        for q in queries_executed:
            lines.append(f"  - {q}")

    if app.raw_research:
        lines.append("\n📝 DATA GATHERED SO FAR:")
        lines.append(app.raw_research[:2000])  # Truncate if too long

    return "\n".join(lines)


# =============================================================================
# PARSING LLM RESPONSES
# =============================================================================

def extract_json_from_response(content: str) -> Optional[Any]:
    """
    Extract JSON from LLM response that might contain markdown code blocks.
    """
    import logging
    logger = logging.getLogger("agents")

    # Try to find JSON in code blocks first
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            logger.warning(f"[json_extract] Code block JSON failed: {e}")
            logger.debug(f"[json_extract] Attempted to parse: {json_match.group(1)[:200]}...")

    # Try to parse the whole content as JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to find JSON array or object patterns
    for pattern in [r'\[[\s\S]*\]', r'\{[\s\S]*\}']:
        match = re.search(pattern, content)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as e:
                logger.debug(f"[json_extract] Pattern {pattern} failed: {e}")
                continue

    # Last resort: try to fix common LLM JSON issues
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
    if json_match:
        json_str = json_match.group(1)
        # Remove trailing commas before ] or }
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"[json_extract] Even after cleanup, JSON failed: {e}")

    logger.warning(f"[json_extract] No valid JSON found in response of length {len(content)}")
    return None


def parse_subqueries_from_response(content: str) -> List[SubQuery]:
    """
    Parse sub-queries from planner agent response.
    """
    data = extract_json_from_response(content)
    if not data or not isinstance(data, list):
        return []

    queries = []
    for item in data:
        if isinstance(item, dict) and "query" in item:
            queries.append(SubQuery(
                query=item.get("query", ""),
                purpose=item.get("purpose", ""),
            ))

    return queries


def parse_apps_from_response(content: str) -> List[AppOpportunity]:
    """
    Parse discovered apps from discovery agent response.
    """
    data = extract_json_from_response(content)
    if not data:
        return []

    # Handle both single object and array
    if isinstance(data, dict):
        data = [data]

    apps = []
    for item in data:
        if isinstance(item, dict) and "name" in item:
            # Get source URL if provided
            sources = []
            if item.get("source_url"):
                sources.append(item.get("source_url"))
            if item.get("sources"):
                sources.extend(item.get("sources", []))

            apps.append(AppOpportunity(
                name=item.get("name", ""),
                developer=item.get("developer", ""),
                category=item.get("category", ""),
                why_viral=item.get("why_interesting", item.get("description", "")),
                sources=sources,
            ))

    return apps


def update_app_with_research(app: AppOpportunity, content: str) -> AppOpportunity:
    """
    Update an app with data from deep research.
    """
    data = extract_json_from_response(content)
    if not data or not isinstance(data, dict):
        # Even without JSON, mark raw research
        app.raw_research += f"\n\n{content}"
        return app

    # Update fields from JSON
    app.developer = data.get("developer", app.developer)
    app.category = data.get("category", app.category)
    app.revenue_estimate = data.get("revenue_estimate", app.revenue_estimate)
    app.downloads_estimate = data.get("downloads_estimate", app.downloads_estimate)

    rating = data.get("rating")
    if rating:
        try:
            app.rating = float(rating)
        except (ValueError, TypeError):
            pass

    app.hook_feature = data.get("hook_feature", app.hook_feature)
    app.differentiation_angle = data.get("differentiation_angle", app.differentiation_angle)
    app.why_viral = data.get("why_viral", app.why_viral)
    app.growth_strategy = data.get("growth_strategy", app.growth_strategy)

    clone_diff = data.get("clone_difficulty")
    if clone_diff:
        try:
            app.clone_difficulty = int(clone_diff)
        except (ValueError, TypeError):
            pass

    app.mvp_features = data.get("mvp_features", app.mvp_features)
    app.skip_features = data.get("skip_features", app.skip_features)
    app.clone_lessons = data.get("clone_lessons", app.clone_lessons)
    app.sources = data.get("sources", app.sources)
    app.research_complete = True

    return app


def parse_reflection_response(content: str) -> Dict[str, Any]:
    """
    Parse reflection agent response.
    """
    data = extract_json_from_response(content)
    if not data or not isinstance(data, dict):
        return {
            "is_sufficient": False,
            "apps_needing_more_research": [],
            "suggested_queries": [],
            "reasoning": "Failed to parse reflection response",
        }

    return {
        "is_sufficient": data.get("is_sufficient", False),
        "apps_needing_more_research": data.get("apps_needing_more_research", []),
        "suggested_queries": data.get("suggested_queries", []),
        "reasoning": data.get("reasoning", ""),
    }


def parse_patterns_response(content: str) -> tuple[List[Pattern], List[str], Dict[str, str]]:
    """
    Parse pattern extractor response.
    Returns: (patterns, gaps, best_opportunities)
    """
    data = extract_json_from_response(content)
    if not data or not isinstance(data, dict):
        return [], [], {}

    patterns = []
    for p in data.get("patterns", []):
        if isinstance(p, dict):
            patterns.append(Pattern(
                name=p.get("name", ""),
                description=p.get("description", ""),
                examples=p.get("examples", []),
                how_to_apply=p.get("how_to_apply", ""),
            ))

    gaps = data.get("gaps", [])
    best_opportunities = data.get("best_opportunities", {})

    return patterns, gaps, best_opportunities


# =============================================================================
# FORMATTING FOR AGENTS
# =============================================================================

def format_research_plan(plan: List[SubQuery]) -> str:
    """
    Format research plan for discovery agent.
    """
    lines = ["=== RESEARCH PLAN ==="]
    lines.append("Execute these queries to find indie app opportunities:\n")

    for i, sq in enumerate(plan, 1):
        status = "✅" if sq.executed else "⏳"
        lines.append(f"{status} {i}. {sq.query}")
        lines.append(f"   Purpose: {sq.purpose}")

    return "\n".join(lines)


def format_research_summary(apps: List[AppOpportunity]) -> str:
    """
    Format all apps for reflection agent evaluation.
    """
    lines = [f"=== RESEARCH SUMMARY ({len(apps)} apps) ===\n"]

    for app in apps:
        lines.append(f"## {app.name}")
        lines.append(f"Developer: {app.developer or 'Unknown'}")
        lines.append(f"Category: {app.category or 'Unknown'}")
        lines.append(f"Revenue: {app.revenue_estimate or 'Unknown'}")
        lines.append(f"Downloads: {app.downloads_estimate or 'Unknown'}")
        lines.append(f"Rating: {app.rating or 'Unknown'}")
        lines.append(f"Hook Feature: {app.hook_feature or 'Not identified'}")
        lines.append(f"Why Viral: {app.why_viral or 'Not identified'}")
        lines.append(f"Clone Difficulty: {app.clone_difficulty or 'Not rated'}/5")
        lines.append(f"Research Complete: {'Yes' if app.research_complete else 'No'}")
        lines.append("")

    return "\n".join(lines)


def format_all_apps_for_patterns(apps: List[AppOpportunity]) -> str:
    """
    Format all apps for pattern extraction.
    Includes full detail for pattern analysis.
    """
    lines = [f"=== ALL RESEARCHED APPS ({len(apps)} total) ===\n"]

    for app in apps:
        lines.append(f"## {app.name}")
        lines.append(f"**Developer:** {app.developer}")
        lines.append(f"**Category:** {app.category}")
        lines.append(f"**Revenue Estimate:** {app.revenue_estimate}")
        lines.append(f"**Downloads:** {app.downloads_estimate}")
        lines.append(f"**Rating:** {app.rating}")
        lines.append(f"**Hook Feature:** {app.hook_feature}")
        lines.append(f"**Differentiation:** {app.differentiation_angle}")
        lines.append(f"**Why Viral:** {app.why_viral}")
        lines.append(f"**Growth Strategy:** {app.growth_strategy}")
        lines.append(f"**Clone Difficulty:** {app.clone_difficulty}/5")
        lines.append(f"**MVP Features:** {', '.join(app.mvp_features) if app.mvp_features else 'N/A'}")
        lines.append(f"**Skip Features:** {', '.join(app.skip_features) if app.skip_features else 'N/A'}")
        lines.append(f"**Clone Lessons:** {app.clone_lessons}")
        if app.sources:
            lines.append(f"**Sources:** {', '.join(app.sources)}")
        lines.append("")

    return "\n".join(lines)


def format_patterns_for_synthesis(patterns: List[Pattern], gaps: List[str]) -> tuple[str, str]:
    """
    Format patterns and gaps for synthesis agent.
    Returns: (patterns_text, gaps_text)
    """
    pattern_lines = []
    for p in patterns:
        pattern_lines.append(f"### {p.name}")
        pattern_lines.append(p.description)
        if p.examples:
            pattern_lines.append(f"Examples: {', '.join(p.examples)}")
        if p.how_to_apply:
            pattern_lines.append(f"How to apply: {p.how_to_apply}")
        pattern_lines.append("")

    gap_lines = []
    for g in gaps:
        gap_lines.append(f"- {g}")

    return "\n".join(pattern_lines), "\n".join(gap_lines)


# =============================================================================
# DEFAULT QUERIES (fallback if planner fails)
# =============================================================================

def generate_default_queries(categories: List[str]) -> List[SubQuery]:
    """
    Generate default research queries if planner fails.
    """
    from datetime import date
    today = date.today()
    month = today.strftime("%B")
    year = today.year

    queries = []

    for category in categories:
        # Discovery queries
        queries.extend([
            SubQuery(
                query=f"{category} apps trending reddit {month} {year}",
                purpose="Find viral apps from Reddit"
            ),
            SubQuery(
                query=f"viral {category} app TikTok {year}",
                purpose="Find TikTok viral apps"
            ),
            SubQuery(
                query=f"indie {category} app success story {year}",
                purpose="Find indie success stories"
            ),
        ])

        # Ecosystem queries
        queries.extend([
            SubQuery(
                query=f"best {category} apps comparison {year}",
                purpose="Understand the landscape"
            ),
            SubQuery(
                query=f"Product Hunt {category} launches this week",
                purpose="Find new launches"
            ),
        ])

        # Opportunity queries
        queries.extend([
            SubQuery(
                query=f"{category} app complaints reddit",
                purpose="Find user pain points"
            ),
        ])

    return queries[:12]  # Cap at 12 queries


# =============================================================================
# JSON OUTPUT BUILDER
# =============================================================================

def build_json_output(
    mode: str,
    categories: List[str],
    apps: List[AppOpportunity],
    patterns: List[Pattern],
    gaps: List[str],
    best_opportunities: Dict[str, str],
) -> Dict[str, Any]:
    """
    Build the final JSON output structure.
    """
    from datetime import date

    # Convert apps to dict format
    opportunities = []
    for app in apps:
        opportunities.append({
            "name": app.name,
            "developer": app.developer,
            "category": app.category,
            "revenue_estimate": app.revenue_estimate,
            "downloads_estimate": app.downloads_estimate,
            "rating": app.rating,
            "clone_difficulty": app.clone_difficulty,
            "opportunity_score": app.opportunity_score,
            "hook_feature": app.hook_feature,
            "differentiation_angle": app.differentiation_angle,
            "why_viral": app.why_viral,
            "mvp_features": app.mvp_features,
            "skip_features": app.skip_features,
            "trend_timing": app.trend_timing,
            "sources": app.sources,
        })

    # Convert patterns to dict format
    pattern_list = []
    for p in patterns:
        pattern_list.append({
            "name": p.name,
            "description": p.description,
            "examples": p.examples,
            "how_to_apply": p.how_to_apply,
        })

    return {
        "mode": mode,
        "niche": ", ".join(categories),
        "run_date": date.today().isoformat(),
        "opportunities": opportunities,
        "patterns": pattern_list,
        "gaps": gaps,
        "best_opportunities": best_opportunities,
    }
