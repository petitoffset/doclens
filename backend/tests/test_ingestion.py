from pathlib import Path

import pytest

from app.ingestion import (
    CHUNK_SIZE,
    chunk_document,
    chunk_documents,
    document_from_bytes,
    load_bundled_documents,
)


def test_loads_only_the_seventeen_bundled_markdown_sources() -> None:
    documents = load_bundled_documents()

    assert len(documents) == 17
    assert [document.source_id for document in documents] == sorted(
        document.source_id for document in documents
    )
    assert all(document.source_id.endswith(".md") for document in documents)
    assert all(document.origin == "bundled" for document in documents)
    assert all(
        document.display_filename == document.filename for document in documents
    )
    assert "fact-ledger.yaml" not in {document.source_id for document in documents}
    assert {document.category for document in documents} == {
        "faq",
        "specification",
        "support-ticket",
    }


def test_document_from_bytes_is_reusable_for_uploaded_content() -> None:
    document = document_from_bytes(
        content=b"\xef\xbb\xbf# Upload\r\n\r\nReusable text.\r\n",
        source_id="upload/example.md",
        filename="example.md",
        category="uploaded",
        origin="upload",
    )

    assert document.text == "# Upload\n\nReusable text."
    assert document.source_id == "upload/example.md"
    assert document.origin == "upload"


@pytest.mark.parametrize("content", [b"", b"  \r\n", b"\xff"])
def test_document_from_bytes_rejects_empty_or_invalid_utf8(content: bytes) -> None:
    with pytest.raises(ValueError):
        document_from_bytes(
            content=content,
            source_id="invalid.txt",
            filename="invalid.txt",
            category="uploaded",
            origin="upload",
        )


def test_chunking_is_deterministic_bounded_and_traceable() -> None:
    document = document_from_bytes(
        content=(
            "# Limits\n\n"
            + "Rate limit details and recovery guidance. " * 50
            + "\n\n# Dashboard\n\n"
            + "Dashboard refresh and cache behavior. " * 50
        ).encode(),
        source_id="specifications/example.md",
        filename="example.md",
        category="specification",
        origin="bundled",
    )

    first = chunk_document(document)
    second = chunk_document(document)

    assert len(first) > 1
    assert first == second
    assert all(0 < len(chunk.text) <= CHUNK_SIZE for chunk in first)
    assert [chunk.chunk_index for chunk in first] == list(range(len(first)))
    assert len({chunk.chunk_id for chunk in first}) == len(first)
    assert all(chunk.metadata()["source_id"] == document.source_id for chunk in first)
    assert all(
        chunk.metadata()["display_filename"] == document.filename for chunk in first
    )


def test_display_filename_does_not_affect_deterministic_chunk_ids() -> None:
    common = {
        "content": b"Stable content",
        "source_id": "uploads/stable.md",
        "filename": "stable.md",
        "category": "uploaded",
        "origin": "upload",
    }

    first = document_from_bytes(**common, display_filename="Stable Draft.md")
    second = document_from_bytes(**common, display_filename="Stable Final.md")

    assert chunk_document(first)[0].chunk_id == chunk_document(second)[0].chunk_id


def test_chunk_documents_preserves_document_order() -> None:
    documents = [
        document_from_bytes(
            content=f"Document {index}".encode(),
            source_id=f"source-{index}.txt",
            filename=f"source-{index}.txt",
            category="uploaded",
            origin="upload",
        )
        for index in range(2)
    ]

    chunks = chunk_documents(documents)

    assert [chunk.source_id for chunk in chunks] == [
        "source-0.txt",
        "source-1.txt",
    ]


def test_custom_chunk_parameters_are_validated() -> None:
    document = document_from_bytes(
        content=b"Valid content",
        source_id="valid.txt",
        filename="valid.txt",
        category="uploaded",
        origin="upload",
    )

    with pytest.raises(ValueError, match="chunk_size"):
        chunk_document(document, chunk_size=0)
    with pytest.raises(ValueError, match="chunk_overlap"):
        chunk_document(document, chunk_size=100, chunk_overlap=100)


def test_custom_corpus_directory_uses_relative_source_ids(tmp_path: Path) -> None:
    faq_dir = tmp_path / "faqs"
    faq_dir.mkdir()
    (faq_dir / "example.md").write_text("# Example\n\nText", encoding="utf-8")
    (tmp_path / "fact-ledger.yaml").write_text("ignored: true", encoding="utf-8")

    documents = load_bundled_documents(tmp_path)

    assert [document.source_id for document in documents] == ["faqs/example.md"]
    assert documents[0].category == "faq"
