"""
FastAPI application entrypoint.

Run with:  uvicorn app.main:app --reload
Docs at:   http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models import QueryRequest, QueryResponse
from app.rag_engine import answer_query, answer_query_stream
from app.vector_store import vector_store
from app.llm_client import is_mock_mode

app = FastAPI(
    title="RAG & Agent API",
    description="Retrieval-Augmented Generation API over a small technical knowledge base.",
    version="1.0.0",
)

# Wide-open CORS is fine for a local assessment project; tighten this for real deployments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "indexed_chunks": vector_store.count(),
        "llm_mock_mode": is_mock_mode(),
    }


@app.post("/api/v1/query")
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")

    if request.stream:
        return StreamingResponse(
            _sse_generator(request.question),
            media_type="text/event-stream",
        )

    try:
        result = answer_query(request.question)
    except Exception as exc:
        # Retrieval/storage failures should be actionable for clients, not opaque 500s.
        raise HTTPException(status_code=503, detail="The RAG service is temporarily unavailable. Please try again shortly.") from exc
    return QueryResponse(**result)


def _sse_generator(question: str):
    """Formats each streamed text piece as a proper Server-Sent Event."""
    for piece in answer_query_stream(question):
        # SSE format: each event is "data: <payload>\n\n"
        safe_piece = piece.replace("\n", "\\n")
        yield f"data: {safe_piece}\n\n"
    yield "event: done\ndata: [DONE]\n\n"
