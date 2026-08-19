"""Simple fallback tool (mock web search) for demo purposes.

This module provides a very small, easy-to-read fallback used when the
knowledge base does not contain a confident match for the user's question.
In production you would replace this with a real web search or external
tool call. For tests and demos this function returns a clear, friendly
message explaining why the fallback was used.
"""

from typing import Any


def web_search_mock(question: str) -> str:
    """Return a beginner-friendly fallback message.

    Args:
        question: The user's original question (kept for context/logging).

    Returns:
        A human-readable string explaining that the system could not find a
        confident answer in the indexed documentation and that a real web
        search would be used in production.
    """

    # Keep the message short, clear, and deterministic so tests can rely on it.
    return (
        "Fallback response: I couldn't find enough information in the indexed "
        "CloudSync documentation to answer your question confidently.\n\n"
        "What this means:\n"
        "- The internal docs didn't contain a close match for your question.\n"
        "- To avoid making up answers, the system used the fallback path instead.\n\n"
        "In a real system this would call an external web-search API and return "
        "real results. For this demo the response is a static, easy-to-read message."
    )


__all__: list[str] = ["web_search_mock"]
