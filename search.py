"""
search.py - Free web search (Perplexity jaisa feature), DuckDuckGo se.
Koi API key nahi chahiye, bilkul free hai.
"""

from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 5) -> str:
    """Query search karta hai aur results ko ek readable text block mein deta hai."""
    try:
        results = list(DDGS().text(query, max_results=max_results))
    except Exception as e:
        return f"Search failed: {e}"

    if not results:
        return "No results found."

    lines = []
    for r in results:
        title = r.get("title", "")
        body = r.get("body", "")
        href = r.get("href", "")
        lines.append(f"- {title}: {body} (Source: {href})")
    return "\n".join(lines)