from google.adk.agents import LlmAgent

from .prompts import EXTRACTOR_INSTRUCTION, RETRIEVER_INSTRUCTION, SUMMARIZER_INSTRUCTION
from .tools import search_web
from .model_factory import get_model

_model = get_model()

retriever_agent = LlmAgent(
    name="retriever",
    model=_model,
    description=(
        "Searches the web for information matching a pseudonymous identity. "
        "Input: a focused search query string. "
        "Output: relevant titles, URLs, and content snippets."
    ),
    instruction=RETRIEVER_INSTRUCTION,
    tools=[search_web],
)

extractor_agent = LlmAgent(
    name="extractor",
    model=_model,
    description=(
        "Extracts and structures PII from raw web search results. "
        "Input: raw search result text from the retriever. "
        "Output: categorized PII findings with confidence levels and source URLs."
    ),
    instruction=EXTRACTOR_INSTRUCTION,
    tools=[],
)

summarizer_agent = LlmAgent(
    name="summarizer",
    model=_model,
    description=(
        "Produces a final de-anonymization assessment report. "
        "Input: all findings accumulated across retriever and extractor calls. "
        "Output: structured report evaluating attack success and privacy measure effectiveness."
    ),
    instruction=SUMMARIZER_INSTRUCTION,
    tools=[],
)
