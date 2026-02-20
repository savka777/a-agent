# ALPHY Refactor Plan: Supervisor + Workers + MCP Architecture

> **Goal**: Replace the rigid 6-agent pipeline with a flexible supervisor + parallel workers architecture powered by specialized MCPs for high-quality app market data.

## Why This Matters

| Before (Tavily Web Search) | After (MCPs) |
|---------------------------|--------------|
| "Search for habit tracker apps" → blog articles | `app-store-search("habit tracker")` → actual apps |
| "App X revenue" → maybe find an article | Revenue MCP → actual estimates |
| "Is this app indie?" → unreliable | `app-store-developer(devId)` → portfolio size |
| Extract app names from search results → hallucinations | Structured API data → `{ name, rating, reviews }` |
| Product Hunt via web search → outdated articles | `get_posts(topic, featured)` → real launches |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           ALPHY CLI                                 │
│                    (Claude Code-style UI)                           │
│  • User input bar with /commands                                    │
│  • Plan approval flow                                               │
│  • Real-time worker status                                          │
│  • Conversation continuity                                          │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SUPERVISOR AGENT                            │
│                                                                     │
│  Responsibilities:                                                  │
│  • Parse user intent (explore / validate / compare / deep-dive)     │
│  • Create research plan, show to user for approval                  │
│  • Dispatch parallel workers                                        │
│  • Evaluate results, retry failures                                 │
│  • Synthesize final response                                        │
│  • Be transparent about gaps/failures                               │
│                                                                     │
│  Tools: dispatch_researchers, ask_user, save_report                 │
│  (Supervisor has NO research tools - only delegation)               │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
             ┌───────────┐ ┌───────────┐ ┌───────────┐
             │ RESEARCHER│ │ RESEARCHER│ │ RESEARCHER│
             │  Worker 1 │ │  Worker 2 │ │  Worker N │
             │           │ │           │ │           │
             │ Stateless │ │ Stateless │ │ Stateless │
             │ One task  │ │ One task  │ │ One task  │
             └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
                   │             │             │
                   └─────────────┴─────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          MCP LAYER                                  │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  App Store       │  │  Product Hunt    │  │  Tavily          │  │
│  │  Scraper ✅      │  │  MCP ✅          │  │  (Web Search)    │  │
│  │                  │  │                  │  │                  │  │
│  │ iOS + Android:   │  │ • get_posts      │  │ • General search │  │
│  │ • search_app     │  │ • get_post_details│ │ • Revenue search │  │
│  │ • get_app_details│  │ • get_collections│  │   (MRR, revenue) │  │
│  │ • analyze_reviews│  │ • search_topics  │  │ • Social buzz    │  │
│  │ • get_similar    │  │ • filter by topic│  │   (Twitter, etc) │  │
│  │ • get_developer  │  │                  │  │ • News articles  │  │
│  │ • get_pricing    │  │                  │  │                  │  │
│  │ • ASO keywords   │  │                  │  │                  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: MCP Infrastructure

**Owner**: Backend Agent
**Priority**: FIRST - everything depends on this

### 0.1 MCP Client Setup ✅ VALIDATED
- [x] Research MCP client options for Python → Using `mcp` Python SDK
- [ ] Create `src/mcp/__init__.py`
- [ ] Create `src/mcp/client.py` - MCP connection manager
  - [ ] `MCPClient` class with connection pooling
  - [ ] `call_tool(server, tool_name, params)` method
  - [ ] Error handling and retries
  - [ ] Timeout configuration (60s default)

### 0.2 MCP Server Configuration ✅ VALIDATED
- [ ] Create `src/mcp/config.py` - server definitions
  ```python
  MCP_SERVERS = {
      "app_store": {
          "command": "node",
          "args": ["mcp-servers/mcp-appstore/server.js"],
          "cwd": "mcp-servers/mcp-appstore",
          "env": {}
      },
      "product_hunt": {
          "command": ".venv/bin/product-hunt-mcp",
          "env": {"PRODUCT_HUNT_TOKEN": "${PRODUCT_HUNT_TOKEN}"}
      }
  }
  # Note: Revenue data via Tavily web search, not dedicated MCP
  ```
