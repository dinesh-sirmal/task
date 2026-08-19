import importlib

import app.config as config
from app import rag_engine


def _make_chunk(distance: float, source: str = "doc.md", chunk_id: int = 0):
    return {"text": "some text", "source": source, "chunk_id": chunk_id, "distance": distance}


def test_relevant_question_used_fallback_false(monkeypatch):
    # Ensure threshold is relaxed for test
    config.RAG_SIMILARITY_THRESHOLD = 0.75
    config.RAG_SIMILARITY_COMPARISON = "distance"

    # Mock vector store to return a very close match
    monkeypatch.setattr(rag_engine.vector_store, "query", lambda q: [
        _make_chunk(0.1, "02_authentication.md", 0)
    ])

    # Mock LLM generation
    monkeypatch.setattr(rag_engine, "generate", lambda prompt: ("LLM answer", 10))

    res = rag_engine.answer_query("How does authentication work?")
    assert res["used_fallback"] is False
    assert res["sources"]
    assert "LLM answer" in res["answer"]


def test_unrelated_question_used_fallback_true(monkeypatch):
    config.RAG_SIMILARITY_THRESHOLD = 0.5
    config.RAG_SIMILARITY_COMPARISON = "distance"

    # No chunks returned (no match)
    monkeypatch.setattr(rag_engine.vector_store, "query", lambda q: [])

    # Ensure generate would not be called; if it is, fail the test
    def fail_generate(prompt):
        raise AssertionError("LLM should not be called for unrelated questions")

    monkeypatch.setattr(rag_engine, "generate", fail_generate)

    res = rag_engine.answer_query("What is CloudSync's pricing?")
    assert res["used_fallback"] is True
    assert "I couldn't find enough information" in res["answer"] or "Fallback response" in res["answer"]


def test_borderline_threshold(monkeypatch):
    # Set threshold to 0.5
    config.RAG_SIMILARITY_THRESHOLD = 0.5
    config.RAG_SIMILARITY_COMPARISON = "distance"

    # Exactly at threshold -> considered confident (<=)
    monkeypatch.setattr(rag_engine.vector_store, "query", lambda q: [_make_chunk(0.5)])
    monkeypatch.setattr(rag_engine, "generate", lambda prompt: ("OK", 5))
    res_ok = rag_engine.answer_query("Borderline question?")
    assert res_ok["used_fallback"] is False

    # Slightly worse than threshold -> fallback
    monkeypatch.setattr(rag_engine.vector_store, "query", lambda q: [_make_chunk(0.5001)])
    res_fallback = rag_engine.answer_query("Borderline question 2?")
    assert res_fallback["used_fallback"] is True


def test_paraphrased_question_used_fallback_false(monkeypatch):
    config.RAG_SIMILARITY_THRESHOLD = 0.75
    config.RAG_SIMILARITY_COMPARISON = "distance"

    # Paraphrase still returns a close chunk
    monkeypatch.setattr(rag_engine.vector_store, "query", lambda q: [_make_chunk(0.2, "03_files_endpoint.md")])
    monkeypatch.setattr(rag_engine, "generate", lambda prompt: ("File upload answer", 8))
    res = rag_engine.answer_query("How to upload a file?")
    assert res["used_fallback"] is False
    assert any(s["source"] == "03_files_endpoint.md" or "files" in s["snippet"].lower() for s in res["sources"])


def test_unknown_question_no_hallucination(monkeypatch):
    config.RAG_SIMILARITY_THRESHOLD = 0.4
    config.RAG_SIMILARITY_COMPARISON = "distance"

    # No relevant chunks
    monkeypatch.setattr(rag_engine.vector_store, "query", lambda q: [])

    # If generate is called, fail the test
    def fail_generate(prompt):
        raise AssertionError("LLM must not be called when fallback triggers")

    monkeypatch.setattr(rag_engine, "generate", fail_generate)

    res = rag_engine.answer_query("Who founded CloudSync?")
    assert res["used_fallback"] is True
    assert "CloudSync" in res["answer"] or "Fallback response" in res["answer"]
