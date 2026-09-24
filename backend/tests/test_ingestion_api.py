from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ingestion import MAX_UPLOAD_BYTES
from app.main import create_app
from app.retrieval import PersistentRetriever


def deterministic_embedding(texts: Sequence[str]) -> list[list[float]]:
    return [
        [
            1.0 + len(text) % 17,
            1.0 + text.lower().count("dashboard"),
            1.0 + text.lower().count("alert"),
        ]
        for text in texts
    ]


@pytest.fixture
def api(tmp_path: Path) -> Iterator[tuple[TestClient, PersistentRetriever, Path]]:
    chroma_path = tmp_path / "chroma"
    retriever = PersistentRetriever(
        persist_directory=chroma_path,
        embedding_function=deterministic_embedding,
        collection_name="test_upload_api",
    )
    with TestClient(create_app(retriever)) as client:
        yield client, retriever, tmp_path


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("guide.md", b"# Guide\n\nDashboard guidance."),
        ("notes.txt", b"Plain-text alert notes."),
    ],
)
def test_supported_uploads_are_indexed(
    api: tuple[TestClient, PersistentRetriever, Path],
    filename: str,
    content: bytes,
) -> None:
    client, retriever, _ = api

    response = client.post(
        "/api/documents/upload",
        files={"file": (filename, content, "text/plain")},
    )

    assert response.status_code == 201
    assert response.json() == {
        "filename": filename,
        "source_id": f"uploads/{filename}",
        "chunks_indexed": 1,
    }
    assert retriever.count() == 1


def test_upload_sanitizes_filename_before_indexing(
    api: tuple[TestClient, PersistentRetriever, Path],
) -> None:
    client, _, _ = api

    response = client.post(
        "/api/documents/upload",
        files={"file": ("../../Quarterly Report?.MD", b"# Report", "text/markdown")},
    )

    assert response.status_code == 201
    assert response.json()["filename"] == "Quarterly_Report.md"
    assert response.json()["source_id"] == "uploads/Quarterly_Report.md"


def test_unsupported_file_type_is_rejected(
    api: tuple[TestClient, PersistentRetriever, Path],
) -> None:
    client, retriever, _ = api

    response = client.post(
        "/api/documents/upload",
        files={"file": ("report.pdf", b"not a PDF", "application/pdf")},
    )

    assert response.status_code == 415
    assert retriever.count() == 0


def test_oversized_upload_is_rejected(
    api: tuple[TestClient, PersistentRetriever, Path],
) -> None:
    client, retriever, _ = api

    response = client.post(
        "/api/documents/upload",
        files={"file": ("large.md", b"x" * (MAX_UPLOAD_BYTES + 1), "text/markdown")},
    )

    assert response.status_code == 413
    assert retriever.count() == 0


@pytest.mark.parametrize("content", [b"", b"\xff"])
def test_empty_or_invalid_utf8_upload_is_rejected(
    api: tuple[TestClient, PersistentRetriever, Path],
    content: bytes,
) -> None:
    client, retriever, _ = api

    response = client.post(
        "/api/documents/upload",
        files={"file": ("invalid.md", content, "text/markdown")},
    )

    assert response.status_code == 422
    assert retriever.count() == 0


def test_same_sanitized_filename_replaces_previous_chunks(
    api: tuple[TestClient, PersistentRetriever, Path],
) -> None:
    client, retriever, _ = api
    long_content = ("First version with dashboard details. " * 80).encode()

    first_response = client.post(
        "/api/documents/upload",
        files={"file": ("status report.md", long_content, "text/markdown")},
    )
    second_response = client.post(
        "/api/documents/upload",
        files={"file": ("status?report.md", b"Short replacement.", "text/markdown")},
    )

    assert first_response.status_code == 201
    assert first_response.json()["chunks_indexed"] > 1
    assert second_response.status_code == 201
    assert second_response.json()["source_id"] == "uploads/status_report.md"
    assert second_response.json()["chunks_indexed"] == 1
    assert retriever.count() == 1


def test_bundled_corpus_endpoint_indexes_current_corpus(
    api: tuple[TestClient, PersistentRetriever, Path],
) -> None:
    client, retriever, _ = api

    response = client.post("/api/corpus/index")

    assert response.status_code == 200
    assert response.json() == {"chunks_indexed": 45}
    assert retriever.count() == 45


def test_uploaded_raw_file_is_not_retained(
    api: tuple[TestClient, PersistentRetriever, Path],
) -> None:
    client, _, temp_root = api

    response = client.post(
        "/api/documents/upload",
        files={"file": ("private.md", b"Temporary source content.", "text/markdown")},
    )

    assert response.status_code == 201
    assert list(temp_root.rglob("*.md")) == []
    assert list(temp_root.rglob("*.txt")) == []
