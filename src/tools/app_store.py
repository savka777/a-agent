"""App Store MCP tool wrappers."""

import json
import logging
from typing import Literal

from src.mcp.client import call_tool
from src.state.schemas import (
    AppSummary,
    AppDetails,
    DeveloperInfo,
    PricingDetails,
    ReviewSummary,
)

logger = logging.getLogger(__name__)

Platform = Literal["ios", "android"]


def _parse_json(text: str) -> dict:
    """Parse JSON response from MCP."""
    if isinstance(text, dict):
        return text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON: {text[:100]}...")
        return {}


async def search_apps(
    term: str,
    platform: Platform = "ios",
    num: int = 10,
    country: str = "us",
) -> list[AppSummary]:
    """
    Search for apps by keyword.

    Args:
        term: Search keyword
        platform: "ios" or "android"
        num: Number of results (max 50)
        country: Country code

    Returns:
        List of app summaries
    """
    result = await call_tool(
        "app_store",
        "search_app",
        {
            "term": term,
            "platform": platform,
            "num": min(num, 50),
            "country": country,
        }
    )

    data = _parse_json(result)
    apps = data.get("results", data) if isinstance(data, dict) else data

    if not isinstance(apps, list):
        apps = [apps] if apps else []

    return [
        AppSummary(
            app_id=str(app.get("appId") or app.get("id", "")),
            name=app.get("title") or app.get("name", "Unknown"),
            developer=app.get("developer", "Unknown"),
            developer_id=str(app.get("developerId", "")) if app.get("developerId") else None,
            platform=platform,
            score=app.get("score"),
            ratings_count=app.get("ratings"),
            free=app.get("free", True),
            url=app.get("url"),
        )
        for app in apps
        if app
    ]


async def get_app_details(
    app_id: str,
    platform: Platform = "ios",
    country: str = "us",
) -> AppDetails | None:
    """
    Get full details for an app.

    Args:
        app_id: App Store or Play Store app ID
        platform: "ios" or "android"
        country: Country code

    Returns:
        Full app details or None if not found
    """
    result = await call_tool(
        "app_store",
        "get_app_details",
        {
            "appId": app_id,
            "platform": platform,
            "country": country,
        }
    )

    data = _parse_json(result)
    if not data:
        return None

    return AppDetails(
        app_id=str(data.get("appId") or data.get("id", app_id)),
        name=data.get("title") or data.get("name", "Unknown"),
        developer=data.get("developer", "Unknown"),
        developer_id=str(data.get("developerId", "")) if data.get("developerId") else None,
        platform=platform,
        description=data.get("description"),
        score=data.get("score"),
        ratings_count=data.get("ratings"),
        reviews_count=data.get("reviews"),
        version=data.get("version"),
        released=data.get("released"),
        updated=data.get("updated"),
        size=data.get("size"),
        installs=data.get("installs"),
        price=data.get("price", 0.0),
        free=data.get("free", True),
        url=data.get("url"),
        icon=data.get("icon"),
        screenshots=data.get("screenshots", []),
        genre=data.get("genre") or data.get("primaryGenre"),
        content_rating=data.get("contentRating"),
    )


async def get_developer_info(
    developer_id: str,
    platform: Platform = "ios",
) -> DeveloperInfo | None:
    """
    Get developer portfolio info (for indie detection).

    Args:
        developer_id: Developer ID (must be string)
        platform: "ios" or "android"

    Returns:
        Developer info including app count
    """
    result = await call_tool(
        "app_store",
        "get_developer_info",
        {
            "developerId": str(developer_id),
            "platform": platform,
        }
    )

    data = _parse_json(result)
    if not data:
        return None

    total_apps = data.get("totalApps", 0)

    apps = []
    for app in data.get("apps", []):
        apps.append(AppSummary(
            app_id=str(app.get("appId") or app.get("id", "")),
            name=app.get("title") or app.get("name", "Unknown"),
            developer=data.get("name", "Unknown"),
            platform=platform,
            score=app.get("score"),
            free=app.get("free", True),
        ))

    return DeveloperInfo(
        developer_id=str(developer_id),
        name=data.get("name", "Unknown"),
        platform=platform,
        total_apps=total_apps,
        apps=apps,
        average_rating=data.get("averageRating"),
        total_ratings=data.get("totalRatings"),
        is_indie=total_apps < 5,
    )