- [ ] Create `.env.example` with required tokens
  ```
  PRODUCT_HUNT_TOKEN=your_token_here
  TAVILY_API_KEY=your_key_here
  ```

### 0.3 Tool Registry
- [ ] Create `src/tools/__init__.py`
- [ ] Create `src/tools/registry.py`
  - [ ] `ToolRegistry` class - discovers and registers tools
  - [ ] Load tools from MCP servers at startup
  - [ ] Unified interface: `registry.call(tool_name, params)`
- [ ] Create `src/tools/schemas.py` - Pydantic models for tool inputs/outputs

### 0.4 MCP Tool Wrappers
- [ ] Create `src/tools/app_store.py`
  ```python
  async def search_apps(query: str, platform: str = "both") -> List[App]:
      """Search App Store and/or Play Store."""

  async def get_app_details(app_id: str, platform: str) -> AppDetails:
      """Get full app metadata."""

  async def get_app_reviews(app_id: str, platform: str, limit: int = 50) -> List[Review]:
      """Get user reviews."""

  async def get_similar_apps(app_id: str, platform: str) -> List[App]:
      """Get competitor/similar apps."""

  async def get_developer_apps(developer_id: str, platform: str) -> List[App]:
      """Get all apps by developer (for indie detection)."""
  ```
- [ ] Create `src/tools/revenue.py`
  ```python
  async def search_revenue(app_name: str, founder_name: Optional[str] = None) -> RevenueSearchResult:
      """Search Tavily for publicly shared revenue data (MRR, revenue posts)."""

  async def get_revenue_proxies(app_id: str, platform: str) -> RevenueProxies:
      """Get indirect revenue signals: pricing model, ratings count, review count."""
  ```
- [ ] Create `src/tools/product_hunt.py`
  ```python
  async def get_trending_products(topic: str, days: int = 30) -> List[Product]:
      """Get recent Product Hunt launches."""

  async def get_product_details(slug: str) -> ProductDetails:
      """Get full product info including votes, comments."""
  ```
- [ ] Create `src/tools/web_search.py`
  ```python
  async def web_search(query: str) -> List[SearchResult]:
      """General web search via Tavily (fallback)."""

  async def social_search(query: str) -> SocialBuzz:
      """Search Reddit, Twitter, TikTok mentions."""
  ```

---

## Phase 1: State & Schemas

**Owner**: Backend Agent

### 1.1 Core State Schema
- [ ] Create `src/state/__init__.py`
- [ ] Create `src/state/supervisor_state.py`
  ```python
  class SupervisorState(TypedDict):
      # User interaction
      user_query: str
      messages: List[BaseMessage]  # Conversation history

      # Planning
      intent: Intent  # explore | validate | compare | deep_dive
      plan: List[ResearchTask]
      plan_approved: bool

      # Execution
      scratchpad: Scratchpad  # Single source of truth
      pending_tasks: List[ResearchTask]
      active_workers: Dict[str, WorkerStatus]

      # Results
      completed_results: List[ResearchResult]
      failed_tasks: List[FailedTask]

      # Control
      iteration_count: int
      max_iterations: int  # default 3
  ```

### 1.2 Research Schemas
- [ ] Create `src/state/schemas.py`
  ```python
  class ResearchTask(BaseModel):
      id: str
      type: Literal["discover", "deep_research", "validate", "compare"]
      target: str  # App name, search query, or app ID
      platform: Literal["ios", "android", "both", "producthunt"]
      context: str  # User's overall intent
      success_criteria: List[str]

  class ResearchResult(BaseModel):
      task_id: str
      app_name: str
      app_id: Optional[str]
      platform: str
      exists: bool
      confidence: Literal["high", "medium", "low"]

      # Data from MCPs
      details: Optional[AppDetails]
      reviews_summary: Optional[ReviewsSummary]
      revenue_estimate: Optional[RevenueEstimate]
      similar_apps: Optional[List[str]]
      is_indie: Optional[bool]  # Based on developer portfolio

      gaps: List[str]  # What we couldn't find
      sources: List[str]  # MCP calls made

  class Scratchpad(BaseModel):
      discovered_apps: List[AppSummary]
      researched_apps: Dict[str, ResearchResult]
      product_hunt_launches: List[ProductSummary]
      patterns: List[str]  # Cross-app observations
      user_refinements: List[str]  # User feedback incorporated
  ```

