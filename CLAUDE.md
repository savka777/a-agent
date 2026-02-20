# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ALPHY is a deep research AI agent for finding indie app clone opportunities. It performs multi-phase research using specialized agents to find trending apps, analyze their success factors, extract patterns, and produce actionable Reddit-post-quality reports for entrepreneurs.

**Task tracking:** See `docs/backlog.md` for current status and pending tasks.
**Refactor plan:** See `docs/refactor-plan.md` for the full architecture plan.

## Architecture: Two Codebases in One Repo

The project is transitioning from a rigid 6-agent pipeline to a **supervisor + parallel workers + MCP architecture**. Both codebases coexist under `src/`. **When making changes, check if code is in old pipeline or new architecture.**

| Chunk | Status | Description |
|-------|--------|-------------|
| **A: Foundation** | COMPLETE | MCP client, state schemas, tool wrappers |
| **B: Agents + Workflow** | NEXT | Supervisor, Researcher, LangGraph workflow |
| **C: UI + Integration** | Pending | Rich CLI, components, commands |

### Import Path Convention (Critical)

The old pipeline and new architecture use **different import conventions**:

- **Old pipeline** runs with `src/` as the working directory, using relative imports:
  `from state.schema import AgentState`, `from agents.tools import DISCOVERY_TOOLS`
- **New architecture** uses `src.`-prefixed absolute imports:
  `from src.mcp.client import call_tool`, `from src.state.schemas import AppSummary`

When adding new code to the new architecture, always use `src.` prefixed imports.

### New Architecture (Chunk A)

```
src/mcp/client.py        MCPClient class, call_tool() convenience function, mcp_client() context manager
src/mcp/config.py         MCP_SERVERS dict with app_store + product_hunt server configs
src/state/schemas.py      Pydantic models: AppSummary, AppDetails, ResearchTask, ResearchResult, Scratchpad, etc.
src/state/supervisor_state.py   SupervisorState TypedDict with custom reducers (merge_scratchpad, dedupe_tasks, etc.)
src/tools/app_store.py    7 async wrappers: search_apps, get_app_details, get_developer_info, get_pricing_details, analyze_reviews, get_similar_apps, fetch_reviews
src/tools/product_hunt.py 4 async wrappers: get_posts, get_post_details, search_topics, get_collections
src/tools/web_search.py   Tavily wrappers: web_search, search_revenue, search_social_buzz
```

### Old Pipeline (Still Active)

```
Flow: init -> planning -> discovery <-> discovery_tools
                               |
                          deep_research <-> deep_research_tools
                               |
                          reflection -> pattern_extraction -> synthesis -> END
```

Key old pipeline files:
```
src/state/schema.py          AgentState TypedDict + dataclasses (AppOpportunity, ResearchScratchpad, SubQuery)
src/config/agent_config.py   AgentConfig dataclass + all 6 agent prompt configs
src/agents/base.py           Agent base class + create_llm() factory + AgentResponse dataclass
src/agents/tools.py          Tool definitions (DISCOVERY_TOOLS, DEEP_RESEARCH_TOOLS, RESEARCH_TOOLS)
src/workflow/graph.py        LangGraph StateGraph construction + run_workflow() entry point
src/workflow/nodes.py        Node functions for each graph step
src/workflow/routing.py      Conditional edge routing functions
src/cli.py                   CLI interaction: banners, questionary prompts, report saving
src/main.py                  Entry point: sync main() -> asyncio.run() for workflow
```

### Dual State Schemas (Watch Out)

Two state files with near-identical names serve different architectures:
- `src/state/schema.py` (no 's') - Old pipeline. Uses `AgentState` TypedDict + dataclasses (`AppOpportunity`, `ResearchScratchpad`)
- `src/state/schemas.py` (with 's') - New architecture. Uses Pydantic models (`AppSummary`, `ResearchResult`, `Scratchpad`)

The new `SupervisorState` in `src/state/supervisor_state.py` imports from `schemas.py` (new), not `schema.py` (old).

## Commands

```bash
# Install dependencies
uv sync

# Run workflow (interactive)
uv run python src/main.py

# Run with specific niche
uv run python src/main.py "plant identifier apps"

# Run with debug logging
uv run python src/main.py --debug

# Run gold standard evaluations
uv run python scripts/run_gold_standard.py
uv run python scripts/run_gold_standard.py --parallel

# Test MCP servers
uv run python scripts/test_product_hunt_mcp.py
uv run python scripts/test_revenue_mcp.py

# Verify new architecture imports compile
uv run python -c "from src.mcp.client import MCPClient; from src.state.schemas import ResearchTask; from src.state.supervisor_state import SupervisorState; print('OK')"
```

## MCP Setup

MCPs provide structured app data. The `mcp-servers/` directory is gitignored.

```bash
# App Store Scraper MCP (iOS + Android)
cd mcp-servers
git clone https://github.com/appreply-co/mcp-appstore.git
cd mcp-appstore && npm install

# Product Hunt MCP
uv pip install product-hunt-mcp
# Requires PRODUCT_HUNT_TOKEN from https://www.producthunt.com/v2/oauth/applications
```

