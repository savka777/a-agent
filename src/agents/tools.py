import os
from langchain_core.tools import tool
from tavily import TavilyClient


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
]

# Deep research phase tools - detailed info on specific apps
DEEP_RESEARCH_TOOLS = [
    web_search,
    app_store_search,
    estimate_app_revenue,
    social_buzz_search,
]

# All available tools
ALL_TOOLS = [
    web_search,
    app_store_search,
    product_hunt_search,
    estimate_app_revenue,
    social_buzz_search,
]
