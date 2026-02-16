# ALPHY Backlog

## Completed

- [x] Fix `TAVILY_API_KEY not found` error - Added `load_dotenv()` to gold standard script
- [x] Fix `compile_workflow` import error - Changed to `run_workflow` in gold standard script
- [x] Clean up duplicate logs - Added `propagate=False` to logger setup
- [x] Remove verbose log noise - Removed LLM response attrs, raw content dumps
- [x] Make LLM banner show once - Added `_llm_banner_shown` flag
- [x] Investigate why good apps (Grubby AI) were discarded - Found root cause: JSON parsing failed, fallback extracted article titles as app names
- [x] Add JSON extraction logging - Added warnings to `extract_json_from_response`
- [x] Refactor to tool-based structured output - Added `submit_discovered_apps` and `submit_app_research` tools

## In Progress

- [ ] Test the refactored workflow with a single category
- [ ] Run gold standard evaluations (10 categories)

## Pending

- [ ] Fix reflection loop - Currently detects problems (e.g., "all 15 apps are Grammarly") but doesn't properly retry with better queries
- [ ] Manual labeling of gold standard apps in `scorers/gold_standard.json`
- [ ] Integrate with Braintrust for regression testing
- [ ] Add multi-provider support (let users paste API key and pick provider)

## Future Considerations

- [ ] DuckDuckGo fallback for when Tavily credits run out
- [ ] Smarter app deduplication (fuzzy matching on names)
- [ ] Rate limiting / retry logic for API calls
- [ ] Parallel deep research (research multiple apps concurrently)
