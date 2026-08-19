"""
All tunable settings live here, loaded from environment variables (.env file).
Keeping config in one place makes the whole project easier to read/change.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

_DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
_LEGACY_GEMINI_MODELS = {
    "gemini-1.5-flash": _DEFAULT_GEMINI_MODEL,
    "gemini-1.5-flash-latest": _DEFAULT_GEMINI_MODEL,
    "gemini-1.5-pro": _DEFAULT_GEMINI_MODEL,
}

_configured_model = (os.getenv("GEMINI_MODEL") or _DEFAULT_GEMINI_MODEL).strip()
GEMINI_MODEL = _LEGACY_GEMINI_MODELS.get(_configured_model, _configured_model) or _DEFAULT_GEMINI_MODEL

# --- Embeddings / Vector store ---
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "cloudsync_docs")

# --- Chunking ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))       # characters per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120")) # overlap between chunks

# --- Retrieval / RAG behaviour ---
TOP_K = int(os.getenv("TOP_K", "4"))
# The collection is explicitly configured with cosine distance (lower = more similar).
# Backwards-compatible distance threshold (kept for reference).
DISTANCE_THRESHOLD = float(os.getenv("DISTANCE_THRESHOLD", "0.75"))

# New, configurable RAG threshold. This value's meaning depends on
# `RAG_SIMILARITY_COMPARISON` below (either 'distance' or 'similarity').
# Default keeps previous behaviour: lower distance is better and 0.75 is the
# maximum acceptable distance.
RAG_SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", str(DISTANCE_THRESHOLD)))

# How to interpret the vector-store metric when making the fallback decision.
# - 'distance' means lower is better (e.g. cosine distance).
# - 'similarity' means higher is better (e.g. cosine similarity_score).
RAG_SIMILARITY_COMPARISON = os.getenv("RAG_SIMILARITY_COMPARISON", "distance").lower()

# --- Docs source ---
DOCS_DIR = os.getenv("DOCS_DIR", "./data/docs")
