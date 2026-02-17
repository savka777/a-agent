# App Store Scraper MCP

**Source**: [appreply-co/mcp-appstore](https://github.com/appreply-co/mcp-appstore)
**Built by**: AppReply.co
**Status**: ✅ Tested and working
**Platforms**: iOS App Store + Google Play Store

## Problem It Solves for ALPHY

| ALPHY Need | How This MCP Solves It |
|------------|------------------------|
| **Find trending apps in a niche** | `search_app(term, platform)` returns apps with ratings, developer info |
| **Verify app exists** | `get_app_details(appId)` returns full metadata - no hallucination risk |
| **Check if developer is indie** | `get_developer_info(devId)` returns `totalApps` - if < 5, likely indie |
| **Understand monetization** | `get_pricing_details(appId)` shows IAPs, subscriptions, freemium model |
| **Find user pain points** | `analyze_reviews(appId)` returns sentiment, issues, keyword frequency |
| **Discover competitors** | `get_similar_apps(appId)` returns related apps |

## Installation

```bash
# From project root
cd mcp-servers
git clone https://github.com/appreply-co/mcp-appstore.git
cd mcp-appstore
npm install
```

## Running the Server

```bash
# Start MCP server
npm start

# Run tests
npm test
```

## MCP Configuration

Add to your MCP client config:

```json
{
  "mcpServers": {
    "app-store-scraper": {
      "command": "node",
      "args": ["/path/to/mcp-servers/mcp-appstore/server.js"],
      "cwd": "/path/to/mcp-servers/mcp-appstore"
    }
  }
}
```

## Tools Available (17 total)

### Core Tools for ALPHY

| Tool | Purpose | Key Returns |
|------|---------|-------------|
| `search_app` | Search apps by keyword | `appId`, `title`, `developer`, `developerId`, `score`, `free` |
| `get_app_details` | Full app metadata | `description`, `ratings`, `reviews`, `histogram`, `installs`, `version` |
| `get_developer_info` | Developer portfolio | `totalApps`, `apps[]`, `averageRating`, `totalRatings` |
| `get_pricing_details` | Monetization model | `basePrice`, `inAppPurchases`, `subscriptions`, `monetizationModel` |
| `analyze_reviews` | Sentiment analysis | `sentimentBreakdown`, `keywordFrequency`, `recentIssues`, `commonThemes` |
| `fetch_reviews` | Raw reviews | `reviews[]` with `text`, `score`, `replyText` (developer responses) |
| `get_similar_apps` | Competitors | Similar apps with metadata |

### ASO Tools (Bonus)

| Tool | Purpose |
|------|---------|
| `analyze_top_keywords` | Keyword competition analysis |
| `get_keyword_scores` | Difficulty and traffic scores |
| `suggest_keywords_by_category` | Keywords from category |
| `suggest_keywords_by_similarity` | Keywords from similar apps |
| `suggest_keywords_by_competition` | Keywords from competitors |
| `suggest_keywords_by_apps` | Keywords from arbitrary apps |
| `suggest_keywords_by_seeds` | Keywords from seed terms |
| `suggest_keywords_by_search` | Keywords from search completion |

### Utility Tools

| Tool | Purpose |
|------|---------|
| `get_version_history` | App version changelog |
| `get_android_categories` | List Play Store categories |

## Example: Indie Developer Detection

```javascript
// 1. Search for apps in niche
const search = await client.callTool({
  name: "search_app",
  arguments: { term: "habit tracker", platform: "ios", num: 10 }
});

// 2. Check each developer's portfolio
for (const app of search.results) {
  const dev = await client.callTool({
    name: "get_developer_info",
    arguments: {
      developerId: String(app.developerId),
      platform: "ios"
    }
  });

  const isIndie = dev.totalApps < 5;
  console.log(`${app.title} by ${dev.name}: ${isIndie ? 'INDIE' : 'NOT INDIE'} (${dev.totalApps} apps)`);
}
```

## Data Quality Notes

### What Works Well
- App search returns real apps with valid IDs
- Developer portfolio count is accurate for indie detection
- Review sentiment analysis is built-in (no need for custom analyzer)
- Cross-platform support (iOS + Android) in single MCP

### Limitations
- **No revenue/download estimates** - Need separate Revenue MCP
- **iOS developerId is numeric** - Must convert to string before passing to `get_developer_info`
- **Review analysis may return empty `recentIssues`** for apps with few negative reviews
- **Android categories API** returns limited data ("APPLICATION" only)

### Data NOT Provided (Need Other MCPs)
- Revenue estimates
- Download counts (iOS)
- Product Hunt launches
- Social buzz (Reddit, TikTok, Twitter mentions)

## Tested Use Cases

| Use Case | Result |
|----------|--------|
| Search "habit tracker" on iOS | ✅ Found 5 apps with metadata |
| Check if developer is indie | ✅ `totalApps` field works (InnerGrow = 8 apps, NOT indie) |
| Get monetization model | ✅ Returns "Completely free" / "Freemium with subscriptions" |
| Analyze review sentiment | ✅ Returns sentiment breakdown (46% positive, 38% neutral) |
| Find competitors | ✅ Returns 5 similar apps with ratings |

## Environment Variables

None required - this MCP scrapes public app store data.

## Rate Limiting

The MCP includes:
- 10-minute response caching (memoization)
- Built-in rate limiting protection

For high-volume usage, consider adding delays between requests.
