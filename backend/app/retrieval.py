"""Local embedding and persistent semantic retrieval for DocLens."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb

from app.ingestion import (
    DEFAULT_CORPUS_DIR,
    DocumentChunk,
    chunk_documents,
    load_bundled_documents,
)


DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_CHROMA_PATH = Path(__file__).resolve().parents[2] / "data" / "chroma"
DEFAULT_COLLECTION_NAME = "doclens_documents"
TOP_K = 3

EmbeddingFunction = Callable[[Sequence[str]], Sequence[Sequence[float]]]


@dataclass(frozen=True, slots=True)
class SearchResult:
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float


class SentenceTransformerEmbedding:
    """Load one local Sentence Transformer and reuse it for documents and queries."""

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def __call__(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()


class PersistentRetriever:
    """A small Chroma-backed index with an explicit embedding seam for tests."""

    def __init__(
        self,
        *,
        persist_directory: Path = DEFAULT_CHROMA_PATH,
        embedding_function: EmbeddingFunction | None = None,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ) -> None:
        persist_directory.mkdir(parents=True, exist_ok=True)
        self._embedding_function = embedding_function or SentenceTransformerEmbedding()
        self._client = chromadb.PersistentClient(path=str(persist_directory))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def index(self, chunks: Sequence[DocumentChunk]) -> int:
        """Replace indexed chunks for supplied sources and return the chunk count."""

        if not chunks:
            return 0

        for source_id in sorted({chunk.source_id for chunk in chunks}):
            self._collection.delete(where={"source_id": source_id})

        embeddings = self._embed([chunk.text for chunk in chunks])
        self._collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[chunk.metadata() for chunk in chunks],
        )
        return len(chunks)

    def search(self, query: str, *, top_k: int = TOP_K) -> list[SearchResult]:
        """Return the nearest chunks ordered by Chroma distance."""

        if not query.strip():
            raise ValueError("query must not be empty.")
        if top_k <= 0:
            raise ValueError("top_k must be positive.")

        result_count = min(top_k, self.count())
        if result_count == 0:
            return []

        response = self._collection.query(
            query_embeddings=self._embed([query]),
            n_results=result_count,
            include=["documents", "metadatas", "distances"],
        )

        ids = response["ids"][0]
        documents = response["documents"][0] if response["documents"] else []
        metadatas = response["metadatas"][0] if response["metadatas"] else []
        distances = response["distances"][0] if response["distances"] else []

        return [
            SearchResult(
                chunk_id=chunk_id,
                text=documents[index],
                metadata=dict(metadatas[index]),
                distance=float(distances[index]),
            )
            for index, chunk_id in enumerate(ids)
        ]

    def count(self) -> int:
        return self._collection.count()

    def _embed(self, texts: Sequence[str]) -> list[list[float]]:
        embeddings = [list(vector) for vector in self._embedding_function(texts)]
        if len(embeddings) != len(texts):
            raise ValueError("Embedding function returned an unexpected number of vectors.")
        return embeddings


def index_bundled_corpus(
    retriever: PersistentRetriever,
    *,
    corpus_dir: Path = DEFAULT_CORPUS_DIR,
) -> int:
    """Load, chunk, and index the bundled Markdown corpus."""

    documents = load_bundled_documents(corpus_dir)
    return retriever.index(chunk_documents(documents))
