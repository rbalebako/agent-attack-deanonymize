# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Red-team tool for a contracted security engagement. Runs a multi-agent de-anonymization attack against pseudonymous identity records to evaluate whether privacy-enhancing database measures can withstand an LLM-based attack, and to measure attack cost in tokens/USD. Operates on synthetic data only.

## Setup

```bash
cp .env.example .env          # fill in GOOGLE_API_KEY and TAVILY_API_KEY
pip install -r requirements.txt
```

## Running attacks

```bash
# Attack all records in a file
python main.py data/synthetic_sample.json

# Attack a single identity
python main.py data/synthetic_sample.json --id synth_001

# Stream agent events in real time
python main.py data/synthetic_sample.json --id synth_001 --verbose

# Write results to a specific directory
python main.py data/synthetic_sample.json --output-dir results/

# Run via ADK CLI (interactive dev mode)
adk run deanonymize
adk web  # opens ADK dev UI at localhost:8000
```

Results are written as `result_<id>.json` in the output directory.

## Architecture

Four agents wired with Google ADK (`google-adk`), all using Gemini:

```
main.py
  └─ Runner(root_agent)
       └─ strategist  [deanonymize/agent.py]         ← root agent, orchestrates
            ├─ AgentTool → retriever  [sub_agents.py]  ← calls search_web tool
            ├─ AgentTool → extractor  [sub_agents.py]  ← no tools, pure reasoning
            └─ AgentTool → summarizer [sub_agents.py]  ← no tools, pure reasoning
```

**Strategist** (root): Plans the attack, decides which agents to call and in what order, enforces the 10-call iteration budget via its system prompt. Calls the other three as ADK `AgentTool`s.

**Retriever**: Given a query string from the strategist, calls `search_web` (in `deanonymize/tools.py`) 1–3 times and returns raw results. The only agent with a tool.

**Extractor**: Receives raw retriever output, returns structured PII with `HIGH/MEDIUM/LOW` confidence and source URLs.

**Summarizer**: Receives all accumulated findings, produces the final structured assessment report used to evaluate privacy measures.

## Key files

| File | Purpose |
|---|---|
| `deanonymize/prompts.py` | All four system prompts — primary place to tune agent behavior |
| `deanonymize/tools.py` | `search_web` function: Tavily (default) or Google CSE backend |
| `cost_tracker.py` | Accumulates token counts from ADK event stream; computes USD cost |
| `models.py` | `IdentityRow` (input schema) and `AttackResult` (output schema) |
| `config.py` | `Settings` via pydantic-settings; reads `.env` |
| `data/synthetic_sample.json` | Three synthetic identity records for testing |

## Iteration budget

The strategist is instructed via its system prompt (`MAX_ITERATIONS`, default 10) to stay within the budget. This is soft enforcement (prompt-level). The budget is intentionally not hard-enforced in code so the strategist has flexibility on the final call to summarizer.

## Token cost tracking

`CostTracker` accumulates `prompt_token_count` and `candidates_token_count` from `event.usage_metadata` on each ADK event in the runner stream. Pricing constants in `cost_tracker.py` are set for Gemini 2.0 Flash — update them if switching models.

## Search backends

- **Tavily** (default): set `TAVILY_API_KEY` in `.env`. Free tier available.
- **Google CSE**: set `SEARCH_BACKEND=google`, `GOOGLE_CSE_ID`, and `GOOGLE_API_KEY`. Useful if running against Vertex AI with built-in grounding.

## Adding identity records

`data/synthetic_sample.json` accepts a JSON array of `IdentityRow` objects. Required field: `id`. All others are optional but more fields = richer attack surface for testing.

## ADK notes

- `deanonymize/__init__.py` exports `root_agent` so `adk run deanonymize` works from the project root.
- ADK event field names (`author`, `usage_metadata`, `is_final_response()`) should match `google-adk>=0.3.0`. If an upgrade breaks event parsing, check `_extract_usage()` and `_print_event_verbose()` in `main.py`.
- If switching to Vertex AI, you can replace the custom `search_web` function with ADK's built-in `google_search` tool (grounding via Vertex).