---

## Phase 2: Supervisor Agent

**Owner**: Backend Agent

### 2.1 Supervisor Implementation
- [ ] Create `src/agents/supervisor/__init__.py`
- [ ] Create `src/agents/supervisor/supervisor.py`
- [ ] Create `src/agents/supervisor/prompts.py`
  ```python
  SUPERVISOR_SYSTEM_PROMPT = """
  You are ALPHY's research supervisor. Your job is to:

  1. UNDERSTAND what the user wants to research
     - Explore: "What's trending in X?" → broad discovery
     - Validate: "Is X a good opportunity?" → focused research
     - Compare: "X vs Y?" → comparative analysis
     - Deep-dive: "Tell me everything about X" → comprehensive single-app

  2. CREATE a research plan
     - Break into specific, parallelizable tasks
     - Each task targets ONE app or ONE search
     - Show plan to user, get approval before executing

  3. DISPATCH workers
     - Spin up parallel researchers for each task
     - Workers have access to: App Store MCP, Revenue MCP, Product Hunt MCP

  4. EVALUATE results
     - Check: Does app exist? Do we have revenue data? Is it indie?
     - Retry failed tasks with different approach (max 2 retries)
     - Be honest about what we couldn't find

  5. SYNTHESIZE response
     - Combine worker results into coherent answer
     - Include confidence levels and sources
     - Highlight gaps transparently

  You have these tools:
  - show_plan(tasks): Display plan to user
  - dispatch_researchers(tasks): Spin up parallel workers
  - ask_user(question): Get clarification
  - save_report(format): Export findings

  You do NOT have research tools. You delegate, you don't research.
  """
  ```

### 2.2 Supervisor Tools
- [ ] Create `src/agents/supervisor/tools.py`
  ```python
  @tool
  def show_plan(tasks: List[ResearchTask]) -> str:
      """Display research plan to user for approval."""

  @tool
  def dispatch_researchers(tasks: List[ResearchTask]) -> str:
      """Dispatch parallel worker agents."""

  @tool
  def ask_user(question: str) -> str:
      """Ask user for clarification or input."""

  @tool
  def save_report(format: Literal["markdown", "json"]) -> str:
      """Export research to file."""
  ```

---

## Phase 3: Researcher Worker Agent

**Owner**: Backend Agent

### 3.1 Worker Implementation
- [ ] Create `src/agents/researcher/__init__.py`
- [ ] Create `src/agents/researcher/researcher.py`
- [ ] Create `src/agents/researcher/prompts.py`
  ```python
  RESEARCHER_SYSTEM_PROMPT = """
  You are a deep research specialist. You receive ONE task and execute it thoroughly.

  Your task: {task}
  Context: {context}
  Success criteria: {criteria}

  You have access to these MCP-powered tools:

  APP STORE DATA:
  - search_apps(query, platform) → Find apps
  - get_app_details(app_id, platform) → Full metadata
  - get_app_reviews(app_id, platform) → User reviews
  - get_similar_apps(app_id, platform) → Competitors
  - get_developer_apps(dev_id, platform) → Portfolio (for indie check)

  REVENUE DATA:
  - estimate_revenue(app_id) → Revenue/download estimates

  PRODUCT HUNT:
  - get_trending_products(topic, days) → Recent launches
  - get_product_details(slug) → Full product info

  WEB (fallback):
  - web_search(query) → General search
  - social_search(query) → Reddit, Twitter, TikTok

  PROCESS:
  1. Execute relevant tool calls
  2. Validate: Does the app actually exist? Is data reliable?
  3. Check if indie: Does developer have <5 apps?
  4. Report confidence level and any gaps

  OUTPUT: Call submit_research(result) with your structured findings.

  RULES:
  - NEVER invent data. If you can't find it, say "unknown"
  - ALWAYS include sources (which MCP tools returned the data)
  - If app doesn't exist in stores, say so clearly
  """
  ```

