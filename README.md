# agent-attack-deanonymize

A multi-agent LLM tool for red-team evaluation of privacy-enhancing database measures. It attempts to de-anonymize pseudonymous identity records using orchestrated web research, and reports what was found and at what token/cost.

The primary output is a cost measurement: how expensive (in LLM tokens and USD) is a successful de-anonymization attempt? This helps organizations decide whether their anonymization strategy raises the bar high enough to make attacks economically impractical.

---

## Status

_Last updated: 2026-11-01_

**Phase: pipeline built, not yet validated end-to-end.** The code is complete enough to run, but no attack results have been recorded yet.

### Done

- [x] Four-agent ADK pipeline (strategist → retriever / extractor / summarizer via `AgentTool`)
- [x] Web search tool with Tavily (default) and Google CSE backends
- [x] Input schema reshaped to the SMS click-tracking DataFrame format (`IdentityRow`)
- [x] Synthetic test set: 26 records (`row_001`–`row_003` mixed GB/DE/IN, `row_ie_001`–`row_ie_023` Ireland-based)
- [x] Token/USD cost tracking per run (`CostTracker`, Gemini 2.0 Flash pricing)
- [x] Pluggable LLM backend: Gemini (default) or local Ollama via LiteLLM
- [x] Runner hardening: exponential backoff on 429 rate limits, per-record JSON output
- [x] `.gitignore` for `.env`, `__pycache__/`, `results/`; old `__pycache__/` files removed from the repo
- [x] Unit tests (`pytest`) for `IdentityRow`, `CostTracker`, ADK event parsing, and the sample data

### Next up

