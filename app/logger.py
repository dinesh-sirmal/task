"""
Structured (JSON) logging so latency and token usage per request are easy to
grep / ship to a log aggregator later.
"""
import json
import logging
import sys

logger = logging.getLogger("rag_api")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_handler)
logger.propagate = False


def log_request(
    question: str,
    used_fallback: bool,
    retrieval_time_ms: float,
    generation_time_ms: float,
    total_time_ms: float,
    approx_tokens_used: int,
    num_sources: int,
):
    record = {
        "event": "query_completed",
        "question": question[:200],
        "used_fallback": used_fallback,
        "retrieval_time_ms": round(retrieval_time_ms, 2),
        "generation_time_ms": round(generation_time_ms, 2),
        "total_time_ms": round(total_time_ms, 2),
        "approx_tokens_used": approx_tokens_used,
        "num_sources": num_sources,
    }
    logger.info(json.dumps(record))


def log_generation_failure(question: str, error: Exception) -> None:
    """Log provider failures without exposing their details to API clients."""
    logger.warning(json.dumps({
        "event": "llm_generation_failed",
        "question": question[:200],
        "error_type": type(error).__name__,
    }))