### 3.2 Worker Tools (MCP-backed)
- [ ] Bind MCP tools to worker agent
- [ ] Create output tool:
  ```python
  @tool
  def submit_research(result: ResearchResult) -> str:
      """Submit your research findings."""
      return "ok"
  ```

---

## Phase 4: Workflow Graph

**Owner**: Backend Agent

### 4.1 Main Graph
- [ ] Create `src/workflow/supervisor_graph.py`
  ```python
  # Nodes
  - parse_intent: Extract user intent from query
  - create_plan: Supervisor creates task list
  - await_approval: Show plan, wait for user OK/refinement
  - dispatch_workers: Spawn parallel researchers via Send()
  - researcher_node: Individual worker execution
  - collect_results: Gather all worker outputs
  - evaluate_results: Supervisor checks quality
  - handle_failures: Retry or report failures
  - synthesize: Create final response
  - await_followup: Wait for user continuation

  # Edges
  START → parse_intent → create_plan → await_approval

  await_approval ─[approved]─→ dispatch_workers
  await_approval ─[refine]──→ create_plan

  dispatch_workers → [parallel workers] → collect_results

  collect_results → evaluate_results

  evaluate_results ─[has failures, retries left]─→ dispatch_workers
  evaluate_results ─[sufficient]───────────────→ synthesize
  evaluate_results ─[max retries]──────────────→ synthesize

  synthesize → await_followup

  await_followup ─[new query]─→ parse_intent
  await_followup ─[/save]─────→ END
  await_followup ─[exit]──────→ END
  ```

