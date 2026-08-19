"""
Wraps ChromaDB + sentence-transformers so the rest of the app never talks to
either library directly. Swap the embedding model or vector DB here only.
"""
import chromadb
from chromadb.errors import InvalidCollectionException
from chromadb.utils import embedding_functions
from app.config import CHROMA_PERSIST_DIR, COLLECTION_NAME, EMBEDDING_MODEL_NAME, TOP_K


class VectorStore:
    def __init__(self):
        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )
        self._client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        self._collection = self._get_or_recreate_collection()

    def _get_or_recreate_collection(self):
        try:
            collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
            collection.count()
            return collection
        except Exception:
            try:
                self._client.delete_collection(COLLECTION_NAME)
            except Exception:
                pass
            return self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )

    def _ensure_collection(self):
        try:
            self._collection.count()
            return
        except InvalidCollectionException:
            self._collection = self._get_or_recreate_collection()
        except Exception:
            self._collection = self._get_or_recreate_collection()

    def reset(self):
        """Delete and recreate the collection (used before a fresh ingest run)."""
        try:
            self._client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[dict]):
        if not chunks:
            return
        self._collection.add(
            ids=[c["id"] for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[{"source": c["source"], "chunk_id": c["chunk_id"]} for c in chunks],
        )

    def count(self) -> int:
        self._ensure_collection()
        return self._collection.count()

    def query(self, question: str, top_k: int = TOP_K) -> list[dict]:
        """
        Returns a list of {text, source, chunk_id, distance}, sorted by
        relevance (lowest distance = most similar, since we use cosine space).
        """
        self._ensure_collection()
        results = self._collection.query(query_texts=[question], n_results=top_k)

        out = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances):
            out.append({
                "text": doc,
                "source": meta.get("source", "unknown"),
                "chunk_id": meta.get("chunk_id", -1),
                "distance": dist,
            })
        return out


# Single shared instance used across the app (loading the embedding model is slow,
# so we only want to do it once per process).
vector_store = VectorStore()
