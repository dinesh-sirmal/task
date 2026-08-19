"""
Fallback tool triggered when retrieval confidence is too low (i.e. the question
is probably not covered by the internal knowledge base). In a real system this
would call a real web search API; here it's a clearly-labelled mock so the
behaviour is deterministic and doesn't need extra API keys.
"""


def web_search_mock(question: str) -> str:
    return (
        "I couldn't find enough relevant information in the internal knowledge base "
        "to answer this confidently. This looks like it's outside the scope of the "
        "indexed documentation (CloudSync API docs). "
        "[Fallback tool] In a production system this would route to a live web search; "
        "for this demo it returns this placeholder instead."
    )