### 4.2 Parallel Worker Dispatch
- [ ] Create `src/workflow/dispatch.py`
  - [ ] Use LangGraph's `Send()` API for parallel worker spawning
  - [ ] Worker timeout handling (60s default)
  - [ ] Error isolation (one worker crash doesn't kill others)
  - [ ] Result collection and aggregation

### 4.3 Worker Configuration (REQUIRED)

```python
# src/workflow/dispatch.py
WORKER_CONFIG = {
    "max_concurrent": 5,        # Max parallel workers
    "timeout_seconds": 60,      # Per-worker timeout
    "max_retries": 2,           # Retries per failed task
    "retry_strategy": "different_approach",  # Try alternate search terms
    "failure_mode": "continue", # Don't abort other workers on failure
    "result_aggregation": "wait_all",  # Wait for all workers before proceeding
}
```

**Timeout enforcement:** Use `asyncio.wait_for()` or LangGraph's built-in timeout.
**Failure handling:** Failed workers return `ResearchResult` with `exists=False` and `gaps=["reason"]`.
**Result aggregation:** Collect all results, then pass to supervisor for evaluation.

### 4.4 Event System Specification (REQUIRED)

Events emitted by workflow for UI updates:

```python
# src/workflow/events.py
class WorkflowEvent(Enum):
    # Planning phase
    INTENT_PARSED = "intent_parsed"      # {intent: str, confidence: float}
    PLAN_CREATED = "plan_created"        # {tasks: List[ResearchTask]}
    PLAN_APPROVED = "plan_approved"      # {}
    PLAN_REFINED = "plan_refined"        # {feedback: str}

    # Execution phase
    WORKER_STARTED = "worker_started"    # {worker_id: str, task: ResearchTask}
    WORKER_PROGRESS = "worker_progress"  # {worker_id: str, status: str}
    WORKER_COMPLETED = "worker_completed"  # {worker_id: str, result: ResearchResult}
    WORKER_FAILED = "worker_failed"      # {worker_id: str, error: str}

    # Synthesis phase
    SYNTHESIS_STARTED = "synthesis_started"  # {}
    SYNTHESIS_COMPLETE = "synthesis_complete"  # {summary: str}

    # Session
    REPORT_SAVED = "report_saved"        # {path: str, format: str}
```

**Event delivery:** Use Python `asyncio.Queue` or callback pattern.
**UI subscription:** `workflow.on(WorkflowEvent.WORKER_STARTED, callback)`.

---

## Phase 5: CLI Interface (UI/UX)

**Owner**: UI/UX Agent

### 5.1 Design System
- [ ] Create `src/ui/theme.py`
  - [ ] ALPHY color palette (distinct from Claude Code)
  - [ ] Status colors: success (green), warning (yellow), error (red), info (blue)
  - [ ] Component styles: borders, padding, spacing

### 5.2 Main Application
- [ ] Create `src/ui/app.py`
  - [ ] Main application loop using Rich
  - [ ] State machine: IDLE → PLANNING → APPROVED → RESEARCHING → RESULTS → IDLE
  - [ ] Keyboard interrupt handling (Ctrl+C to cancel)

### 5.3 Components
- [ ] Create `src/ui/components/input_bar.py`
  - [ ] User text input
  - [ ] /command autocomplete (/save, /compact, /help, /clear)
  - [ ] Multi-line input support
- [ ] Create `src/ui/components/plan_display.py`
  - [ ] Render plan as numbered checklist
  - [ ] Show task types with icons
  - [ ] "Press Enter to approve, or type to refine"
- [ ] Create `src/ui/components/progress.py`
  - [ ] Worker status grid (Worker 1: ✓, Worker 2: ⟳, Worker 3: ✗)
  - [ ] Overall progress bar
  - [ ] Current action spinner
- [ ] Create `src/ui/components/results.py`
  - [ ] App cards with key metrics
  - [ ] Confidence indicators
  - [ ] Expandable details
  - [ ] Source attribution
- [ ] Create `src/ui/components/status_bar.py`
  - [ ] Context usage (tokens)
  - [ ] Current phase
  - [ ] Warning notifications

### 5.4 Commands
- [ ] Create `src/ui/commands.py`
  - [ ] `/save [format]` - Export to markdown or JSON
  - [ ] `/compact` - Summarize context to free space
  - [ ] `/help` - Show available commands
  - [ ] `/clear` - Clear conversation
  - [ ] `/status` - Show research status

### 5.5 Event System
- [ ] Create `src/ui/events.py`
  - [ ] Event types for real-time UI updates
  - [ ] `plan_created`, `plan_approved`
  - [ ] `worker_started`, `worker_progress`, `worker_completed`, `worker_failed`
  - [ ] `synthesis_started`, `synthesis_complete`

---

## Phase 6: Integration

**Owner**: Both agents coordinate

### 6.1 Connect Workflow to UI
- [ ] Modify `src/main.py`
  - [ ] Initialize MCP clients
  - [ ] Initialize UI
  - [ ] Connect workflow events to UI updates
  - [ ] Main conversation loop

### 6.2 Session Management
- [ ] Create `src/session/session.py`
  - [ ] Session state persistence to disk
  - [ ] Scratchpad serialization/deserialization
  - [ ] Resume capability (future)

### 6.3 Report Export
- [ ] Create `src/ui/export.py`
  - [ ] Markdown report generation from scratchpad
  - [ ] JSON export
  - [ ] Include sources, confidence levels, gaps

---

## Phase 7: Testing

**Owner**: Backend Agent

### 7.1 MCP Integration Tests
- [ ] Create `tests/test_mcp_client.py`
  - [ ] AppInsightMCP connection
  - [ ] Product Hunt MCP connection
  - [ ] Tool call execution
  - [ ] Error handling

### 7.2 Agent Tests
- [ ] Create `tests/test_supervisor.py`
  - [ ] Intent parsing
  - [ ] Plan creation
  - [ ] Result evaluation
- [ ] Create `tests/test_researcher.py`
  - [ ] Tool execution
  - [ ] Output formatting
  - [ ] Confidence scoring

### 7.3 End-to-End Tests
- [ ] Create `tests/test_workflow.py`
  - [ ] Full query → plan → research → synthesis
  - [ ] Parallel worker execution
  - [ ] Failure recovery
  - [ ] User refinement flow

### 7.4 Manual Testing Checklist
- [ ] Single app research works
- [ ] Multi-app parallel research works
- [ ] User can refine plan before execution
- [ ] Failed tasks retry with different approach
- [ ] Failures reported transparently
- [ ] Follow-up questions work
- [ ] /save exports correctly
- [ ] MCP fallback works when one server is down

---

## Phase 8: Cleanup

**Owner**: Both agents

### 8.1 Archive Old Code
- [ ] Move to `src/_archive/`:
  - [ ] `src/agents/planner/`
  - [ ] `src/agents/discovery/`
  - [ ] `src/agents/deep_research/`
  - [ ] `src/agents/reflection/`
  - [ ] `src/agents/pattern_extraction/`
  - [ ] `src/agents/synthesis/`
  - [ ] `src/workflow/graph.py`
  - [ ] `src/workflow/nodes.py`

### 8.2 Update Documentation
- [ ] Update `CLAUDE.md` with new architecture
- [ ] Update `docs/backlog.md`
- [ ] Create `docs/architecture.md` with diagrams
- [ ] Create `docs/mcp-setup.md` with MCP configuration guide

---

## File Structure (After Refactor)

```
src/
├── main.py                      # Entry point
├── mcp/                         # NEW: MCP infrastructure
│   ├── __init__.py
│   ├── client.py                # MCP connection manager
│   └── config.py                # Server definitions
├── tools/                       # NEW: Tool wrappers
│   ├── __init__.py
│   ├── registry.py              # Tool discovery
│   ├── schemas.py               # Input/output models
│   ├── app_store.py             # AppInsight MCP wrapper
│   ├── revenue.py               # Revenue MCP wrapper
│   ├── product_hunt.py          # Product Hunt MCP wrapper
│   └── web_search.py            # Tavily fallback
├── state/
│   ├── __init__.py
│   ├── supervisor_state.py      # Main state
│   └── schemas.py               # Research schemas
├── agents/
│   ├── __init__.py
│   ├── base.py
│   ├── supervisor/              # NEW
│   │   ├── __init__.py
│   │   ├── supervisor.py
│   │   ├── prompts.py
│   │   └── tools.py
│   └── researcher/              # NEW
│       ├── __init__.py
│       ├── researcher.py
│       └── prompts.py
├── workflow/
│   ├── __init__.py
│   ├── supervisor_graph.py      # NEW: Main workflow
│   └── dispatch.py              # NEW: Parallel workers
├── ui/                          # NEW
│   ├── __init__.py
│   ├── app.py
│   ├── theme.py
│   ├── events.py
│   ├── commands.py
│   ├── export.py
│   └── components/
│       ├── __init__.py
│       ├── input_bar.py
│       ├── plan_display.py
│       ├── progress.py
│       ├── results.py
│       └── status_bar.py
├── session/                     # NEW
│   ├── __init__.py
│   └── session.py
├── config/
│   ├── __init__.py
│   └── settings.py
└── _archive/                    # OLD: Preserved for reference
    ├── agents/
    └── workflow/
```

---

## Implementation Order: 3 Chunks with Checkpoints

> **Execution mode:** YOLO mode with reflection checkpoints after each chunk.
> **Code review:** Run `code-reviewer` agent after each chunk before proceeding.

### Chunk A: Foundation (Phases 0-2)
**Owner:** Main orchestration agent
**Scope:** MCP client, state schemas, tool wrappers

| Task | Files | Acceptance Criteria |
|------|-------|---------------------|
| MCP Client | `src/mcp/client.py`, `src/mcp/config.py` | Can call both MCPs |
| State Schema | `src/state/supervisor_state.py`, `src/state/schemas.py` | All TypedDicts compile |
| Tool Wrappers | `src/tools/app_store.py`, `src/tools/product_hunt.py`, `src/tools/web_search.py` | Can search apps, get details |

**Checkpoint A:** Run test that calls each MCP tool and returns structured data.
```bash
uv run python -c "from src.tools.app_store import search_apps; print(search_apps('habit tracker', 'ios'))"
```

---

### Chunk B: Agents + Workflow (Phases 3-4)
**Owner:** Main orchestration agent
**Scope:** Supervisor agent, researcher worker, LangGraph workflow, parallel dispatch

| Task | Files | Acceptance Criteria |
|------|-------|---------------------|
| Supervisor Agent | `src/agents/supervisor/` | Can parse intent, create plan |
| Researcher Worker | `src/agents/researcher/` | Can execute one research task |
| Workflow Graph | `src/workflow/supervisor_graph.py` | End-to-end flow compiles |
| Parallel Dispatch | `src/workflow/dispatch.py` | Can spawn 3 workers in parallel |

**Checkpoint B:** Run test query that creates plan, dispatches 3 workers, collects results.
```bash
uv run python -c "from src.workflow import run_test; run_test('habit tracker apps')"
```

---

### Chunk C: UI + Integration (Phases 5-6)
**Owner:** UI/UX agent
**Scope:** Rich CLI interface, components, commands, event integration

| Task | Files | Acceptance Criteria |
|------|-------|---------------------|
| Theme & Design | `src/ui/theme.py` | Colors, styles defined |
| Main App | `src/ui/app.py` | Can start, show prompt |
| Components | `src/ui/components/` | Input, progress, results render |
| Commands | `src/ui/commands.py` | /save, /help work |
| Integration | `src/main.py` | Workflow events update UI |

**Checkpoint C:** Full end-to-end demo works:
```
Ask question → See plan → Approve → Watch workers → See results → /save
```

---

### Post-Chunk: Testing & Cleanup (Phases 7-8)
**Owner:** Both agents
**Scope:** Integration tests, archive old code, update docs

---

## Success Criteria

- [ ] User can ask open-ended research questions (no preset categories)
- [ ] Supervisor shows plan, user can approve or refine
- [ ] Workers research apps in parallel using MCPs
- [ ] Real app data from App Store/Play Store (not web scraping)
- [ ] Revenue estimates available for most apps
- [ ] Product Hunt launches searchable by topic/date
- [ ] Failures reported honestly with retry option
- [ ] User can continue conversation after results
- [ ] /save exports clean report with sources
- [ ] No hallucinated apps (MCP data is structured)

---

## Environment Variables Required

```bash
# MCP Servers
PRODUCT_HUNT_TOKEN=your_ph_developer_token

# Fallback Search
TAVILY_API_KEY=your_tavily_key

# LLM Provider
LLM_PROVIDER=vertex
ANTHROPIC_VERTEX_PROJECT_ID=your_project
CLOUD_ML_REGION=us-east5
GOOGLE_APPLICATION_CREDENTIALS=/path/to/creds.json
```

---

## MCP Server Reference

| MCP | Install | Required Env | Status |
|-----|---------|--------------|--------|
| **App Store Scraper** | `git clone https://github.com/appreply-co/mcp-appstore.git && npm install` | None | ✅ **VALIDATED** - See `docs/mcp/app-store-scraper.md` |
| **Product Hunt** | `uv pip install product-hunt-mcp` | `PRODUCT_HUNT_TOKEN` | ✅ **VALIDATED** - See `docs/mcp/product-hunt.md` |
| Revenue MCP | N/A | N/A | ⏳ **SKIPPED** - See note below |

> **Note**: AppInsightMCP (`@jeromyfu/app-insight-mcp`) was replaced with App Store Scraper from AppReply.co which provides more comprehensive coverage (17 tools including ASO features).

### Revenue Data Strategy

Revenue data is not publicly available - services like Sensor Tower ($25k+/year) use panel data and statistical modeling to estimate it.

**Our approach:** Use Tavily web search to find publicly shared revenue:
```python
# Example search queries for revenue discovery
web_search(f'"{app_name}" MRR site:twitter.com OR site:indiehackers.com')
web_search(f'"{app_name}" revenue monthly')
web_search(f'"{founder_name}" "{app_name}" making money')
```

**Revenue proxies from validated MCPs:**
| Signal | Tool | MCP |
|--------|------|-----|
| Monetization model | `get_pricing_details` | App Store Scraper |
| Popularity | Rating/review counts | App Store Scraper |
| Traction | Votes, comments | Product Hunt |

---

## Notes for Agents

### For Backend Agent:
- Start with MCP infrastructure (Phase 0) - everything depends on it
- Test each MCP connection before building agents
- Use structured output (tool-based) for all agent outputs
- Supervisor should NEVER have research tools
- Workers are stateless - all context passed in

### For UI/UX Agent:
- Use Rich library (already in dependencies)
- Real-time updates are critical for good UX
- Match Claude Code interaction patterns where sensible
- Plan approval is key UX moment - make it clear
- Show worker progress visually (grid or list)
