"""
Returns the configured LLM for use in LlmAgent definitions.

  LLM_BACKEND=google  →  returns the Gemini model name string (default)
  LLM_BACKEND=ollama  →  returns a LiteLlm wrapper pointing at local Ollama

The return value is accepted directly as the `model` argument to LlmAgent.
"""

from __future__ import annotations
from typing import Union


def get_model() -> Union[str, object]:
    from config import settings

    if settings.llm_backend == "ollama":
        import os
        # LiteLLM reads OLLAMA_API_BASE to locate the Ollama server.
        os.environ.setdefault("OLLAMA_API_BASE", settings.ollama_base_url)
        try:
            from google.adk.models.lite_llm import LiteLlm
        except ImportError as e:
            raise ImportError(
                "LiteLlm support requires the 'litellm' package. "
                "Run: pip install litellm"
            ) from e
        return LiteLlm(model=f"ollama/{settings.ollama_model}")

    # Default: Gemini via Google ADK
    if not settings.google_api_key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. Add it to .env or set LLM_BACKEND=ollama."
        )
    return settings.gemini_model
