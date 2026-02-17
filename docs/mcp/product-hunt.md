# Product Hunt MCP

**Source**: [jaipandya/producthunt-mcp-server](https://github.com/jaipandya/producthunt-mcp-server)
**Package**: `product-hunt-mcp` (PyPI)
**Status**: ✅ Tested and working
**Auth Required**: Yes - Product Hunt Developer Token

## Problem It Solves for ALPHY

| ALPHY Need | How This MCP Solves It |
|------------|------------------------|
| **Discover trending products** | `get_posts(featured=True)` returns top-voted launches |
| **Find products by niche/topic** | `get_posts(topic="artificial-intelligence")` filters by category |
| **Validate product traction** | Vote counts, comment counts, featured status |
| **Identify makers** | `makers[]` array shows who built it (indie indicator) |
| **Find related collections** | `get_collections()` shows curated product lists |
| **Research topics/niches** | `search_topics(query)` finds relevant categories |

## Installation

```bash
# Install from PyPI
uv pip install product-hunt-mcp

# Or with pip
pip install product-hunt-mcp
```

## Setup

### 1. Get a Product Hunt API Token

1. Go to [Product Hunt API Dashboard](https://www.producthunt.com/v2/oauth/applications)
2. Sign in and click "Add an Application"
3. Fill in:
   - **Name**: `ALPHY` (or anything)
   - **Redirect URI**: `https://localhost:8424/callback` (required but unused)
4. Copy the **Developer Token**

### 2. Add to Environment

```bash
# Add to .env
echo 'PRODUCT_HUNT_TOKEN=your_token_here' >> .env
```

## Running the Server

```bash
# The executable is in your venv
.venv/bin/product-hunt-mcp
```

## MCP Configuration

```json
{
  "mcpServers": {
    "product-hunt": {
      "command": "/path/to/project/.venv/bin/product-hunt-mcp",
      "env": {
        "PRODUCT_HUNT_TOKEN": "your_token_here"
      }
    }
  }
}
```

## Tools Available (11 total)

### Core Tools for ALPHY

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `get_posts` | Get product launches | `topic`, `featured`, `order`, `count`, `posted_before`, `posted_after` |
| `get_post_details` | Detailed product info | `id` or `slug`, `comments_count` |
| `search_topics` | Find topic categories | `query`, `count` |
| `get_topic` | Topic details | `id` or `slug` |
| `get_collections` | Curated product lists | `featured`, `count` |
| `get_collection` | Collection details | `id` or `slug` |

### Other Tools

| Tool | Purpose |
|------|---------|
| `get_comment` | Single comment details |
| `get_post_comments` | Comments on a post |
| `get_user` | User profile info |
| `get_viewer` | Authenticated user info |
| `check_server_status` | API status and rate limits |

## Response Structure

Responses are wrapped in:
```json
{
  "success": true,
  "data": {
    "posts": [
      { "node": { "name": "...", "votesCount": 957, ... } }
    ],
    "pagination": { "end_cursor": "...", "has_next_page": true }
  },
  "rate_limits": { "remaining": 6250, "reset_at": "..." }
}
```

## Example: Get Trending AI Products

```python
result = await session.call_tool("get_posts", {
    "topic": "artificial-intelligence",
    "featured": True,
    "count": 10,
    "order": "VOTES"
})

data = json.loads(result.content[0].text)
posts = data["data"]["posts"]

for post in posts:
    p = post["node"]
    print(f"{p['name']} - {p['votesCount']} votes")
    print(f"  {p['tagline']}")
    print(f"  Makers: {len(p.get('makers', []))}")
```

## Example: Find Products in a Niche

```python
# First, find the topic slug
topics = await session.call_tool("search_topics", {"query": "productivity"})
# Returns: Productivity (slug: productivity), 645k followers

# Then get posts in that topic
posts = await session.call_tool("get_posts", {
    "topic": "productivity",
    "count": 20
})
```

## Data Quality Notes

### What Works Well
- Real-time featured products with accurate vote counts
- Topic filtering works (tested with "artificial-intelligence", "productivity")
- Makers array available for indie detection
- Pagination supported for large result sets
- Rate limit info included in every response

### Limitations
- **Maker names are [REDACTED]** in responses (privacy feature of API)
- **No revenue data** - Need separate Revenue MCP
- **No app store presence** - Products may or may not have mobile apps
- Rate limited: ~6000 requests per 15-minute window

### What This MCP Does NOT Provide
- Revenue/download estimates
- App store metadata
- User reviews/sentiment (only comments)
- Social buzz data

## Tested Use Cases

| Use Case | Result |
|----------|--------|
| Get featured posts | ✅ Returns top-voted products (happycapy 957 votes, DataFast 848 votes) |
| Filter by topic (AI) | ✅ Returns AI products (Figr AI, Boost.space, Mozart for iOS) |
| Search topics | ✅ Found "Productivity" with 645k followers |
| Get collections | ✅ Returns curated lists (Free Stuff For Startups, $0 Design Tools) |

## Rate Limiting

- ~6000 requests per 15-minute window
- Rate limit info in every response: `rate_limits.remaining`, `rate_limits.reset_at`
- Use `check_server_status` tool to verify authentication and limits

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PRODUCT_HUNT_TOKEN` | Yes | Developer token from PH API dashboard |

## Complementary MCPs

Use Product Hunt MCP alongside:
- **App Store Scraper MCP** - For apps that have mobile versions
- **Revenue MCP** - For revenue/download estimates (if product is an app)