MCP documentation: `docs/mcp/app-store-scraper.md`, `docs/mcp/product-hunt.md`, `docs/mcp/revenue-search-strategy.md`

Revenue data is not available via dedicated MCP (enterprise APIs cost $25k+/year). Instead, Tavily web search finds publicly shared MRR/revenue on Twitter, Indie Hackers, Reddit. See `docs/mcp/revenue-search-strategy.md`.

## Requirements

- **Python 3.14+** (pyproject.toml)
- **uv** package manager
- **Node.js 18+** (for App Store Scraper MCP)
- **Vertex AI** configured with Claude access

## Environment Variables

```bash
# LLM Provider
LLM_PROVIDER=vertex  # or "gemini"

# Vertex AI (Claude)
ANTHROPIC_VERTEX_PROJECT_ID=your-project-id
CLOUD_ML_REGION=us-east5
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Gemini (fallback)
GEMINI_API_KEY=your-gemini-key

# Tools
TAVILY_API_KEY=your-tavily-key
PRODUCT_HUNT_TOKEN=your-product-hunt-token

# Observability (optional)
BRAINTRUST_API_KEY=your-braintrust-key
```

## Key Patterns

### LLM Provider Abstraction

`create_llm()` in `src/agents/base.py` is the single factory for all LLM clients. It reads `LLM_PROVIDER` env var and maps model nicknames (e.g., `"claude-opus"`) to actual model IDs via `src/config/settings.py`. Model mappings are in `MODEL_MAPPING` dict. Only this function needs to change when adding providers.

### Tool-Based Structured Output

JSON text parsing fails silently with different LLM providers. Use tool calls for structured output:

```python
@tool
def submit_discovered_apps(apps: List[DiscoveredApp]) -> str:
    return "ok"  # Extract args from tool call, not this return value
```

The LLM calls the tool and the API returns arguments already parsed as typed data. The tool doesn't "do" anything except force structured output.

### MCP Tool Wrappers

New architecture tool wrappers in `src/tools/` follow a consistent pattern:
1. Call `call_tool(server_name, tool_name, params)` from `src/mcp/client.py`
2. Parse JSON response with `_parse_json()` helper
3. Map raw MCP response fields to Pydantic schema fields
4. Return typed Pydantic objects (not raw dicts)

### Anti-Hallucination Measures

1. **Source URLs Required** - Discovery and deep research agents must provide source URLs
2. **No-Hallucination Rules** - Prompts state: "Do NOT invent or hallucinate app names"
3. **Unknown Over Guessing** - Agents say "unknown" for missing data
4. **Tool-Based Output** - Typed schemas eliminate JSON parsing failures
5. **No Hardcoded Blocklists** - Agent reasons about "indie apps" vs "big companies"

## Development Notes

- **Lazy Initialization** - Agents, Tavily client, and MCP connections are lazily initialized to avoid import-time errors
- **Sync CLI, Async Workflow** - `main()` is sync (for questionary prompts), then `asyncio.run()` for the LangGraph workflow
- **Phase-Specific Messages** - Old workflow uses `discovery_messages` and `deep_research_messages` as separate message keys for independent tool loops
- **Logging** - `propagate=False` on custom loggers to prevent duplicates; `--debug` for verbose output
- **MCP Client Lifecycle** - `MCPClient` manages session lifecycle manually (not via `async with`). Use `mcp_client()` context manager or call `disconnect_all()` explicitly
- **Custom LangGraph Reducers** - `SupervisorState` uses custom reducers (`merge_scratchpad`, `dedupe_tasks`, `dedupe_results`) to handle concurrent worker updates without duplicates

## Known Issues

- Python 3.14 shows Pydantic V1 deprecation warnings (harmless)
- No retry logic for API rate limits
- App deduplication uses basic name matching (could use fuzzy matching)
- Search provider tied to Tavily; no fallback when credits run out
- No test suite yet (`tests/` directory does not exist)

## Output

Reports saved to `alphy/` directory:
- `MM-DD-YY-alphy-{niche}.md` - Markdown report
- `MM-DD-YY-alphy-{niche}.json` - Structured data

## Evaluation Framework

- **Gold Standard**: Schema in `scorers/gold_standard.json` (min 6 apps, 0 hallucinations, 80%+ relevance)
- **Usefulness Scorer**: 5-dimension LLM-as-judge in `scorers/usefulness_scorer.md`
- **Effectiveness Scorer**: `scorers/effectiveness_scorer.md`
- **Timeliness Scorer**: `scorers/timeliness_scorer.md`
- 10 preset categories in `scripts/run_gold_standard.py`

## Development Workflow

After completing any major feature or code change:

1. **Verify imports compile:** `uv run python -c "from src.{module} import *"`
2. **Run smoke test** - Quick test that new code works
3. **Review for issues** - Check for bugs, security issues, missing error handling
4. **Report summary** - List what was done, validation results, any issues
5. **Wait for approval** before proceeding to next feature
