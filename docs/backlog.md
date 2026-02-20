# ALPHY Backlog

## Current Focus: Architecture Refactor

See `docs/refactor-plan.md` for the full plan.

**Summary**: Replacing the rigid 6-agent pipeline with a supervisor + parallel workers architecture.

---

## Phase 0: MCP Validation ✅ COMPLETE

| MCP | Status | Documentation |
|-----|--------|---------------|
| App Store Scraper (appreply-co/mcp-appstore) | ✅ Validated | `docs/mcp/app-store-scraper.md` |
| Product Hunt MCP (product-hunt-mcp) | ✅ Validated | `docs/mcp/product-hunt.md` |
| Revenue MCP | ⏳ **Skipped** | See note below |

### Revenue Data Strategy

**Decision:** Skip dedicated Revenue MCP - requires expensive enterprise APIs ($25k+/year for Sensor Tower, data.ai, etc.)

**Alternative:** Use Tavily web search to find publicly shared revenue:
- Many indie makers share MRR on Twitter, Indie Hackers, blog posts
- Search queries: `"[App name] MRR"`, `"[App name] revenue"`, `"[Founder] making $X"`
- Already have `TAVILY_API_KEY` configured in project

**Revenue proxies from existing MCPs:**
- `get_pricing_details` → monetization model (free/freemium/subscription/IAP)
- `get_app_details` → ratings count, review count as popularity proxy
- Product Hunt votes/comments → traction signals

---

## Architecture Assessment ✅ READY

All gaps have been resolved in `docs/refactor-plan.md`:
- **Worker config:** Section 4.3 (max 5 concurrent, 60s timeout, 2 retries)
- **Event system:** Section 4.4 (WorkflowEvent enum with UI callbacks)
- **MCP fallback:** App Store → Tavily web search
- **Session state:** In-memory during session (disk persistence is future work)

---

## Execution Plan: 3 Chunks with Checkpoints

### Chunk A: Foundation (Phases 0-2) ✅ COMPLETE

**Owner:** Team lead (direct implementation)
**Completed:** 2026-02-19
**Code Review:** PASS (2 critical fixes applied)

| Task | Status | Files |
|------|--------|-------|
| MCP Client | ✅ | `src/mcp/client.py`, `src/mcp/config.py` |
| State Schemas | ✅ | `src/state/supervisor_state.py`, `src/state/schemas.py` |
| App Store Tools | ✅ | `src/tools/app_store.py` (7 async wrappers) |
| Product Hunt Tools | ✅ | `src/tools/product_hunt.py` (4 async wrappers) |
| Web Search Tools | ✅ | `src/tools/web_search.py` (revenue + social search) |

**Checkpoint A Results:**
- ✅ All imports compile
- ✅ Tavily web search returns results
- ✅ `create_initial_state()` works
- ✅ MCP servers installed, env vars set

**Code Review Fixes Applied:**
- Fixed MCP client session lifecycle (was exiting immediately)
- Added proper `_cleanup_server()` for disconnect
- Moved `import re` to top of web_search.py

### Chunk B: Agents + Workflow (Phases 3-4)
**Owner:** Main orchestration agent

| Task | Acceptance Criteria | Files |
|------|---------------------|-------|
| Supervisor Agent | Can parse intent, create plan | `src/agents/supervisor/` |
| Researcher Worker | Can execute one research task | `src/agents/researcher/` |
| Workflow Graph | End-to-end flow compiles | `src/workflow/supervisor_graph.py` |
| Parallel Dispatch | Can spawn 3 workers | `src/workflow/dispatch.py` |

**Checkpoint B:** Run a test query that creates a plan with 3 tasks, dispatches workers in parallel, collects results.

### Chunk C: UI + Integration (Phases 5-6)
**Owner:** UI/UX agent

| Task | Acceptance Criteria | Files |
|------|---------------------|-------|
| Theme & Design | Colors, styles defined | `src/ui/theme.py` |
| Main App | Can start, show prompt | `src/ui/app.py` |
| Components | Input, progress, results | `src/ui/components/` |
| Commands | /save, /help work | `src/ui/commands.py` |
| Integration | Workflow events update UI | `src/main.py` |

**Checkpoint C:** Full end-to-end demo: ask question → see plan → approve → watch workers → see results → /save.

---

## Agent Roles for YOLO Mode

### Main Orchestration Agent
**Responsibilities:**
- Phases 0-4 (MCP, State, Agents, Workflow)
- Write all backend code
- Ensure MCP integrations work
- Implement parallel worker dispatch
- Connect workflow to state

**Tools available:** All tools (read, write, edit, bash, etc.)

### UI/UX Agent
**Responsibilities:**
- Phase 5 (CLI Interface)
- Design system and theme
- All UI components
- User interaction patterns
- Real-time progress display

**Tools available:** All tools

