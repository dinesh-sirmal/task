"""
Ingestion & Indexing Pipeline.

Reads every .md / .txt / .pdf file from DOCS_DIR, splits each into overlapping
chunks (simple character-based sliding window -- easy to understand, no extra
NLP dependency needed), and returns a flat list of chunk dicts ready to embed.
"""
import os
from typing import List, Dict
from app.config import DOCS_DIR, CHUNK_SIZE, CHUNK_OVERLAP


def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _read_pdf_file(path: str) -> str:
    # Imported lazily so the app doesn't require pypdf if you only use markdown docs.
    from pypdf import PdfReader

    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Simple sliding-window chunker over raw characters."""
    text = " ".join(text.split())  # collapse whitespace/newlines
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap  # step forward, keeping some overlap for context continuity
    return chunks


def load_and_chunk_documents(docs_dir: str = DOCS_DIR) -> List[Dict]:
    """
    Returns a list of dicts: {id, text, source, chunk_id}
    `id` is unique per chunk (used as the ChromaDB document id).
    """
    if not os.path.isdir(docs_dir):
        raise FileNotFoundError(f"Docs directory not found: {docs_dir}")

    all_chunks: List[Dict] = []

    for filename in sorted(os.listdir(docs_dir)):
        path = os.path.join(docs_dir, filename)
        if not os.path.isfile(path):
            continue

        ext = filename.lower().rsplit(".", 1)[-1]
        if ext in ("md", "txt"):
            raw_text = _read_text_file(path)
        elif ext == "pdf":
            raw_text = _read_pdf_file(path)
        else:
            continue  # skip unsupported file types

        chunks = chunk_text(raw_text)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "id": f"{filename}::chunk_{i}",
                "text": chunk,
                "source": filename,
                "chunk_id": i,
            })

    return all_chunks