async def get_pricing_details(
    app_id: str,
    platform: Platform = "ios",
) -> PricingDetails | None:
    """
    Get app monetization model.

    Args:
        app_id: App ID
        platform: "ios" or "android"

    Returns:
        Pricing and monetization details
    """
    result = await call_tool(
        "app_store",
        "get_pricing_details",
        {
            "appId": app_id,
            "platform": platform,
        }
    )

    data = _parse_json(result)
    if not data:
        return None

    # Determine monetization model
    base_price = data.get("basePrice", 0.0)
    has_iap = bool(data.get("inAppPurchases"))
    has_subs = data.get("hasSubscriptions", False)

    if base_price > 0:
        model = "paid"
    elif has_subs:
        model = "subscription"
    elif has_iap:
        model = "freemium"
    else:
        model = "free"

    return PricingDetails(
        app_id=app_id,
        base_price=base_price,
        currency=data.get("currency", "USD"),
        in_app_purchases=data.get("inAppPurchases", []),
        has_subscriptions=has_subs,
        monetization_model=model,
    )


async def analyze_reviews(
    app_id: str,
    platform: Platform = "ios",
) -> ReviewSummary | None:
    """
    Analyze app reviews for sentiment and themes.

    Args:
        app_id: App ID
        platform: "ios" or "android"

    Returns:
        Review analysis summary
    """
    result = await call_tool(
        "app_store",
        "analyze_reviews",
        {
            "appId": app_id,
            "platform": platform,
        }
    )

    data = _parse_json(result)
    if not data:
        return None

    sentiment = data.get("sentimentBreakdown", {})

    return ReviewSummary(
        app_id=app_id,
        total_reviews=data.get("totalReviews", 0),
        average_score=data.get("averageScore"),
        sentiment_positive=sentiment.get("positive", 0) / 100,
        sentiment_neutral=sentiment.get("neutral", 0) / 100,
        sentiment_negative=sentiment.get("negative", 0) / 100,
        common_themes=data.get("commonThemes", []),
        recent_issues=data.get("recentIssues", []),
        keyword_frequency=data.get("keywordFrequency", {}),
    )


async def get_similar_apps(
    app_id: str,
    platform: Platform = "ios",
) -> list[AppSummary]:
    """
    Get similar/competitor apps.

    Args:
        app_id: App ID
        platform: "ios" or "android"

    Returns:
        List of similar apps
    """
    result = await call_tool(
        "app_store",
        "get_similar_apps",
        {
            "appId": app_id,
            "platform": platform,
        }
    )

    data = _parse_json(result)
    apps = data.get("results", data) if isinstance(data, dict) else data

    if not isinstance(apps, list):
        apps = [apps] if apps else []

    return [
        AppSummary(
            app_id=str(app.get("appId") or app.get("id", "")),
            name=app.get("title") or app.get("name", "Unknown"),
            developer=app.get("developer", "Unknown"),
            platform=platform,
            score=app.get("score"),
            free=app.get("free", True),
        )
        for app in apps
        if app
    ]


async def fetch_reviews(
    app_id: str,
    platform: Platform = "ios",
    num: int = 50,
    sort: str = "recent",
) -> list[dict]:
    """
    Fetch raw reviews for an app.

    Args:
        app_id: App ID
        platform: "ios" or "android"
        num: Number of reviews
        sort: "recent" or "helpful"

    Returns:
        List of review objects
    """
    result = await call_tool(
        "app_store",
        "fetch_reviews",
        {
            "appId": app_id,
            "platform": platform,
            "num": num,
            "sort": sort,
        }
    )

    data = _parse_json(result)
    return data.get("reviews", []) if isinstance(data, dict) else []
