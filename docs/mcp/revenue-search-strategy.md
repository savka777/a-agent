# Revenue Search Strategy

**Status**: Using Tavily web search (no dedicated MCP)
**Reason**: Revenue data is not public - services like Sensor Tower require $25k+/year enterprise subscriptions

## Why No Revenue MCP?

Revenue estimates from services like Sensor Tower, data.ai, and AppMagic are derived from:
- Panel data (apps installed on tracked devices)
- Statistical modeling
- SDK integrations
- Credit card partnerships

This data is proprietary and expensive. However, many indie makers publicly share their revenue.

## Our Approach: Search for Public Revenue Data

Use Tavily web search to find revenue mentions in:
- Twitter/X posts
- Indie Hackers posts
- Blog articles
- Interviews
- Product Hunt launch posts

## Search Query Templates

```python
# Primary revenue searches
f'"{app_name}" MRR'
f'"{app_name}" revenue monthly'
f'"{app_name}" ARR'
f'"{app_name}" making money'

# Platform-specific searches
f'"{app_name}" MRR site:twitter.com'
f'"{app_name}" revenue site:indiehackers.com'
f'"{founder_name}" "{app_name}" revenue'

# Alternative signals
f'"{app_name}" customers paying'
f'"{app_name}" subscribers'
f'"{app_name}" downloads revenue'
```

## Revenue Proxies from Validated MCPs

When direct revenue data isn't found, use these proxies:

### From App Store Scraper

| Tool | Signal | Interpretation |
|------|--------|----------------|
| `get_pricing_details` | Monetization model | Free vs Paid vs Subscription |
| `get_pricing_details` | IAP price range | Revenue potential per user |
| `get_app_details` | Rating count | Popularity / user base size |
| `get_app_details` | Review count | Engaged user base |
| `get_developer_info` | Total apps | Indie (< 5) vs studio |

### From Product Hunt MCP

| Tool | Signal | Interpretation |
|------|--------|----------------|
| `get_posts` | Vote count | Launch traction |
| `get_post_details` | Comment count | Community interest |
| `get_post_details` | Featured status | Quality signal |

## Example: Estimating Revenue Potential

```python
async def estimate_revenue_potential(app_name: str, app_id: str):
    """Combine multiple signals to estimate revenue potential"""

    signals = {}

    # 1. Get monetization model
    pricing = await app_store_mcp.get_pricing_details(app_id)
    signals['monetization'] = pricing['monetizationModel']
    signals['has_subscriptions'] = pricing['subscriptions']['offers']

    # 2. Get popularity metrics
    details = await app_store_mcp.get_app_details(app_id)
    signals['ratings_count'] = details['ratings']
    signals['avg_rating'] = details['score']

    # 3. Search for public revenue data
    revenue_search = await tavily.search(f'"{app_name}" MRR OR revenue')
    signals['revenue_mentions'] = extract_revenue_figures(revenue_search)

    # 4. Check indie status
    dev_info = await app_store_mcp.get_developer_info(details['developerId'])
    signals['is_indie'] = dev_info['totalApps'] < 5

    return signals
```

## Common Revenue Sharing Patterns

Indie makers often share revenue in these formats:
- "Just hit $10k MRR with [App]!"
- "[App] is now making $5k/month"
- "Revenue update: $50k ARR"
- "We crossed 1000 paying customers"

The search should look for these patterns and extract the figures.

## Limitations

- Not all apps have public revenue data
- Self-reported numbers may be inflated/outdated
- Search results depend on Tavily's index coverage
- Twitter/X API changes may affect social search

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TAVILY_API_KEY` | Yes | Already configured in project |
