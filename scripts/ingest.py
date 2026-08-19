"""
Standalone ingestion script. Run this once (and again whenever your docs change):

    python scripts/ingest.py

It reads every file in data/docs/, chunks it, embeds it, and stores it in the
local ChromaDB folder (./chroma_db). The FastAPI app just reads from that
folder -- it never re-ingests automatically.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ingestion import load_and_chunk_documents
from app.vector_store import vector_store


def main():
    print("Loading and chunking documents...")
    chunks = load_and_chunk_documents()
    print(f"Produced {len(chunks)} chunks from {len(set(c['source'] for c in chunks))} file(s).")

    print("Resetting existing collection...")
    vector_store.reset()

    print("Embedding and storing chunks in ChromaDB (this may take a moment)...")
    vector_store.add_chunks(chunks)

    print(f"Done. Collection now has {vector_store.count()} chunks.")


if __name__ == "__main__":
    main()
