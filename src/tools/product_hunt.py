"""Product Hunt MCP tool wrappers."""

import json
import logging
from typing import Literal

from src.mcp.client import call_tool
from src.state.schemas import ProductSummary, ProductDetails

logger = logging.getLogger(__name__)


def _parse_json(text: str) -> dict:
    """Parse JSON response from MCP."""
    if isinstance(text, dict):
        return text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON: {text[:100]}...")
        return {}


async def get_posts(
    topic: str | None = None,
    featured: bool = True,
    count: int = 20,
    order: Literal["VOTES", "NEWEST", "RANKING"] = "VOTES",
) -> list[ProductSummary]:
    """
    Get Product Hunt posts/launches.

    Args:
        topic: Topic slug (e.g., "artificial-intelligence", "productivity")
        featured: Only featured products
        count: Number of results
        order: Sort order

    Returns:
        List of product summaries
    """
    params = {
        "featured": featured,
        "count": min(count, 50),
        "order": order,
    }
    if topic:
        params["topic"] = topic

    result = await call_tool("product_hunt", "get_posts", params)

    data = _parse_json(result)

    # Handle nested response structure
    if data.get("success") and data.get("data"):
        posts = data["data"].get("posts", [])
    else:
        posts = data.get("posts", [])

    products = []
    for post in posts:
        # Handle node wrapper if present
        node = post.get("node", post)

        products.append(ProductSummary(
            id=str(node.get("id", "")),
            name=node.get("name", "Unknown"),
            tagline=node.get("tagline", ""),
            slug=node.get("slug", ""),
            votes_count=node.get("votesCount", 0),
            comments_count=node.get("commentsCount", 0),
            featured=node.get("featured", False),
            url=node.get("url"),
            thumbnail=node.get("thumbnail", {}).get("url") if isinstance(node.get("thumbnail"), dict) else node.get("thumbnail"),
            topics=[t.get("name", "") for t in node.get("topics", {}).get("nodes", [])] if isinstance(node.get("topics"), dict) else [],
            makers_count=len(node.get("makers", [])),
        ))

    return products


async def get_post_details(
    post_id: str | None = None,
    slug: str | None = None,
    comments_count: int = 10,
) -> ProductDetails | None:
    """
    Get detailed info about a Product Hunt product.

    Args:
        post_id: Product ID
        slug: Product slug (alternative to ID)
        comments_count: Number of comments to fetch

    Returns:
        Full product details
    """
    params = {"comments_count": comments_count}
    if post_id:
        params["id"] = post_id
    elif slug:
        params["slug"] = slug
    else:
        raise ValueError("Either post_id or slug required")

    result = await call_tool("product_hunt", "get_post_details", params)

    data = _parse_json(result)

    if data.get("success") and data.get("data"):
        post = data["data"].get("post", {})
    else:
        post = data.get("post", data)

    if not post:
        return None

    return ProductDetails(
        id=str(post.get("id", "")),
        name=post.get("name", "Unknown"),
        tagline=post.get("tagline", ""),
        slug=post.get("slug", ""),
        description=post.get("description"),
        votes_count=post.get("votesCount", 0),
        comments_count=post.get("commentsCount", 0),
        featured=post.get("featured", False),
        url=post.get("url"),
        website=post.get("website"),
        thumbnail=post.get("thumbnail", {}).get("url") if isinstance(post.get("thumbnail"), dict) else post.get("thumbnail"),
        topics=[t.get("name", "") for t in post.get("topics", {}).get("nodes", [])] if isinstance(post.get("topics"), dict) else [],
        makers=post.get("makers", []),
        created_at=post.get("createdAt"),
    )


async def search_topics(
    query: str,
    count: int = 10,
) -> list[dict]:
    """
    Search for Product Hunt topics.

    Args:
        query: Search term
        count: Number of results

    Returns:
        List of topic objects with name, slug, followers
    """
    result = await call_tool(
        "product_hunt",
        "search_topics",
        {"query": query, "count": count}
    )

    data = _parse_json(result)

    if data.get("success") and data.get("data"):
        topics = data["data"].get("topics", [])
    else:
        topics = data.get("topics", [])

    return [
        {
            "name": t.get("node", t).get("name", ""),
            "slug": t.get("node", t).get("slug", ""),
            "followers": t.get("node", t).get("followersCount", 0),
        }
        for t in topics
    ]


async def get_collections(
    featured: bool = True,
    count: int = 10,
) -> list[dict]:
    """
    Get Product Hunt collections.

    Args:
        featured: Only featured collections
        count: Number of results

    Returns:
        List of collection objects
    """
    result = await call_tool(
        "product_hunt",
        "get_collections",
        {"featured": featured, "count": count}
    )

    data = _parse_json(result)

    if data.get("success") and data.get("data"):
        collections = data["data"].get("collections", [])
    else:
        collections = data.get("collections", [])

    return [
        {
            "id": c.get("node", c).get("id", ""),
            "name": c.get("node", c).get("name", ""),
            "tagline": c.get("node", c).get("tagline", ""),
            "products_count": c.get("node", c).get("postsCount", 0),
        }
        for c in collections
    ]
