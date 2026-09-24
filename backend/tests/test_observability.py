import json
import logging
from collections.abc import Iterator
from io import StringIO
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.observability import LOGGER_NAME, JsonFormatter
from app.retrieval import SearchResult


SENSITIVE_QUERY = "sensitive customer question"
SENSITIVE_ANSWER = "sensitive generated answer"
SENSITIVE_CHUNK = "sensitive retrieved document content"
SENSITIVE_UPLOAD = "sensitive uploaded document content"
SENSITIVE_API_KEY = "secret-value-that-must-not-be-logged"


class StubRetriever:
    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results

    def search(self, query: str) -> list[SearchResult]:
        return self.results

    def index(self, chunks: list[Any]) -> int:
        return len(chunks)


class StubGenerator:
    def generate(self, question: str, context: list[SearchResult]) -> str:
        return SENSITIVE_ANSWER


@pytest.fixture
def json_log_output() -> Iterator[StringIO]:
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger(LOGGER_NAME)
    logger.addHandler(handler)
    try:
        yield output
    finally:
        logger.removeHandler(handler)


def test_query_and_request_events_are_correlated_and_safe(
    json_log_output: StringIO,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", SENSITIVE_API_KEY)
    results = [
        SearchResult(
            chunk_id="chunk-1",
            text=SENSITIVE_CHUNK,
            metadata={
                "source_id": "specifications/limits.md",
                "filename": "limits.md",
                "category": "specification",
                "origin": "bundled",
                "chunk_index": 0,
            },
            distance=0.125,
        ),
        SearchResult(
            chunk_id="chunk-2",
            text="Second retrieved chunk.",
            metadata={
                "source_id": "faqs/limits.md",
                "filename": "limits.md",
                "category": "faq",
                "origin": "bundled",
                "chunk_index": 0,
            },
            distance=0.25,
        ),
    ]

    with TestClient(create_app(StubRetriever(results), StubGenerator())) as client:
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("private.md", SENSITIVE_UPLOAD, "text/markdown")},
        )
        response = client.post("/api/query", json={"question": SENSITIVE_QUERY})

    assert upload_response.status_code == 201
    assert response.status_code == 200
    events = [json.loads(line) for line in json_log_output.getvalue().splitlines()]
    query_event = next(event for event in events if event["event"] == "query_completed")
    request_event = next(
        event
        for event in events
        if event["event"] == "request_completed" and event["path"] == "/api/query"
    )
    request_id = response.headers["X-Request-ID"]

    assert request_event == {
        "timestamp": request_event["timestamp"],
        "level": "INFO",
        "event": "request_completed",
        "request_id": request_id,
        "method": "POST",
        "path": "/api/query",
        "status_code": 200,
        "duration_ms": request_event["duration_ms"],
    }
    assert request_event["timestamp"].endswith("Z")
    assert request_event["duration_ms"] >= 0
    assert query_event == {
        "timestamp": query_event["timestamp"],
        "level": "INFO",
        "event": "query_completed",
        "request_id": request_id,
        "outcome": "generated",
        "retrieved_count": 2,
        "retrieved": [
            {
                "source_id": "specifications/limits.md",
                "chunk_id": "chunk-1",
                "distance": 0.125,
            },
            {
                "source_id": "faqs/limits.md",
                "chunk_id": "chunk-2",
                "distance": 0.25,
            },
        ],
    }

    logged = json_log_output.getvalue()
    for sensitive_value in (
        SENSITIVE_QUERY,
        SENSITIVE_ANSWER,
        SENSITIVE_CHUNK,
        SENSITIVE_UPLOAD,
        SENSITIVE_API_KEY,
    ):
        assert sensitive_value not in logged


def test_abstention_logs_empty_retrieval(json_log_output: StringIO) -> None:
    with TestClient(create_app(StubRetriever([]), StubGenerator())) as client:
        response = client.post("/api/query", json={"question": "Unknown topic"})

    events = [json.loads(line) for line in json_log_output.getvalue().splitlines()]
    query_event = next(event for event in events if event["event"] == "query_completed")

    assert response.status_code == 200
    assert query_event["request_id"] == response.headers["X-Request-ID"]
    assert query_event["outcome"] == "insufficient_context"
    assert query_event["retrieved_count"] == 0
    assert query_event["retrieved"] == []
