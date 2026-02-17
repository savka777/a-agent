# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ALPHY is a deep research AI agent for finding indie app clone opportunities. It performs multi-phase research using specialized agents to find trending apps, analyze their success factors, extract patterns, and produce actionable Reddit-post-quality reports for entrepreneurs.

**Task tracking:** See `docs/backlog.md` for current status, in-progress work, and pending tasks.

## ⚠️ Architecture Refactor In Progress

The project is transitioning from a rigid 6-agent pipeline to a **supervisor + parallel workers + MCP architecture**. See `docs/refactor-plan.md` for the full plan.

**Current state:** Old 6-agent pipeline still in `src/`. Refactor introduces:
- Supervisor agent (plans, delegates, synthesizes)
- Parallel researcher workers (stateless, one task each)
- MCP layer for real app data (App Store, Product Hunt, Revenue APIs)
- Conversational CLI with /commands

When making changes, check if the code is in the old pipeline or new architecture.

## Commands

```bash
# Install dependencies
uv sync

# Run the workflow (interactive mode)
uv run python src/main.py

# Run with specific niche (targeted mode)
uv run python src/main.py "plant identifier apps"

# Run with debug logging
uv run python src/main.py --debug

# Run with pre-selected categories
uv run python src/main.py --categories "AI Writing Tools,Developer Tools"

# Run gold standard evaluations
uv run python scripts/run_gold_standard.py
uv run python scripts/run_gold_standard.py --parallel  # Faster but more resources
uv run python scripts/run_gold_standard.py --dry-run   # Preview without running
```

## Requirements

- **Python 3.14+** (required by pyproject.toml)
- **uv** package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Vertex AI** configured with Claude access

## Environment Variables

Set in `.env` or shell:

```bash
# LLM Provider (default: vertex)
LLM_PROVIDER=vertex  # or "gemini" for fallback

# Vertex AI (Claude) - required when LLM_PROVIDER=vertex
ANTHROPIC_VERTEX_PROJECT_ID=your-project-id
CLOUD_ML_REGION=us-east5
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Gemini (fallback) - required when LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key

# Tools
TAVILY_API_KEY=your-tavily-key

# Observability (optional)
BRAINTRUST_API_KEY=your-braintrust-key
```

## Preset Categories

10 indie-focused categories are defined in `scripts/run_gold_standard.py`. Future candidates tracked in `docs/candidate_categories.md`.

## Current Architecture (Pre-Refactor)

> **Note:** This documents the current 6-agent pipeline. See `docs/refactor-plan.md` for the target architecture.

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
- `src/config/settings.py` - LLM provider config (vertex/gemini), model mappings
- `src/agents/base.py` - Agent base class, `create_llm()` factory
- `src/config/agent_config.py` - Agent configurations with system prompts
- `src/workflow/graph.py` - LangGraph state machine definition
- `src/workflow/nodes.py` - Node implementations for each phase
- `src/workflow/routing.py` - Conditional edge routing
- `src/workflow/helpers.py` - Response parsers and formatters
- `src/state/schema.py` - State types (AgentState, AppOpportunity, etc.)
- `src/agents/tools.py` - Tool definitions (web_search, app_store_search, etc.)

### LLM Provider Configuration

Multiple LLM providers supported via `src/config/settings.py`. Set `LLM_PROVIDER` env var to `vertex` (Claude) or `gemini`. Model mappings and defaults configured in `src/config/agent_config.py`.

### State Schema

See `src/state/schema.py` for full details. Key points:
- `AgentState` is the main TypedDict with custom reducers for `discovered_apps` (deduplication) and `scratchpad` (merge)
- Phase-specific message histories (`discovery_messages`, `deep_research_messages`) support independent tool loops
- `errors` uses the `add` reducer to accumulate without overwriting

### Tools

Tools are in `src/agents/tools.py` with lazy Tavily client initialization.

**Search Tools:** `web_search`, `app_store_search`, `product_hunt_search`, `estimate_app_revenue`, `social_buzz_search`

**Output Tools:** `submit_discovered_apps`, `submit_app_research` - force structured output via Pydantic schemas (`DiscoveredApp`, `AppResearch`). These tools don't "do" anything except ensure the LLM returns typed data.

### Output

Reports are saved to `alphy/` directory:
- `MM-DD-YY-alphy-{niche}.md` - Markdown report with sources
- `MM-DD-YY-alphy-{niche}.json` - Structured data

## Evaluation Framework

### Gold Standard

Schema in `scorers/gold_standard.json`. Pass/fail thresholds:
- Min apps: 6
- Max hallucinations: 0
- Max broken links: 1
- Min relevance: 80%

Each app is labeled for: exists, cited, relevant, recent, indie, opportunity_quality.

### Usefulness Scorer

