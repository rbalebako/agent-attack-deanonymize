# agent-attack-deanonymize

A multi-agent LLM tool for red-team evaluation of privacy-enhancing database measures. It attempts to de-anonymize pseudonymous identity records using orchestrated web research, and reports what was found and at what token/cost.

The primary output is a cost measurement: how expensive (in LLM tokens and USD) is a successful de-anonymization attempt? This helps organizations decide whether their anonymization strategy raises the bar high enough to make attacks economically impractical.

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

## Input format

Identity records are JSON objects in an array. Only `id` is required; the more fields provided, the richer the attack surface for testing.

```json
[
  {
    "id": "synth_001",
    "handle": "d3ep_w4ters",
    "location_hint": "Pacific Northwest, UTC-8",
    "bio": "ML engineer by day, amateur radio operator by night.",
    "interests": ["distributed systems", "amateur radio", "espresso"],
    "platform_hints": ["posts in r/MachineLearning", "GitHub repos in Rust"],
    "writing_samples": ["Anyone else finding k3s more enjoyable than full k8s?"],
    "metadata": {
      "estimated_age_range": "35-45"
    }
  }
]
```

See `data/synthetic_sample.json` for three complete examples.

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
