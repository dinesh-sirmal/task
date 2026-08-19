"""Pydantic request/response models for the API."""
from pydantic import BaseModel, Field
from typing import List, Optional


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The user's question")
    stream: bool = Field(default=False, description="If true, response is Server-Sent Events")


class SourceChunk(BaseModel):
    source: str
    chunk_id: int
    snippet: str
    distance: float


class QueryResponse(BaseModel):
    answer: str
    used_fallback: bool
    sources: List[SourceChunk]
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float
    approx_tokens_used: int
