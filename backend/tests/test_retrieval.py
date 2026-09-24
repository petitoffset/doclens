from collections.abc import Sequence

import pytest

from app.ingestion import chunk_documents, document_from_bytes, load_bundled_documents
from app.retrieval import PersistentRetriever, index_bundled_corpus


class KeywordEmbedding:
    """Small deterministic embedding used only by retrieval tests."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [self._vector(text) for text in texts]

    @staticmethod
    def _vector(text: str) -> list[float]:
        lowered = text.lower()
        return [
            1.0 + lowered.count("rate"),
            1.0 + lowered.count("dashboard"),
            1.0 + lowered.count("alert"),
        ]


def _example_chunks():
    documents = [
        document_from_bytes(
            content=b"API rate limits and retry guidance.",
            source_id="specifications/rate.md",
            filename="rate.md",
            category="specification",
            origin="bundled",
        ),
        document_from_bytes(
            content=b"Dashboard refresh and cache behavior.",
            source_id="specifications/dashboard.md",
            filename="dashboard.md",
            category="specification",
            origin="bundled",
        ),
        document_from_bytes(
            content=b"Alert evaluation and notification behavior.",
            source_id="specifications/alert.md",
            filename="alert.md",
            category="specification",
            origin="bundled",
        ),
        document_from_bytes(
            content=b"CSV validation and timestamp requirements.",
            source_id="specifications/csv.md",
            filename="csv.md",
            category="specification",
            origin="bundled",
        ),
    ]
    return chunk_documents(documents)


def test_index_persists_and_search_returns_top_three_with_sources(tmp_path) -> None:
    embedding = KeywordEmbedding()
    retriever = PersistentRetriever(
        persist_directory=tmp_path / "chroma",
        embedding_function=embedding,
        collection_name="test_documents",
    )
    chunks = _example_chunks()

    assert retriever.index(chunks) == 4
    assert retriever.count() == 4

    reopened = PersistentRetriever(
        persist_directory=tmp_path / "chroma",
        embedding_function=embedding,
        collection_name="test_documents",
    )
    results = reopened.search("rate limit", top_k=3)

    assert reopened.count() == 4
    assert len(results) == 3
    assert results[0].metadata["source_id"] == "specifications/rate.md"
    assert results[0].metadata["display_filename"] == "rate.md"
    assert all(result.text for result in results)
    assert all(result.chunk_id for result in results)
    assert all("chunk_index" in result.metadata for result in results)
    assert results == sorted(results, key=lambda result: result.distance)


def test_reindexing_the_same_sources_does_not_duplicate_chunks(tmp_path) -> None:
    retriever = PersistentRetriever(
        persist_directory=tmp_path / "chroma",
        embedding_function=KeywordEmbedding(),
        collection_name="test_reindex",
    )
    chunks = _example_chunks()

    retriever.index(chunks)
    retriever.index(chunks)

    assert retriever.count() == len(chunks)


def test_documents_and_queries_use_the_same_embedding_function(tmp_path) -> None:
    embedding = KeywordEmbedding()
    retriever = PersistentRetriever(
        persist_directory=tmp_path / "chroma",
        embedding_function=embedding,
        collection_name="test_embedding_path",
    )

    retriever.index(_example_chunks())
    retriever.search("dashboard")

    assert len(embedding.calls) == 2
    assert embedding.calls[-1] == ["dashboard"]


def test_empty_index_returns_no_results_and_validates_queries(tmp_path) -> None:
    retriever = PersistentRetriever(
        persist_directory=tmp_path / "chroma",
        embedding_function=KeywordEmbedding(),
        collection_name="test_empty",
    )

    assert retriever.search("anything") == []
    with pytest.raises(ValueError, match="query"):
        retriever.search("  ")
    with pytest.raises(ValueError, match="top_k"):
        retriever.search("query", top_k=0)


def test_bundled_corpus_indexes_through_the_shared_pipeline(tmp_path) -> None:
    retriever = PersistentRetriever(
        persist_directory=tmp_path / "chroma",
        embedding_function=KeywordEmbedding(),
        collection_name="test_bundled",
    )
    expected_chunks = chunk_documents(load_bundled_documents())

    indexed_count = index_bundled_corpus(retriever)

    assert indexed_count == len(expected_chunks)
    assert retriever.count() == len(expected_chunks)