### Code Reviewer Agent
**When to invoke:**
- After Chunk A completion
- After Chunk B completion
- After Chunk C completion
- Before any merge/commit

---

## Pre-flight Checklist (Before YOLO Mode)

- [x] Add explicit worker config values to refactor-plan.md ✅ (Section 4.3)
- [x] Define event system specification ✅ (Section 4.4)
- [x] Create stub `__init__.py` files for new directory structure ✅

### YOLO Mode Prompt (Chunk B - Next)

```
Read docs/refactor-plan.md and docs/backlog.md carefully.

CHUNK A IS COMPLETE. Continue with CHUNK B.

CHUNK B (Agents + Workflow) - Owner: Main orchestration agent
Files to create:
1. src/agents/supervisor/supervisor.py - Supervisor agent class
2. src/agents/supervisor/prompts.py - System prompts for supervisor
3. src/agents/supervisor/tools.py - show_plan, dispatch_researchers, ask_user, save_report
4. src/agents/researcher/researcher.py - Stateless worker agent
5. src/agents/researcher/prompts.py - System prompts for researcher
6. src/workflow/supervisor_graph.py - LangGraph state machine
7. src/workflow/dispatch.py - Parallel worker spawning with WORKER_CONFIG
8. src/workflow/events.py - WorkflowEvent enum for UI updates

Key constraints:
- Supervisor delegates only - NO research tools (only dispatch_researchers, show_plan, ask_user, save_report)
- Researcher has MCP tools - search_apps, get_app_details, get_posts, web_search, etc.
- Workers are stateless - all context passed in ResearchTask
- Use tool-based structured output via submit_research(ResearchResult)
- Worker config: max 5 concurrent, 60s timeout, 2 retries, continue on failure
- Use LangGraph Send() API for parallel dispatch

Reference existing code:
- src/mcp/client.py - call_tool() for MCP calls
- src/state/schemas.py - ResearchTask, ResearchResult, Scratchpad
- src/state/supervisor_state.py - SupervisorState TypedDict
- src/tools/*.py - Tool wrapper functions

→ CHECKPOINT: Test query creates plan, spawns 3 workers, collects results

After completing:
1. STOP and report what was completed
2. Review code for issues
3. Fix any issues found
4. Report summary to user
5. Wait for approval before Chunk C
```

---

## Why Refactor?

- Current pipeline is too rigid (linear flow)
- Context is fragmented between agents
- Reflection loop doesn't effectively retry
- No conversational follow-up possible
- User can't refine plan before execution

### New Architecture
- **Supervisor agent**: Plans, delegates, evaluates, synthesizes
- **Researcher workers**: Deep dive on individual apps (parallel)
- **Conversational UI**: Claude Code-style CLI with /commands
- **User in the loop**: See plan, approve/refine, continue conversation

---

## Completed (Pre-Refactor)

- [x] Fix `TAVILY_API_KEY not found` error
- [x] Fix `compile_workflow` import error
- [x] Clean up duplicate logs
- [x] Remove verbose log noise
- [x] Make LLM banner show once
- [x] Investigate Grammarly bug (JSON parsing failed, fallback extracted article titles)
- [x] Add JSON extraction logging
- [x] Refactor to tool-based structured output

---

## Archived (No Longer Relevant Post-Refactor)

These were relevant to the old 6-agent pipeline:

- [ ] ~~Fix reflection loop~~
- [ ] ~~Run gold standard evaluations on 10 categories~~
- [ ] ~~Manual labeling of gold standard apps~~

---

## Future Considerations (Post-Refactor)

- [ ] Session persistence (resume research later)
- [ ] DuckDuckGo fallback for when Tavily credits run out
- [ ] Smarter app deduplication (fuzzy matching)
- [ ] Multi-provider support (let users pick LLM provider)
- [ ] Context compaction (/compact command)
- [ ] Export to multiple formats (md, json, pdf)

---

## Final Steps (Before Open Source Release)

### README Creation Checklist

- [ ] Create comprehensive README.md with:
  - [ ] Project overview and features
  - [ ] Quick start guide
  - [ ] **MCP setup instructions** (run `scripts/setup_mcps.sh`)
  - [ ] Environment variables (see `.env.example`)
  - [ ] Required API tokens:
    - `PRODUCT_HUNT_TOKEN` - from https://www.producthunt.com/v2/oauth/applications
    - `TAVILY_API_KEY` - for web search fallback
    - Vertex AI / Gemini credentials for LLM
  - [ ] Usage examples
  - [ ] Architecture overview (link to `docs/refactor-plan.md`)
  - [ ] Contributing guidelines
  - [ ] License

### Notes for README
- `mcp-servers/` is gitignored - users must run setup script
- MCP documentation lives in `docs/mcp/`
- Each MCP has its own setup requirements (Node.js for App Store, Python for Product Hunt)
