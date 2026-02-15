# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ALPHY is a deep research AI agent for finding indie app clone opportunities. It performs multi-phase research using specialized agents to find trending apps, analyze their success factors, extract patterns, and produce actionable Reddit-post-quality reports for entrepreneurs.

## Commands

```bash
# Run the workflow (interactive mode)
uv run python src/main.py

# Run with specific niche (targeted mode)
uv run python src/main.py "plant identifier apps"

# Run with debug logging
uv run python src/main.py --debug

# Run with pre-selected categories
uv run python src/main.py --categories "AI Photo/Video,Health & Fitness"

# Install dependencies
uv sync
```

## Required Environment Variables

Set in `.env`:
- `GEMINI_API_KEY` - Google Gemini API key (uses `gemini-3-pro-preview` model)
- `TAVILY_API_KEY` - Tavily search API key
- `BRAINTRUST_API_KEY` - Braintrust logging API key (optional)

Model aliases are configured in `src/config/settings.py` (e.g., `gemini-3-pro` → `gemini-3-pro-preview`).

## Architecture

### Core Flow (Deep Research)

```
init → planning → discovery ←→ discovery_tools
                      ↓
                 deep_research ←→ deep_research_tools
                      ↓
                 reflection
                 ↓ (sufficient?)
    (no) → discovery    or    pattern_extraction → (yes)
                                     ↓
                                 synthesis → END
```

### Six Specialized Agents

| Agent | Purpose | Tools |
|-------|---------|-------|
| **Planner** | Decomposes query into 8-12 targeted sub-queries | None |
| **Discovery Researcher** | Finds app candidates from searches | web_search, app_store_search, product_hunt_search |
| **Deep Researcher** | Goes deep on ONE app (revenue, differentiation, strategies) | web_search, app_store_search, estimate_app_revenue, social_buzz_search |
| **Reflection** | Evaluates: 8+ apps? Revenue data? Patterns visible? | None |
| **Pattern Extractor** | Finds patterns across all apps | None |
| **Synthesis** | Produces Reddit-post-quality report with sources | None |

### Key Files

- `src/main.py` - CLI entry point (sync prompts, then async workflow)
- `src/cli.py` - Interactive category selection, banner, report saving
- `src/workflow/graph.py` - LangGraph state machine definition
- `src/workflow/nodes.py` - Node implementations for each phase
- `src/workflow/routing.py` - Conditional edge routing
- `src/workflow/helpers.py` - Response parsers (`parse_subqueries_from_response`, `parse_apps_from_response`, etc.) and formatters for agent context
- `src/workflow/logging.py` - Debug mode status display
- `src/state/schema.py` - State types (AgentState, AppOpportunity, etc.)
- `src/config/agent_config.py` - Agent configurations with system prompts
- `src/agents/tools.py` - Tool definitions (web_search, app_store_search, etc.)

### State Schema

`AgentState` in `src/state/schema.py`:
- `categories` - Selected app categories to research
- `mode` - "general" or "targeted"
- `research_plan` - List of SubQuery to execute
- `discovered_apps` - List of AppOpportunity found (with sources) — uses `add_apps` reducer to deduplicate
- `scratchpad` - Tracks executed queries, findings, gaps, iteration count — uses `merge_scratchpad` reducer
- `current_phase` - ResearchPhase enum (PLANNING, DISCOVERY, DEEP_RESEARCH, etc.)
- `discovery_messages` / `deep_research_messages` - Phase-specific message histories — use LangGraph's `add_messages` reducer
- `is_research_sufficient` - Reflection output
- `cross_app_patterns` - Extracted patterns
- `output_to_user` - Final markdown report
- `json_output` - Structured JSON output
- `errors` - Error accumulator using `add` reducer

Custom reducers (`add_apps`, `merge_scratchpad`) in `src/state/schema.py` handle merging state updates across nodes.

### Tools

Tools are in `src/agents/tools.py` with lazy Tavily client initialization:
- `web_search` - General web search via Tavily
- `app_store_search` - App Store focused search (includes appfigures, sensortower)
- `product_hunt_search` - Product Hunt focused search
- `estimate_app_revenue` - Revenue/download estimates from multiple sources
- `social_buzz_search` - TikTok, Reddit, Twitter mentions

### Output

Reports are saved to `alphy/` directory:
- `MM-DD-YY-alphy-{niche}.md` - Markdown report with sources
- `MM-DD-YY-alphy-{niche}.json` - Structured data

## Anti-Hallucination Measures

The agents are configured to reduce hallucination:

1. **Source URLs Required** - Discovery and deep research agents must provide source URLs for each app
2. **Explicit No-Hallucination Rules** - Prompts explicitly state: "Do NOT invent or hallucinate app names"
3. **Unknown Over Guessing** - Agents say "unknown" for missing data rather than fabricating
4. **Fallback Extraction** - `extract_apps_from_messages()` extracts app names directly from tool results with URLs
5. **Synthesis Grounding** - Synthesis agent only includes apps from the research data

## Adding a New Agent

1. Create config in `src/config/agent_config.py` with name, model, tools, timeout, system_prompt
2. Create agent class in `src/agents/<name>/<name>.py` extending `Agent` base class
3. Add specialized methods if needed (e.g., `run_simple()` for one-shot calls, or custom methods like `plan_research()`, `evaluate()`)
4. Export from `src/agents/<name>/__init__.py`
5. Add lazy getter function in `src/workflow/nodes.py` (e.g., `get_my_agent()`)
6. Add node function in `src/workflow/nodes.py` that uses the getter
7. Wire into graph in `src/workflow/graph.py`
8. If the agent uses tools, create a wrapper function for phase-specific messages (see `discovery_tools_node` pattern)
9. Update routing in `src/workflow/routing.py` if needed
10. Update `src/agents/__init__.py` exports

Agent classes typically extend `Agent` from `src/agents/base.py` and use either:
- `run()` - for multi-turn conversation with tool loops
- `run_simple()` - for one-shot calls without state management

## Development Notes

- **Lazy Initialization** - Agents and Tavily client are lazily initialized to avoid errors when API keys aren't set at import time
- **Sync CLI, Async Workflow** - `main()` is sync (for questionary prompts), then calls `asyncio.run()` for the workflow
- **Phase-Specific Messages** - The workflow uses `discovery_messages` and `deep_research_messages` instead of a shared `messages` list to support independent tool loops
- **Tool Node Wrappers** - Custom wrapper functions in `graph.py` map phase-specific messages to/from standard ToolNode
- **Follow-Up Prompting** - After tool results, discovery node adds a follow-up HumanMessage to guide the agent

## Debugging

```bash
# Run with debug flag for verbose logging
uv run python src/main.py --debug

# Logs show:
# - [phase] messages for each workflow phase
# - Tool calls and results
# - App extraction counts
# - Reflection decisions
```

## Known Issues

- Python 3.14 shows Pydantic V1 deprecation warnings (harmless)
- Braintrust logging may not capture all traces
- LLMs may still occasionally synthesize patterns without grounding in specific apps
- Reflection loop may not trigger if iteration_count isn't properly tracked
