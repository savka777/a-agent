import os
from typing import List, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from tavily import TavilyClient


# =============================================================================
# OUTPUT SCHEMAS
# These define the structure for agent outputs via tool calls
# =============================================================================

class DiscoveredApp(BaseModel):
    """Schema for an app discovered during research."""
    name: str = Field(description="The app name")
    developer: str = Field(default="", description="Developer or company name")
    category: str = Field(default="", description="App category")
    description: str = Field(default="", description="What the app does")
    why_interesting: str = Field(default="", description="Why this app is worth researching")
    source_url: str = Field(default="", description="URL where you found this app")


class AppResearch(BaseModel):
    """Schema for deep research on a single app."""
    name: str = Field(description="The app name")
    developer: str = Field(default="", description="Developer or company name")
    category: str = Field(default="", description="App category")
    revenue_estimate: str = Field(default="unknown", description="Revenue estimate e.g. '$50K/month'")
    downloads_estimate: str = Field(default="unknown", description="Download estimate e.g. '100K+'")
    rating: Optional[float] = Field(default=None, description="App store rating")
    hook_feature: str = Field(default="", description="The killer feature that makes users choose this")
    differentiation_angle: str = Field(default="", description="How a clone could differentiate")
    why_viral: str = Field(default="", description="Why/how it went viral")
    growth_strategy: str = Field(default="", description="How they acquired users")
    clone_difficulty: int = Field(default=3, description="1-5 scale, 1=easy 5=hard")
    mvp_features: List[str] = Field(default_factory=list, description="Must-have features for MVP")
    skip_features: List[str] = Field(default_factory=list, description="Features to skip in clone")
    clone_lessons: str = Field(default="", description="Key insight for building a competitor")
    sources: List[str] = Field(default_factory=list, description="URLs where you found this info")


# Lazy initialization to avoid errors when API key isn't set yet
_tavily_client = None


def get_tavily_client() -> TavilyClient:
    """Get or create the Tavily client."""
    global _tavily_client
    if _tavily_client is None:
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set")
        _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client


# =============================================================================
# CORE WEB SEARCH TOOL
# =============================================================================
@tool
def web_search(query: str) -> str:
    """Search the web for current information. Use this to find
    trending apps, App Store charts, app rankings, and app news."""

    response = get_tavily_client().search(
        query=query,
        max_results=10,
        search_depth="advanced",
    )

    results = []
    for r in response.get("results", []):
        results.append(
            f"Title: {r['title']}\n"
            f"URL: {r['url']}\n"
            f"Content: {r['content']}\n"
        )

    return "\n---\n".join(results) if results else "No results found."


# =============================================================================
# APP STORE SEARCH TOOL
# Uses Tavily to search for App Store specific info
# =============================================================================
@tool
def app_store_search(query: str) -> str:
    """Search for App Store information about an app. Use this to find
    app rankings, ratings, reviews, developer info, and App Store page details.
    Add 'App Store' or 'iOS app' to your query for best results."""

    # Enhance query for App Store results
    enhanced_query = f"{query} App Store iOS app"

    response = get_tavily_client().search(
        query=enhanced_query,
        max_results=8,
        search_depth="advanced",
        include_domains=["apps.apple.com", "appfigures.com", "sensortower.com", "data.ai", "appmagic.rocks"],
    )

    results = []
    for r in response.get("results", []):
        results.append(
            f"Source: {r['url']}\n"
            f"Title: {r['title']}\n"
            f"Content: {r['content']}\n"
        )

    return "\n---\n".join(results) if results else "No App Store results found."


# =============================================================================
# PRODUCT HUNT SEARCH TOOL
# Searches for Product Hunt launches and discussions
# =============================================================================
@tool
def product_hunt_search(query: str) -> str:
    """Search Product Hunt for recently launched products, upvotes,
    maker info, and launch discussions. Good for finding new indie apps."""

    enhanced_query = f"{query} site:producthunt.com OR Product Hunt launch"

    response = get_tavily_client().search(
        query=enhanced_query,
        max_results=8,
        search_depth="advanced",
    )

    results = []
    for r in response.get("results", []):
        results.append(
            f"Source: {r['url']}\n"
            f"Title: {r['title']}\n"
            f"Content: {r['content']}\n"
        )

    return "\n---\n".join(results) if results else "No Product Hunt results found."


# =============================================================================
# REVENUE ESTIMATOR TOOL
# Searches for app revenue and download estimates
# =============================================================================
@tool
def estimate_app_revenue(app_name: str) -> str:
    """Search for revenue and download estimates for an app.
    Looks for data from Sensor Tower, AppMagic, data.ai, and similar sources."""

    queries = [
        f"{app_name} app revenue estimate",
        f"{app_name} downloads Sensor Tower data.ai",
        f"{app_name} app monthly revenue earnings",
    ]

    all_results = []
    client = get_tavily_client()
    for query in queries:
        response = client.search(
            query=query,
            max_results=5,
            search_depth="advanced",
        )

        for r in response.get("results", []):
            all_results.append(
                f"Source: {r['url']}\n"
                f"Title: {r['title']}\n"
                f"Content: {r['content']}\n"
            )

    return "\n---\n".join(all_results) if all_results else "No revenue data found."


# =============================================================================
# SOCIAL BUZZ TOOL
# Searches for social media mentions and viral moments
# =============================================================================
@tool
def social_buzz_search(app_name: str) -> str:
    """Search for social media mentions of an app - TikTok videos,
    Reddit threads, Twitter discussions. Good for understanding viral moments."""

    queries = [
        f"{app_name} app TikTok viral",
        f"{app_name} app reddit discussion review",
        f"{app_name} app Twitter trending",
    ]

    all_results = []
    client = get_tavily_client()
    for query in queries:
        response = client.search(
            query=query,
            max_results=5,
            search_depth="advanced",
        )

        for r in response.get("results", []):
            all_results.append(
                f"Platform mention for {app_name}:\n"
                f"Source: {r['url']}\n"
                f"Title: {r['title']}\n"
                f"Content: {r['content']}\n"
            )

    return "\n---\n".join(all_results) if all_results else "No social media mentions found."


# =============================================================================
# OUTPUT TOOLS
# These tools are used to capture structured output from agents
# The tools themselves do nothing - we just extract the args
# =============================================================================

@tool
def submit_discovered_apps(apps: List[DiscoveredApp]) -> str:
    """Submit the indie apps you discovered. Call this ONLY when you are done
    searching and have found 8+ indie apps worth researching. Pass all the apps
    you found with their details."""
    return f"Recorded {len(apps)} apps"


@tool
def submit_app_research(research: AppResearch) -> str:
    """Submit your research findings for this app. Call this when you have
    gathered enough information about the app's revenue, features, growth
    strategy, and clone potential."""
    return f"Research recorded for {research.name}"


# =============================================================================
# TOOL COLLECTIONS
# Different sets of tools for different agent types
# =============================================================================

# Basic research tools (legacy, used by APP_TRENDS_ANALYZER)
RESEARCH_TOOLS = [web_search]

# Discovery phase tools - broad search for finding apps
DISCOVERY_TOOLS = [
    web_search,
    app_store_search,
    product_hunt_search,
    submit_discovered_apps,  # Output tool
]

# Deep research phase tools - detailed info on specific apps
DEEP_RESEARCH_TOOLS = [
    web_search,
    app_store_search,
    estimate_app_revenue,
    social_buzz_search,
    submit_app_research,  # Output tool
]

# All available tools
ALL_TOOLS = [
    web_search,
    app_store_search,
    product_hunt_search,
    estimate_app_revenue,
    social_buzz_search,
]
