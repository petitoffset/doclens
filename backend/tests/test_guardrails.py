import pytest

from app.ingestion import (
    DocumentTooLargeError,
    InvalidFilenameError,
    UnsupportedFileTypeError,
    document_from_upload,
    sanitize_display_filename,
    sanitize_filename,
)


@pytest.mark.parametrize(
    ("original", "expected"),
    [
        ("report.md", "report.md"),
        ("../../Quarterly Report?.MD", "Quarterly_Report.md"),
        (r"..\..\support notes.txt", "support_notes.txt"),
    ],
)
def test_sanitize_filename_removes_paths_and_unsafe_characters(
    original: str,
    expected: str,
) -> None:
    assert sanitize_filename(original) == expected


@pytest.mark.parametrize("filename", ["", "../.md", "notes.pdf", "notes.md.exe"])
def test_sanitize_filename_rejects_invalid_or_unsupported_names(filename: str) -> None:
    with pytest.raises((InvalidFilenameError, UnsupportedFileTypeError)):
        sanitize_filename(filename)


def test_upload_size_is_checked_before_shared_document_creation() -> None:
    with pytest.raises(DocumentTooLargeError):
        document_from_upload(
            content=b"12345",
            filename="example.md",
            max_upload_bytes=4,
        )


def test_sanitized_filename_is_the_explicit_upload_source_identity() -> None:
    document = document_from_upload(
        content=b"# Safe content",
        filename="../../Q3 Customer Success (Final)!.MD",
    )

    assert document.filename == "Q3_Customer_Success_Final.md"
    assert document.display_filename == "Q3 Customer Success (Final)!.MD"
    assert document.source_id == "uploads/Q3_Customer_Success_Final.md"
    assert document.origin == "upload"
    assert document.category == "uploaded"


def test_display_filename_removes_paths_and_control_characters() -> None:
    filename = "../private/Quarterly\x00 Report (Final).MD"

    assert sanitize_display_filename(filename) == "Quarterly Report (Final).MD"
