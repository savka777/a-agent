# ALPHY Backlog

## Current Focus: Architecture Refactor

See `docs/refactor-plan.md` for the full plan.

**Summary**: Replacing the rigid 6-agent pipeline with a supervisor + parallel workers architecture.

### Phase 0: MCP Validation Progress

| MCP | Status | Documentation |
|-----|--------|---------------|
| App Store Scraper (appreply-co/mcp-appstore) | ✅ Validated | `docs/mcp/app-store-scraper.md` |
| Product Hunt MCP (product-hunt-mcp) | ✅ Validated | `docs/mcp/product-hunt.md` |
| Revenue MCP | ⏳ Not started | - |

### Why
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
