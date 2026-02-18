# ALPHY Backlog

## Current Focus: Architecture Refactor

See `docs/refactor-plan.md` for the full plan.

**Summary**: Replacing the rigid 6-agent pipeline with a supervisor + parallel workers architecture.

### Phase 0: MCP Validation Progress

| MCP | Status | Documentation |
|-----|--------|---------------|
| App Store Scraper (appreply-co/mcp-appstore) | ✅ Validated | `docs/mcp/app-store-scraper.md` |
| Product Hunt MCP (product-hunt-mcp) | ✅ Validated | `docs/mcp/product-hunt.md` |
| Revenue MCP | ⏳ **Skipped** | See note below |

#### Revenue Data Strategy

**Decision:** Skip dedicated Revenue MCP - requires expensive enterprise APIs ($25k+/year for Sensor Tower, data.ai, etc.)

**Alternative:** Use Tavily web search to find publicly shared revenue:
- Many indie makers share MRR on Twitter, Indie Hackers, blog posts
- Search queries: `"[App name] MRR"`, `"[App name] revenue"`, `"[Founder] making $X"`
- Already have `TAVILY_API_KEY` configured in project

**Revenue proxies from existing MCPs:**
- `get_pricing_details` → monetization model (free/freemium/subscription/IAP)
- `get_app_details` → ratings count, review count as popularity proxy
- Product Hunt votes/comments → traction signals

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
