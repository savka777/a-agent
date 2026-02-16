# Braintrust Scoring Guide for ALPHY

Step-by-step instructions for scoring ALPHY research output using Braintrust.

---

## 1. Score the Entire System (End-to-End)

### Create the scorer in UI

```
Braintrust Dashboard → Scorers → + Scorer
    → Name: "ALPHY Effectiveness"
    → Type: LLM-as-a-judge
    → Paste your prompt from effectiveness_scorer.md
    → Model: gpt-4o or gemini-2.0-flash
    → Choice scores: Map A/B/C to 1.0/0.5/0.0 OR parse JSON score
    → Save
```

### Run eval on full workflow output

```python
from braintrust import Eval

Eval(
    "ALPHY Research",
    # tests in dev environment, input is what the user picks.
    data=lambda: [{"input": "AI Photo/Video", "expected": None}],
    task=lambda input: run_alphy_workflow(input),  # Returns final report
    scores=["ALPHY Effectiveness"],  # Your custom scorer
)
```

**Key point:** The scorer receives `{{output}}` = your final `output_to_user` markdown report

---

## 2. Score Individual Agents (Step-by-Step)

### Option A: Inline scorers per agent

```python
# In your node function, log spans with scores
import braintrust

@braintrust.traced
async def discovery_node(state):
    result = await discovery_agent.run(state)

    # Score this specific agent's output
    braintrust.current_span().log(
        scores={
            "apps_found": len(parsed_apps) / 10,  # 0-1 score
            "has_sources": 1 if all_have_urls else 0,
        }
    )
    return result
```

### Option B: Separate scorers per phase

```
Create multiple scorers:
    → "Discovery Quality" (scores app count, source URLs)
    → "Deep Research Depth" (scores revenue data, hook features)
    → "Reflection Accuracy" (scores decision quality)
    → "Synthesis Quality" (scores report writing)
```

### Attach to trace spans

```python
# Use hooks to capture intermediate outputs
async def task_func(input, hooks):
    # After discovery phase
    hooks.metadata["discovery_apps"] = discovered_apps
    hooks.metadata["deep_research_data"] = app_details

    # Scorers can access this metadata
    return final_output
```

---

## 3. Set Up Automatic Scoring

### For offline evals (CI/CD)

```bash
# Push your scorer to Braintrust
braintrust push scorers/effectiveness_scorer.py

# Run evals in CI
braintrust eval my_eval.py
```

### For online/production scoring

```
Braintrust Dashboard → Logs → Automations → + Rule
    → Filter: project = "alphy-deep-research"
    → Scorer: Select your custom scorers
    → Sampling: 100% (or lower for cost)
    → Save
```

### Enable logging in your workflow

```python
# In src/workflow/graph.py - already configured!
from braintrust import init_logger

init_logger(project="alphy-deep-research", api_key=api_key)
```

All runs automatically get scored when rules are active.

---

## Quick Reference

| Goal | Where | How |
|------|-------|-----|
| Score full report | Eval() or Online Rules | Pass `output_to_user` to scorer |
| Score discovery agent | Inline span scoring | Log scores in `discovery_node` |
| Score deep research | Inline span scoring | Log scores in `deep_research_node` |
| Score all agents | Trace metadata + hooks | Capture each phase output, score at end |
| Auto-score production | Logs → Automations | Create online scoring rules |
| Auto-score in CI | `braintrust eval` | Add to GitHub Actions |

---

## Gold Standard Evaluation Plan

### Purpose

Provide a benchmark against how well the agent performs in real-world settings. This allows us to identify success and failure modes.

### Two Types of Metrics

| Type | Examples | Requires Gold Standard? |
|------|----------|------------------------|
| **Reference-based** | Precision, recall, hallucination rate | Yes - compare against labeled data |
| **LLM-as-Judge** | Usefulness, effectiveness, timeliness | No - LLM evaluates output directly |

Both run on every evaluation. They complement each other:
- Gold standard catches **factual correctness**
- LLM judge catches **output quality**

### Success Criteria

| Criterion | Type | How to Measure |
|-----------|------|----------------|
| Required number of apps | Deterministic | `len(apps) >= 6` |
| Every app exists + cited | Deterministic | URL validation (HTTP 200) |
| Category relevance | LLM-as-judge | Does app X fit category Y? |
| Recency | Deterministic | App updated within last 12 months |
| Indie (not Big Tech) | Hybrid | Blocklist (Meta, Google, etc.) + LLM for edge cases |

