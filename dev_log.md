# Dev Log

## 2026-02-05: Fix Braintrust Logger Warning

**Problem:** Two `BraintrustCallbackHandler` instances were being created:
1. `main.py` - created after `init_logger()` and set as global handler
2. `base.py` via `get_bt_callback()` - created separately, triggered "Braintrust logging not configured" warning

**Solution:** Removed explicit callback passing in `base.py`. When `set_global_handler(handler)` is called in `main.py`, Braintrust automatically uses that handler for all LangChain calls (completions, tool calls, chains, agent steps).

**Changes to `src/agents/base.py`:**
- Removed `BraintrustCallbackHandler` import
- Removed `_bt_callback` variable and `get_bt_callback()` function
- Removed `config={'callbacks': [...]}` from both `ainvoke()` calls (lines 210, 287)

The global handler now traces everything through a single configured instance.

- still some issues: Braintrust is not picking up logs... 
- once in a while app does not return any data and quits, need retries...