# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ALPHY is a deep research AI agent for finding indie app clone opportunities. It performs multi-phase research using specialized agents to find trending apps, analyze their success factors, extract patterns, and produce actionable Reddit-post-quality reports for entrepreneurs.

## Current Status

**LLM Provider:** Claude Opus 4.5 via Vertex AI (switched from Gemini)

**Recently Completed:**
- Refactored agent outputs to use tool-based structured output (no more JSON text parsing)
- Fixed logging issues (duplicate logs, verbose noise)
- Added `submit_discovered_apps` and `submit_app_research` output tools
- Gold standard evaluation framework set up

**In Progress:** Testing refactored workflow and running gold standard evaluations

**Next Steps:**
1. Test the refactored workflow with a single category
2. Run gold standard evaluations: `uv run python scripts/run_gold_standard.py`
3. Manually label apps in `scorers/gold_standard.json`
4. Fix reflection loop (doesn't properly retry when research is insufficient)
5. Integrate with Braintrust for regression testing

**Backlog:** See `docs/backlog.md` for full task list

## Commands

```bash
# Install dependencies (required after model switch)
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

## Preset Categories (Indie-Focused)

The 10 categories optimized for indie app opportunities:

1. AI Writing Tools
2. Developer Tools & Utilities
3. Personal Knowledge Management
4. Screenshot & Screen Recording
5. Habit & Routine Trackers
6. Journaling & Mental Wellness
7. Freelancer & Invoice Tools
8. No-Code & Automation
9. Focus & Distraction Blocking
10. Mac Menu Bar Utilities

Future candidates in `docs/candidate_categories.md`.

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

The system supports multiple LLM providers via `src/config/settings.py`:

```python
LLM_PROVIDER = "vertex"  # or "gemini"

MODEL_MAPPING = {
    "vertex": {
        "claude-opus": "claude-opus-4-5@20251101",
        "claude-sonnet": "claude-sonnet-4-5-v2@20250514",
    },
    "gemini": {
        "gemini-3-pro": "gemini-3-pro-preview",
    }
}
```

All agents use `claude-opus` by default (configured in `agent_config.py`).

### State Schema

`AgentState` in `src/state/schema.py`:
- `categories` - Selected app categories to research
- `mode` - "general" or "targeted"
- `research_plan` - List of SubQuery to execute
- `discovered_apps` - List of AppOpportunity found (with sources) — uses `add_apps` reducer to deduplicate
- `scratchpad` - Tracks executed queries, findings, gaps, iteration count — uses `merge_scratchpad` reducer
- `current_phase` - ResearchPhase enum (PLANNING, DISCOVERY, DEEP_RESEARCH, etc.)
- `discovery_messages` / `deep_research_messages` - Phase-specific message histories
- `is_research_sufficient` - Reflection output
- `cross_app_patterns` - Extracted patterns
- `output_to_user` - Final markdown report
- `json_output` - Structured JSON output
- `errors` - Error accumulator using `add` reducer

### Tools

Tools are in `src/agents/tools.py` with lazy Tavily client initialization:

**Search Tools:**
- `web_search` - General web search via Tavily
- `app_store_search` - App Store focused search (includes appfigures, sensortower)
- `product_hunt_search` - Product Hunt focused search
- `estimate_app_revenue` - Revenue/download estimates from multiple sources
- `social_buzz_search` - TikTok, Reddit, Twitter mentions

**Output Tools (for structured data extraction):**
- `submit_discovered_apps` - Discovery agent calls this when done, passes list of apps
- `submit_app_research` - Deep research agent calls this when done, passes research data

Output tools use Pydantic schemas (`DiscoveredApp`, `AppResearch`) to enforce structure.

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
4. **Fallback Extraction** - `extract_apps_from_messages()` extracts app names directly from tool results with URLs
5. **Synthesis Grounding** - Synthesis agent only includes apps from the research data

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

## Additional Agents (Not in Main Workflow)

`TrendResearchAgent` and `UserCommunicatorAgent` exist in `src/agents/` but are not wired into the main LangGraph workflow. They may be used for alternative workflows or future features.

## Known Issues

- Python 3.14 shows Pydantic V1 deprecation warnings (harmless)
- Braintrust logging may not capture all traces
- LLMs may still occasionally synthesize patterns without grounding in specific apps
- Reflection loop may not trigger if iteration_count isn't properly tracked

## Recent Changes

- **Model Switch**: Gemini → Claude Opus 4.5 via Vertex AI
- **Categories**: Updated to 10 indie-focused categories
- **Evaluation**: Added gold standard schema, usefulness scorer, evaluation runner
- **Docs**: Added `docs/candidate_categories.md` for future category options
- **Structured Output Refactor**: Switched from JSON text parsing to tool-based output

## Design Decisions & Lessons Learned

### Why Tool-Based Structured Output?

**Problem:** When agents output JSON as text, we had to parse it. This parsing failed silently with Claude (worked fine with Gemini), causing a cascade of bugs:
1. `parse_apps_from_response()` returned 0 apps
2. Fallback `extract_apps_from_messages()` ran
3. Fallback extracted article TITLES as app names (e.g., "Best AI Tools 2026")
4. Deep research then searched for these fake "apps" and found Grammarly articles
5. Final output: 15 entries all containing Grammarly data with garbage names

**Solution:** Use tool calls for structured output. Instead of asking the LLM to write JSON text, we define tools like `submit_discovered_apps(apps: List[DiscoveredApp])`. The LLM calls the tool with structured arguments. The API returns these arguments already parsed - no text parsing needed.

**Key Insight:** The tool doesn't actually DO anything. It's just a mechanism to force the LLM to output structured data that the API will parse for us.

```python
@tool
def submit_discovered_apps(apps: List[DiscoveredApp]) -> str:
    """Submit your findings."""
    return "ok"  # We don't use this - we extract args from the tool call
```

### Why Not Hardcode a Blocklist for Big Companies?

**Considered:** Adding a blocklist like `{"grammarly", "notion", "slack", ...}` to filter out big company apps.

**Decision:** Don't do it. The agent should understand "find indie apps" means "not Grammarly". The goal is to build an agent that reasons well, not one with hardcoded rules. The Grammarly bug was a pipeline failure (JSON parsing), not a reasoning failure.

### Provider Portability

**Goal:** Support multiple LLM providers (Claude, GPT, Gemini) without code changes.

**Approach:**
- Use LangChain abstractions (`bind_tools`, tool calling)
- Tool definitions are provider-agnostic (same Pydantic schemas work everywhere)
- Only the LLM client instantiation changes per provider
- Future: Let users paste API key and pick provider in config

### Logging Philosophy

- `propagate=False` on custom loggers to prevent duplicate output
- LLM provider banner shows once at startup, not per-agent
- Verbose debug info (response attrs, raw content) removed - use `--debug` flag if needed
- Warnings for JSON extraction failures to aid debugging

## Approaches Tried & Rejected

| Approach | Why Rejected |
|----------|--------------|
| Parse JSON from LLM text output | Fails silently with different providers, fragile |
| Hardcode big company blocklist | Agent should reason about indie vs big company |
| `extract_apps_from_messages` fallback | Extracted article titles, not actual apps |
| Multiple JSON extraction strategies | Added complexity, still failed |

## What's Working Well

- Tool-based structured output (provider-agnostic, reliable)
- LangGraph state machine with phase-specific message histories
- Lazy initialization of agents and API clients
- Gold standard evaluation framework for regression testing
- Usefulness scorer with 5-dimension rubric

## Known Gaps to Address

1. **Reflection loop** - Detects problems but doesn't effectively retry with better queries
2. **App deduplication** - Basic name matching, could use fuzzy matching
3. **Rate limiting** - No retry logic for API failures
4. **Search provider** - Tied to Tavily, need fallback (DuckDuckGo) when credits run out
