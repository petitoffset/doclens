import json
from collections.abc import Iterator, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from openai import OpenAIError

from app.generation import (
    GROUNDING_INSTRUCTIONS,
    INSUFFICIENT_CONTEXT_ANSWER,
    MAX_OUTPUT_TOKENS,
    OpenAIAnswerGenerator,
)
from app.ingestion import chunk_documents, document_from_bytes
from app.main import MAX_QUERY_CHARACTERS, create_app
from app.retrieval import TOP_K, PersistentRetriever, SearchResult


class FakeResponses:
    """Records the only mocked boundary: OpenAI Responses API calls."""

    def __init__(self, *, output_text: str = "Use exponential backoff.") -> None:
        self.output_text = output_text
        self.calls: list[dict[str, Any]] = []
        self.error: OpenAIError | None = None

    def create(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(output_text=self.output_text)


def deterministic_embedding(texts: Sequence[str]) -> list[list[float]]:
    vectors = []
    for text in texts:
        lowered = text.lower()
        if "rate" in lowered:
            vectors.append([1.0, 0.0])
        elif "dashboard" in lowered:
            vectors.append([0.9, 0.1])
        elif "alert" in lowered:
            vectors.append([0.5, 0.5])
        else:
            vectors.append([0.0, 1.0])
    return vectors


def indexed_retriever(tmp_path: Path) -> PersistentRetriever:
    retriever = PersistentRetriever(
        persist_directory=tmp_path / "chroma",
        embedding_function=deterministic_embedding,
        collection_name="test_answering_api",
    )
    documents = [
        document_from_bytes(
            content=content.encode(),
            source_id=f"specifications/{filename}",
            filename=filename,
            category="specification",
            origin="bundled",
        )
        for filename, content in [
            ("rate-limits.md", "API rate limits require exponential backoff."),
            ("dashboards.md", "Dashboard data refreshes periodically."),
            ("alerts.md", "Alert notifications can be delayed."),
            ("unrelated.md", "This fourth document must not leave the local index."),
        ]
    ]
    retriever.index(chunk_documents(documents))
    return retriever


@pytest.fixture
def answering_api(
    tmp_path: Path,
) -> Iterator[tuple[TestClient, FakeResponses]]:
    responses = FakeResponses()
    generator = OpenAIAnswerGenerator(
        model="test-model",
        client=SimpleNamespace(responses=responses),
    )
    with TestClient(create_app(indexed_retriever(tmp_path), generator)) as client:
        yield client, responses


def test_query_retrieves_top_three_and_returns_traceable_sources(
    answering_api: tuple[TestClient, FakeResponses],
) -> None:
    client, responses = answering_api

    response = client.post(
        "/api/query",
        json={"question": "  How should API rate limits be handled?  "},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Use exponential backoff."
    assert len(body["sources"]) == 3
    assert body["sources"][0]["source_id"] == "specifications/rate-limits.md"
    assert all(source["chunk_id"] for source in body["sources"])

    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert call["model"] == "test-model"
    assert call["instructions"] == GROUNDING_INSTRUCTIONS
    assert call["max_output_tokens"] == MAX_OUTPUT_TOKENS
    sent = json.loads(call["input"])
    assert sent["question"] == "How should API rate limits be handled?"
    assert len(sent["retrieved_context"]) == TOP_K
    assert all(isinstance(chunk, str) for chunk in sent["retrieved_context"])
    assert all(source["source_id"] not in call["input"] for source in body["sources"])
    assert all(source["chunk_id"] not in call["input"] for source in body["sources"])
    assert "This fourth document must not leave the local index." not in call["input"]


def test_generation_boundary_limits_context_to_retrieval_top_k() -> None:
    responses = FakeResponses()
    generator = OpenAIAnswerGenerator(
        model="test-model",
        client=SimpleNamespace(responses=responses),
    )
    context = [
        SearchResult(
            chunk_id=f"chunk-{index}",
            text=f"Retrieved content {index}",
            metadata={},
            distance=float(index),
        )
        for index in range(TOP_K + 1)
    ]

    generator.generate("What does the context say?", context)

    sent = json.loads(responses.calls[0]["input"])
    assert sent["retrieved_context"] == [
        result.text for result in context[:TOP_K]
    ]
    assert context[TOP_K].text not in responses.calls[0]["input"]


@pytest.mark.parametrize(
    "question",
    ["", "   ", "x" * (MAX_QUERY_CHARACTERS + 1)],
)
def test_invalid_query_is_rejected_before_retrieval_or_generation(
    answering_api: tuple[TestClient, FakeResponses],
    question: str,
) -> None:
    client, responses = answering_api

    response = client.post("/api/query", json={"question": question})

    assert response.status_code == 422
    assert responses.calls == []


def test_empty_index_abstains_without_calling_openai(tmp_path: Path) -> None:
    responses = FakeResponses()
    generator = OpenAIAnswerGenerator(
        model="test-model",
        client=SimpleNamespace(responses=responses),
    )
    retriever = PersistentRetriever(
        persist_directory=tmp_path / "empty-chroma",
        embedding_function=deterministic_embedding,
        collection_name="test_empty_answering_api",
    )

    with TestClient(create_app(retriever, generator)) as client:
        response = client.post("/api/query", json={"question": "What is the limit?"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": INSUFFICIENT_CONTEXT_ANSWER,
        "sources": [],
    }
    assert responses.calls == []


def test_query_does_not_require_api_key_when_generator_is_injected(
    answering_api: tuple[TestClient, FakeResponses],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, responses = answering_api
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post("/api/query", json={"question": "Explain rate limits."})

    assert response.status_code == 200
    assert len(responses.calls) == 1


def test_missing_environment_configuration_returns_service_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    with TestClient(create_app(indexed_retriever(tmp_path))) as client:
        response = client.post("/api/query", json={"question": "Explain rate limits."})

    assert response.status_code == 503
    assert response.json() == {"detail": "Answer generation is not configured."}


def test_openai_failure_returns_bad_gateway(
    answering_api: tuple[TestClient, FakeResponses],
) -> None:
    client, responses = answering_api
    responses.error = OpenAIError("simulated API failure")

    response = client.post("/api/query", json={"question": "Explain rate limits."})

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Answer generation is temporarily unavailable."
    }
