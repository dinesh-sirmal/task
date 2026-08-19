"""
Orchestrates the full RAG logic flow described in the brief:
  1. Retrieve relevant chunks (semantic similarity)
  2. If confidence is too low -> fallback tool
  3. Otherwise synthesize an answer with the LLM, citing sources
Also measures retrieval vs generation latency and token usage for logging.
"""
import time
from typing import Iterator, Tuple, List, Dict

from app.vector_store import vector_store
from app.guardrails import (
    looks_like_prompt_injection,
    sanitize_question,
    is_confident_enough,
    build_prompt,
)
from app.fallback_tool import web_search_mock
from app.llm_client import LLMGenerationError, generate, generate_stream, _approx_tokens
from app.logger import log_generation_failure, log_request

INJECTION_REFUSAL = (
    "I can't follow instructions embedded in a question -- I can only answer questions "
    "about the CloudSync API documentation. Please rephrase your question."
)


def _llm_failure_answer(chunks: List[Dict]) -> str:
    """Provide a transparent, source-grounded response when Gemini is unavailable."""
    sources = ", ".join(sorted({chunk["source"] for chunk in chunks}))
    return (
        "The relevant documentation was retrieved, but the configured LLM is "
        "temporarily unavailable. Please try again shortly. "
        f"Relevant source(s): {sources}."
    )


def _source_payload(chunks: List[Dict]) -> List[Dict]:
    return [
        {"source": c["source"], "chunk_id": c["chunk_id"], "snippet": c["text"][:200], "distance": c["distance"]}
        for c in chunks
    ]


def retrieve(question: str) -> Tuple[List[Dict], float]:
    start = time.perf_counter()
    chunks = vector_store.query(question)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return chunks, elapsed_ms


def answer_query(question: str) -> dict:
    """Non-streaming path. Returns a fully-populated response dict."""
    total_start = time.perf_counter()
    question = sanitize_question(question)

    if looks_like_prompt_injection(question):
        total_ms = (time.perf_counter() - total_start) * 1000
        log_request(question, True, 0, 0, total_ms, 0, 0, None, None)
        return {
            "answer": INJECTION_REFUSAL,
            "used_fallback": True,
            "sources": [],
            "retrieval_time_ms": 0.0,
            "generation_time_ms": 0.0,
            "total_time_ms": total_ms,
            "approx_tokens_used": 0,
        }

    chunks, retrieval_ms = retrieve(question)

    is_confident, best_score = is_confident_enough(chunks)
    configured_threshold = __import__("app.config", fromlist=["RAG_SIMILARITY_THRESHOLD"]).RAG_SIMILARITY_THRESHOLD

    if not is_confident:
        gen_start = time.perf_counter()
        answer = web_search_mock(question)
        generation_ms = (time.perf_counter() - gen_start) * 1000
        total_ms = (time.perf_counter() - total_start) * 1000
        tokens = _approx_tokens(answer)
        log_request(question, True, retrieval_ms, generation_ms, total_ms, tokens, 0, best_score, configured_threshold)
        return {
            "answer": answer,
            "used_fallback": True,
            "sources": [],
            "retrieval_time_ms": retrieval_ms,
            "generation_time_ms": generation_ms,
            "total_time_ms": total_ms,
            "approx_tokens_used": tokens,
        }

    prompt = build_prompt(question, chunks)
    gen_start = time.perf_counter()
    try:
        answer, tokens = generate(prompt)
    except LLMGenerationError as exc:
        generation_ms = (time.perf_counter() - gen_start) * 1000
        total_ms = (time.perf_counter() - total_start) * 1000
        answer = _llm_failure_answer(chunks)
        tokens = _approx_tokens(answer)
        log_generation_failure(question, exc)
        log_request(question, True, retrieval_ms, generation_ms, total_ms, tokens, len(chunks), best_score, configured_threshold)
        return {
            "answer": answer,
            "used_fallback": True,
            "sources": _source_payload(chunks),
            "retrieval_time_ms": retrieval_ms,
            "generation_time_ms": generation_ms,
            "total_time_ms": total_ms,
            "approx_tokens_used": tokens,
        }
    generation_ms = (time.perf_counter() - gen_start) * 1000
    total_ms = (time.perf_counter() - total_start) * 1000

    log_request(question, False, retrieval_ms, generation_ms, total_ms, tokens, len(chunks), best_score, configured_threshold)

    return {
        "answer": answer,
        "used_fallback": False,
        "sources": _source_payload(chunks),
        "retrieval_time_ms": retrieval_ms,
        "generation_time_ms": generation_ms,
        "total_time_ms": total_ms,
        "approx_tokens_used": tokens,
    }


def answer_query_stream(question: str) -> Iterator[str]:
    """
    Streaming path used by the SSE endpoint. Yields plain text chunks.
    Retrieval still happens up-front (it's fast); only generation is streamed,
    matching how most real RAG streaming implementations work.
    """
    total_start = time.perf_counter()
    question = sanitize_question(question)

    if looks_like_prompt_injection(question):
        yield INJECTION_REFUSAL
        log_request(question, True, 0, 0, (time.perf_counter() - total_start) * 1000, 0, 0, None, None)
        return

    chunks, retrieval_ms = retrieve(question)

    is_confident, best_score = is_confident_enough(chunks)
    configured_threshold = __import__("app.config", fromlist=["RAG_SIMILARITY_THRESHOLD"]).RAG_SIMILARITY_THRESHOLD

    if not is_confident:
        answer = web_search_mock(question)
        for word in answer.split(" "):
            yield word + " "
        total_ms = (time.perf_counter() - total_start) * 1000
        log_request(question, True, retrieval_ms, 0, total_ms, _approx_tokens(answer), 0, best_score, configured_threshold)
        return

    prompt = build_prompt(question, chunks)
    gen_start = time.perf_counter()
    full_answer = ""
    try:
        for piece in generate_stream(prompt):
            full_answer += piece
            yield piece
    except LLMGenerationError as exc:
        generation_ms = (time.perf_counter() - gen_start) * 1000
        total_ms = (time.perf_counter() - total_start) * 1000
        answer = _llm_failure_answer(chunks)
        log_generation_failure(question, exc)
        log_request(question, True, retrieval_ms, generation_ms, total_ms, _approx_tokens(answer), len(chunks), best_score, configured_threshold)
        yield answer
        return
    generation_ms = (time.perf_counter() - gen_start) * 1000
    total_ms = (time.perf_counter() - total_start) * 1000
    tokens = _approx_tokens(prompt + full_answer)
    log_request(question, False, retrieval_ms, generation_ms, total_ms, tokens, len(chunks), best_score, configured_threshold)