5-dimension LLM-as-judge scorer in `scorers/usefulness_scorer.md`:
1. Decision Clarity (0.20)
2. Build Guidance (0.20)
3. Market Validation (0.20)
4. Risk Awareness (0.20)
5. Specificity (0.20)

Target persona: Solo dev, 2-4 weeks, <$500 budget, iOS/Android/web.

### Running Evaluations

```bash
# Run all 10 categories, populate gold_standard.json
uv run python scripts/run_gold_standard.py

# Parallel mode (faster)
uv run python scripts/run_gold_standard.py --parallel

# Specific categories only
uv run python scripts/run_gold_standard.py --categories "AI Writing Tools,Developer Tools"
```

After running, manually label apps in `scorers/gold_standard.json`.

## Anti-Hallucination Measures

1. **Source URLs Required** - Discovery and deep research agents must provide source URLs for each app
2. **Explicit No-Hallucination Rules** - Prompts explicitly state: "Do NOT invent or hallucinate app names"
3. **Unknown Over Guessing** - Agents say "unknown" for missing data rather than fabricating
4. **Tool-Based Output** - Agents submit findings via tool calls with typed schemas, eliminating JSON parsing failures that caused previous hallucination-like bugs
5. **Synthesis Grounding** - Synthesis agent only includes apps from the research data

**Deprecated:** `extract_apps_from_messages()` fallback - this extracted article titles as app names and caused major issues. Now we rely on tool-based output instead.

## Adding a New Agent

1. Create config in `src/config/agent_config.py` with name, model, tools, timeout, system_prompt
2. Create agent class in `src/agents/<name>/<name>.py` extending `Agent` base class
3. Add specialized methods if needed (e.g., `run_simple()` for one-shot calls)
4. Export from `src/agents/<name>/__init__.py`
5. Add lazy getter function in `src/workflow/nodes.py`
6. Add node function in `src/workflow/nodes.py` that uses the getter
7. Wire into graph in `src/workflow/graph.py`
8. If the agent uses tools, create a wrapper function for phase-specific messages
9. Update routing in `src/workflow/routing.py` if needed
10. Update `src/agents/__init__.py` exports

## Development Notes

- **Lazy Initialization** - Agents and Tavily client are lazily initialized to avoid errors when API keys aren't set at import time
- **Sync CLI, Async Workflow** - `main()` is sync (for questionary prompts), then calls `asyncio.run()` for the workflow
- **Phase-Specific Messages** - The workflow uses `discovery_messages` and `deep_research_messages` instead of a shared `messages` list to support independent tool loops
- **Tool Node Wrappers** - Custom wrapper functions in `graph.py` map phase-specific messages to/from standard ToolNode

## Additional Agents (Not in Main Workflow)

`TrendResearchAgent` and `UserCommunicatorAgent` exist in `src/agents/` but are not wired into the main LangGraph workflow. They may be used for alternative workflows or future features.

## Known Issues

- Python 3.14 shows Pydantic V1 deprecation warnings (harmless)
- Braintrust logging may not capture all traces
- LLMs may still occasionally synthesize patterns without grounding in specific apps
- Reflection loop may not trigger if iteration_count isn't properly tracked
- No retry logic for API rate limits
- App deduplication uses basic name matching (could use fuzzy matching)
- Search provider tied to Tavily; no fallback when credits run out

## Design Decisions & Lessons Learned

### Tool-Based Structured Output

**Problem:** JSON text parsing failed silently with Claude, causing cascading bugs where article titles became "app names."

**Solution:** Use tool calls for structured output. The LLM calls tools like `submit_discovered_apps(apps: List[DiscoveredApp])` and the API returns arguments already parsed.

**Key Insight:** The output tool doesn't do anything - it just forces structured data that the API parses:
```python
@tool
def submit_discovered_apps(apps: List[DiscoveredApp]) -> str:
    return "ok"  # Extract args from tool call, not this return value
```

### No Hardcoded Blocklists

The agent should reason about "indie apps" vs "big companies" - don't hardcode blocklists. The Grammarly bug was a pipeline failure, not a reasoning failure.

### Provider Portability

- Use LangChain abstractions (`bind_tools`, tool calling)
- Tool definitions are provider-agnostic (Pydantic schemas work everywhere)
- Only LLM client instantiation changes per provider

### Logging

- `propagate=False` on custom loggers to prevent duplicates
- LLM banner shows once at startup
- Use `--debug` flag for verbose output

## Approaches Tried & Rejected

| Approach | Why Rejected |
|----------|--------------|
| Parse JSON from LLM text output | Fails silently with different providers, fragile |
| Hardcode big company blocklist | Agent should reason about indie vs big company |
| `extract_apps_from_messages` fallback | Extracted article titles, not actual apps |
| Multiple JSON extraction strategies | Added complexity, still failed |
