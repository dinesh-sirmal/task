"""
Thin wrapper around the Gemini SDK.

If no GEMINI_API_KEY is set, the client falls back to a local "mock" mode that
returns a canned but clearly-labelled response instead of crashing. This makes
it possible to run and demo the whole project (including streaming) with zero
API keys, then flip to a real LLM by just adding a key to .env.
"""
from typing import Iterator
from app.config import GEMINI_API_KEY, GEMINI_MODEL

_MOCK_MODE = not bool(GEMINI_API_KEY)


class LLMGenerationError(RuntimeError):
    """Raised when the configured LLM provider cannot complete a request."""

if not _MOCK_MODE:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        _model = genai.GenerativeModel(GEMINI_MODEL)
    except Exception:
        _model = genai.GenerativeModel("gemini-2.5-flash")


def _mock_answer(prompt: str) -> str:
    return (
        "[MOCK MODE - no GEMINI_API_KEY set] Based on the retrieved context above, "
        "here is a placeholder answer. Add a real GEMINI_API_KEY to your .env file "
        "to get actual LLM-generated answers."
    )


def generate(prompt: str) -> tuple[str, int]:
    """Non-streaming generation. Returns (answer_text, approx_tokens_used)."""
    if _MOCK_MODE:
        text = _mock_answer(prompt)
        return text, _approx_tokens(prompt + text)

    try:
        response = _model.generate_content(prompt)
    except Exception as exc:
        raise LLMGenerationError("Gemini generation failed") from exc
    text = response.text or ""
    tokens = _approx_tokens(prompt + text)
    # Gemini exposes real usage metadata when available; prefer it over the estimate.
    usage = getattr(response, "usage_metadata", None)
    if usage is not None:
        tokens = getattr(usage, "total_token_count", tokens)
    return text, tokens


def generate_stream(prompt: str) -> Iterator[str]:
    """Streaming generation. Yields text chunks as they arrive."""
    if _MOCK_MODE:
        text = _mock_answer(prompt)
        for word in text.split(" "):
            yield word + " "
        return

    try:
        response = _model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as exc:
        raise LLMGenerationError("Gemini streaming generation failed") from exc


def _approx_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token) used when real usage isn't available."""
    return max(1, len(text) // 4)


def is_mock_mode() -> bool:
    return _MOCK_MODE
