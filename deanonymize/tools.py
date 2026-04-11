"""Web search tool for retriever agent.

Supports two backends:
  - tavily  (default, easiest setup — get a free key at https://tavily.com)
  - google  (uses Google Custom Search API, requires CSE ID)

The active backend is controlled by SEARCH_BACKEND in .env.
"""

import httpx
from config import settings


def search_web(query: str) -> str:
    """
    Search the web for information matching the given query.
    Returns titles, URLs, and content snippets of the top results.

    Args:
        query: A specific search query string targeted at finding identity information.

    Returns:
        Formatted search results as a string, or an error message.
    """
    if settings.search_backend == "google":
        return _search_google_cse(query)
    return _search_tavily(query)


def _search_tavily(query: str) -> str:
    if not settings.tavily_api_key:
        return "Error: TAVILY_API_KEY is not set. Add it to .env or switch SEARCH_BACKEND=google."
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.tavily_api_key)
        response = client.search(
            query=query,
            max_results=settings.max_search_results,
            include_answer=True,
        )

        parts = []
        if response.get("answer"):
            parts.append(f"Summary: {response['answer']}\n")

        for i, result in enumerate(response.get("results", []), 1):
            content = (result.get("content") or "")[:600]
            parts.append(
                f"[{i}] {result.get('title', 'No title')}\n"
                f"    URL: {result.get('url', '')}\n"
                f"    {content}"
            )

        return "\n\n".join(parts) if parts else "No results found."

    except Exception as e:
        return f"Search error (tavily): {e}"


def _search_google_cse(query: str) -> str:
    if not settings.google_cse_id:
        return "Error: GOOGLE_CSE_ID is not set. Add it to .env."
    try:
        params = {
            "key": settings.google_api_key,
            "cx": settings.google_cse_id,
            "q": query,
            "num": settings.max_search_results,
        }
        response = httpx.get(
            "https://www.googleapis.com/customsearch/v1", params=params, timeout=30
        )
        response.raise_for_status()
        items = response.json().get("items", [])

        parts = []
        for i, item in enumerate(items, 1):
            snippet = (item.get("snippet") or "")[:400]
            parts.append(
                f"[{i}] {item.get('title', 'No title')}\n"
                f"    URL: {item.get('link', '')}\n"
                f"    {snippet}"
            )

        return "\n\n".join(parts) if parts else "No results found."

    except Exception as e:
        return f"Search error (google cse): {e}"
