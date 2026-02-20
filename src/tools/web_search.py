"""Web search tools using Tavily for revenue and social data."""

import os
import re
import logging
from typing import Literal

from tavily import AsyncTavilyClient

from src.state.schemas import RevenueSearchResult, SocialBuzzResult

logger = logging.getLogger(__name__)

# Lazy client initialization
_tavily_client: AsyncTavilyClient | None = None


def _get_tavily_client() -> AsyncTavilyClient:
    """Get or create Tavily client."""
    global _tavily_client
    if _tavily_client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set")
        _tavily_client = AsyncTavilyClient(api_key=api_key)
    return _tavily_client


async def web_search(
    query: str,
    max_results: int = 5,
    search_depth: Literal["basic", "advanced"] = "basic",
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> list[dict]:
    """
    General web search via Tavily.

    Args:
        query: Search query
        max_results: Maximum results
        search_depth: "basic" or "advanced"
        include_domains: Only search these domains
        exclude_domains: Exclude these domains

    Returns:
        List of search results with title, url, content
    """
    client = _get_tavily_client()

    kwargs = {
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
    }
    if include_domains:
        kwargs["include_domains"] = include_domains
    if exclude_domains:
        kwargs["exclude_domains"] = exclude_domains

    response = await client.search(**kwargs)

    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0),
        }
        for r in response.get("results", [])
    ]


async def search_revenue(
    app_name: str,
    founder_name: str | None = None,
) -> RevenueSearchResult:
    """
    Search for publicly shared revenue data.

    Searches for MRR, revenue posts on Twitter, Indie Hackers, etc.

    Args:
        app_name: Name of the app
        founder_name: Optional founder name for better results

    Returns:
        Revenue search results
    """
    # Build search queries
    queries = [
        f'"{app_name}" MRR',
        f'"{app_name}" revenue monthly',
        f'"{app_name}" making money indie',
    ]

    if founder_name:
        queries.append(f'"{founder_name}" "{app_name}" revenue')

    # Search with relevant domains
    revenue_domains = [
        "twitter.com",
        "x.com",
        "indiehackers.com",
        "reddit.com",
        "news.ycombinator.com",
    ]

    all_results = []
    revenue_mentions = []
    sources = []

    for query in queries[:2]:  # Limit to avoid rate limits
        try:
            results = await web_search(
                query,
                max_results=3,
                include_domains=revenue_domains,
            )
            all_results.extend(results)
        except Exception as e:
            logger.warning(f"Revenue search failed for query '{query}': {e}")

    # Extract revenue mentions
    mrr = None
    arr = None

    for result in all_results:
        content = result.get("content", "").lower()
        url = result.get("url", "")

        # Look for MRR/ARR patterns
        if "mrr" in content or "monthly" in content:
            revenue_mentions.append(result.get("content", "")[:200])
            sources.append(url)

            # Try to extract MRR value (simple pattern matching)
            mrr_match = re.search(r'\$[\d,]+(?:k)?(?:\s*mrr|\s*monthly)', content)
            if mrr_match and not mrr:
                mrr = mrr_match.group(0)

        if "arr" in content or "annual" in content:
            arr_match = re.search(r'\$[\d,]+(?:k|m)?(?:\s*arr|\s*annual)', content)
            if arr_match and not arr:
                arr = arr_match.group(0)

    return RevenueSearchResult(
        app_name=app_name,
        revenue_found=bool(revenue_mentions),
        mrr=mrr,
        arr=arr,
        revenue_mentions=revenue_mentions[:5],
        sources=list(set(sources))[:5],
    )


async def search_social_buzz(
    app_name: str,
) -> SocialBuzzResult:
    """
    Search for social media mentions and buzz.

    Args:
        app_name: Name of the app

    Returns:
        Social buzz analysis
    """
    # Search different platforms
    platforms = {
        "reddit": "reddit.com",
        "twitter": "twitter.com",
        "hacker_news": "news.ycombinator.com",
    }

    mentions = {
        "reddit": 0,
        "twitter": 0,
        "hacker_news": 0,
    }
    notable_posts = []

    for platform, domain in platforms.items():
        try:
            results = await web_search(
                f'"{app_name}"',
                max_results=5,
                include_domains=[domain],
            )
            mentions[platform] = len(results)

            # Add notable posts (high engagement)
            for r in results[:2]:
                notable_posts.append({
                    "platform": platform,
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")[:150],
                })
        except Exception as e:
            logger.warning(f"Social search failed for {platform}: {e}")

    # Simple sentiment detection
    total = sum(mentions.values())
    sentiment: Literal["positive", "neutral", "negative", "mixed"] = "neutral"

    if total > 10:
        sentiment = "positive"  # Lots of buzz = generally positive
    elif total > 5:
        sentiment = "mixed"

    return SocialBuzzResult(
        app_name=app_name,
        reddit_mentions=mentions["reddit"],
        twitter_mentions=mentions["twitter"],
        hacker_news_mentions=mentions["hacker_news"],
        notable_posts=notable_posts,
        sentiment=sentiment,
    )