- [ ] **First real run:** attack the synthetic set end-to-end and check in a baseline in `results/` (or a summary of it)
- [ ] **Validate token accounting:** confirm ADK `usage_metadata` captures sub-agent calls made through `AgentTool`, not only strategist turns
- [ ] **Fix `iterations_used`:** it currently counts every event that carries usage metadata, not sub-agent calls
- [ ] **Split `findings` and `summary`:** both currently hold the strategist's final response
- [ ] **More tests:** cover the runner loop in `run_attack()` with a stubbed ADK runner, and `search_web` with mocked backends
- [ ] **Aggregate reporting:** cost and success rate across all records, compared across anonymization variants
- [ ] **Ollama path:** confirm tool-calling works with `llama3.2` / `mistral`; record wall-clock time, since Ollama runs report $0
- [ ] **Usage safeguards:** see [Preventing misuse](#preventing-misuse)

---

## Authorization requirement

> **This tool must only be run under a signed rules of engagement or equivalent written authorization from the data owner.**
>
> Unauthorized de-anonymization of real individuals may violate GDPR, CCPA, the Computer Fraud and Abuse Act, and equivalent laws in your jurisdiction. The authors accept no liability for misuse.
>
> Intended use cases:
> - Contracted red-team or penetration testing engagements with explicit written scope
> - Internal privacy audits on data you own or are authorized to test
> - Academic research under an approved IRB protocol
> - Testing against synthetic or fully consented data
>
> **Do not run this tool against real individuals without authorization.**

### Preventing misuse

The individual parts here (LLM agents plus web search) are easy to get, so a determined attacker could build something similar. These steps keep *this* tool from making that easier:

- **Keep the repository private.** Share it only with people named in the engagement. Publish findings and cost figures, not the working prompts or orchestration code.
- **Limit who holds API keys.** Use per-engagement Gemini and Tavily keys with spending caps, and revoke them when the engagement ends.
- **Log every run.** Record who ran what, against which input file, and when, so runs can be checked against the authorized scope.
- **Planned: enforce scope in code.** For example, refuse input files that aren't explicitly marked as synthetic or in-scope.
- **Report through responsible disclosure.** Deliver results to the data owner, and treat result files as sensitive because they show which fields leak identity.

---

## How it works

Four agents are orchestrated via [Google ADK](https://google.github.io/adk-docs/) and Gemini:

```
Strategist (root)
  ├── Retriever  — searches the web for clues matching the identity
  ├── Extractor  — structures raw results into PII findings with confidence levels
  └── Summarizer — produces a final assessment report
```

The **Strategist** receives a pseudonymous identity record and coordinates up to 10 calls across the other three agents. It decides which search angles to pursue, when to refine, and when enough evidence has been gathered to produce a final report.

The **Summarizer**'s report rates each field of the original identity record as `STRONG / WEAK / NEUTRAL` from a privacy perspective, and recommends specific changes to harden the anonymization strategy — the primary output for privacy improvement work.

---

## Setup

**Prerequisites:** Python 3.11+, a [Gemini API key](https://aistudio.google.com/app/apikey), and a [Tavily API key](https://tavily.com) (free tier).

```bash
git clone <repo>
cd agent-attack-deanonymize

pip install -r requirements.txt

cp .env.example .env
# Edit .env — fill in GOOGLE_API_KEY and TAVILY_API_KEY
```

### Alternative search backend

If you prefer Google Custom Search over Tavily, set in `.env`:

```
SEARCH_BACKEND=google
GOOGLE_CSE_ID=your_custom_search_engine_id
```

---

## Usage

```bash
# Attack all records in a file
python main.py data/synthetic_sample.json

# Attack a single identity by ID
python main.py data/synthetic_sample.json --id synth_001

# Stream agent events in real time (shows each agent's reasoning)
python main.py data/synthetic_sample.json --id synth_001 --verbose

# Write results to a specific directory
python main.py data/synthetic_sample.json --output-dir results/
```

Results are written as `result_<id>.json` per identity.

### Via ADK CLI

```bash
adk run deanonymize    # interactive terminal session
adk web                # opens the ADK dev UI at localhost:8000
```

---

## Running tests

```bash
python -m pytest
```

The tests live in `tests/` and need no API keys or network access. `tests/conftest.py` sets a dummy `GOOGLE_API_KEY` so the agents can be imported, but no model or search calls are made.

---

## Input format

Identity records are JSON objects in an array, one per row of the SMS click-tracking DataFrame. Only `sms_text` is required. If `id` is omitted, it is generated as `row_<sha1[:8]>` of `sms_text`.

```json
[
  {
    "id": "row_001",
    "sms_text": "Hi James, your Barclays verification code is 847291. ...",
    "country": "GB",
    "location": "Manchester",
    "inferred_language": "en-GB",
    "display_type": "mobile",
    "click_time": "2024-11-14T09:23:41Z",
    "clicked_url": "https://barclayscards.co.uk/verify?token=xK9mP2&ref=james.whitfield"
  }
]
```

See `data/synthetic_sample.json` for 26 synthetic examples.

---

## Output

Each `result_<id>.json` contains:

| Field | Description |
|---|---|
| `findings` | Full text of the Summarizer's report |
| `success` | Whether a final response was produced |
| `iterations_used` | Number of sub-agent calls made |
| `total_input_tokens` | Accumulated prompt tokens across all agents |
| `total_output_tokens` | Accumulated completion tokens across all agents |
| `cost_usd` | Estimated USD cost for the run (Gemini 2.0 Flash pricing) |
| `agent_call_counts` | Breakdown of calls per agent |

The Summarizer's report includes a per-field privacy rating (`STRONG / WEAK / NEUTRAL`) and specific recommendations for hardening the anonymization strategy.

---

## Configuration

All settings are in `.env` (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Gemini API key (required) |
| `TAVILY_API_KEY` | — | Tavily search key (required unless using Google CSE) |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Model used for all agents |
| `MAX_ITERATIONS` | `10` | Soft cap on total sub-agent calls per run |
| `MAX_SEARCH_RESULTS` | `5` | Results returned per search query |
| `SEARCH_BACKEND` | `tavily` | `tavily` or `google` |

---

## Tuning agent behavior

All system prompts are in `deanonymize/prompts.py`. This is the primary file to edit when:

- Adjusting the Strategist's search strategy or iteration discipline
- Changing what PII categories the Extractor looks for
- Modifying the structure or focus of the Summarizer's report

Token pricing constants (for cost estimates) are at the top of `cost_tracker.py` — update if switching models.