### Pass/Fail Thresholds

| Metric | Pass | Fail |
|--------|------|------|
| App count | ≥ 6 | < 6 |
| Hallucinations | 0 | ≥ 1 |
| Broken links | ≤ 1 | ≥ 2 |
| Category relevance | ≥ 80% | < 80% |

### Phase 1: Build Gold Standard (One-time)

1. Run agent 10x across different categories
2. Log raw outputs to `alphy/`
3. Manually label each run (app exists? relevant? indie? recent?)
4. Save as `gold_standard.json`

**Labeling format:**

```json
{
  "input": "AI Photo/Video",
  "run_date": "2026-02-16",
  "labeled_apps": [
    {
      "name": "Remini",
      "exists": true,
      "cited": true,
      "relevant": true,
      "recent": true,
      "indie": false,
      "quality": "medium"
    }
  ]
}
```

### Phase 2: Regression Testing (Ongoing)

1. Future run executes
2. Compare output against gold standard → Pass/Fail
3. Run usefulness scorer → 0.0-1.0
4. Log everything to Braintrust
5. Failed runs get tagged with failure reason

**Evaluation flow:**

```python
def evaluate_run(output, gold_standard):
    # Fast checks first
    precision = calc_precision(output, gold_standard)
    hallucinations = count_hallucinations(output)

    valid_baseline = precision > 0.5 and hallucinations == 0

    # Always run LLM judges, but tag the result
    usefulness = usefulness_scorer(output)

    return {
        "valid_baseline": valid_baseline,
        "precision": precision,
        "hallucinations": hallucinations,
        "usefulness": usefulness,
    }
```

**Dashboard view:**

| Run | Date | Precision | Recall | Hallucinations | Usefulness | Pass/Fail |
|-----|------|-----------|--------|----------------|------------|-----------|
| v1 | Feb 16 | 75% | 60% | 2 | 0.7 | Fail |
| v2 | Feb 20 | 85% | 70% | 0 | 0.8 | Pass |
| v3 | Mar 1 | 80% | 75% | 1 | 0.85 | Fail |

### Maintenance

Gold standard goes stale. Apps get acquired, removed, or stop being relevant. **Refresh quarterly.**

---

## Your Next Steps

### Step 1: Build Gold Standard

1. Run agent 10x across different categories:
   ```bash
   uv run python src/main.py --categories "AI Photo/Video"
   uv run python src/main.py --categories "Health & Fitness"
   # ... etc
   ```
2. Outputs saved to `alphy/`
3. Manually label each run's apps (exists, relevant, indie, recent)
4. Save labels to `scorers/gold_standard.json`

### Step 2: UI Setup

1. Go to Braintrust → Scorers → + Scorer
2. Create scorer from `usefulness_scorer.md`
3. Set as LLM-as-a-judge with your prompt
4. (Optional) Add effectiveness and timeliness scorers later

### Step 3: Enable Logging

Already configured in `graph.py`. Verify `BRAINTRUST_API_KEY` is in `.env`:

```bash
# .env
BRAINTRUST_API_KEY=your_key_here
```

### Step 4: Run Regression Evals

Once gold standard exists:

```python
from braintrust import Eval

gold_standard = load_json("scorers/gold_standard.json")

Eval(
    "ALPHY Regression",
    data=lambda: [
        {"input": item["input"], "expected": item["labeled_apps"]}
        for item in gold_standard
    ],
    task=lambda input: run_alphy_workflow(input),
    scores=["usefulness", "precision", "hallucination_rate"],
)
```

### Step 5: Analyze Failures

Filter in Braintrust: `valid_baseline = false`

Tag failure reasons:
- `hallucinated_apps`
- `broken_links`
- `irrelevant_category`
- `stale_apps`

---

## Sources

- [Braintrust Scorers Guide](https://www.braintrust.dev/docs/guides/functions/scorers)
- [Evaluating Agents](https://www.braintrust.dev/docs/best-practices/agents)
- [How to Eval: The Braintrust Way](https://www.braintrust.dev/articles/how-to-eval)
- [Agent Evaluation Framework](https://www.braintrust.dev/articles/ai-agent-evaluation-framework)