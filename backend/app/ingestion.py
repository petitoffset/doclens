"""Document loading and deterministic chunking for DocLens."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Iterable
import unicodedata


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS_DIR = PROJECT_ROOT / "corpus"

# Initial retrieval baseline. Keep these in one place so evaluation can tune them.
CHUNK_SIZE = 1_000
CHUNK_OVERLAP = 150
MAX_UPLOAD_BYTES = 1_048_576
SUPPORTED_UPLOAD_EXTENSIONS = {".md", ".txt"}

CATEGORY_BY_DIRECTORY = {
    "faqs": "faq",
    "specifications": "specification",
    "support-tickets": "support-ticket",
}


class DocumentValidationError(ValueError):
    """Base error for documents that cannot enter the ingestion pipeline."""


class InvalidFilenameError(DocumentValidationError):
    pass


class UnsupportedFileTypeError(DocumentValidationError):
    pass


class DocumentTooLargeError(DocumentValidationError):
    pass


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """Normalized text plus the metadata needed throughout ingestion."""

    source_id: str
    filename: str
    display_filename: str
    category: str
    origin: str
    text: str


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    """A deterministic document fragment ready for embedding and indexing."""

    chunk_id: str
    text: str
    source_id: str
    filename: str
    display_filename: str
    category: str
    origin: str
    chunk_index: int

    def metadata(self) -> dict[str, str | int]:
        return {
            "source_id": self.source_id,
            "filename": self.filename,
            "display_filename": self.display_filename,
            "category": self.category,
            "origin": self.origin,
            "chunk_index": self.chunk_index,
        }


def document_from_bytes(
    *,
    content: bytes,
    source_id: str,
    filename: str,
    display_filename: str | None = None,
    category: str,
    origin: str,
) -> SourceDocument:
    """Decode document bytes and create the shared ingestion representation.

    Callers are responsible for source-specific checks such as upload size,
    extension validation, and filename sanitization before calling this function.
    """

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise DocumentValidationError("Document content must be valid UTF-8.") from error

    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized_text:
        raise DocumentValidationError("Document content must not be empty.")

    return SourceDocument(
        source_id=source_id,
        filename=filename,
        display_filename=filename if display_filename is None else display_filename,
        category=category,
        origin=origin,
        text=normalized_text,
    )


def sanitize_filename(filename: str) -> str:
    """Return a metadata-safe basename with a normalized supported extension."""

    basename = filename.replace("\\", "/").rsplit("/", 1)[-1]
    normalized = unicodedata.normalize("NFKC", basename).strip()
    if not normalized:
        raise InvalidFilenameError("Filename must not be empty.")

    original_suffix = Path(normalized).suffix
    suffix = original_suffix.lower()
    if suffix not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise UnsupportedFileTypeError("Only .md and .txt files are supported.")

    stem = normalized[: -len(original_suffix)]
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_-.")
    if not safe_stem:
        raise InvalidFilenameError("Filename must contain a safe name before its extension.")
    return f"{safe_stem}{suffix}"


def sanitize_display_filename(filename: str) -> str:
    """Return a safe basename while retaining useful human-facing formatting."""

    normalized = unicodedata.normalize("NFKC", filename).replace("\\", "/")
    basename = normalized.rsplit("/", 1)[-1]
    return "".join(
        character
        for character in basename
        if not unicodedata.category(character).startswith("C")
    ).strip()


def document_from_upload(
    *,
    content: bytes,
    filename: str,
    max_upload_bytes: int = MAX_UPLOAD_BYTES,
) -> SourceDocument:
    """Validate upload-specific constraints, then enter the shared pipeline.

    The sanitized filename is the MVP source identity. Uploading that filename
    again intentionally replaces its previously indexed chunks.
    """

    if len(content) > max_upload_bytes:
        raise DocumentTooLargeError(
            f"Document exceeds the {max_upload_bytes}-byte upload limit."
        )

    sanitized_filename = sanitize_filename(filename)
    display_filename = sanitize_display_filename(filename) or sanitized_filename
    return document_from_bytes(
        content=content,
        source_id=f"uploads/{sanitized_filename}",
        filename=sanitized_filename,
        display_filename=display_filename,
        category="uploaded",
        origin="upload",
    )


def load_bundled_documents(corpus_dir: Path = DEFAULT_CORPUS_DIR) -> list[SourceDocument]:
    """Load bundled Markdown sources in stable path order."""

    documents: list[SourceDocument] = []
    for path in sorted(corpus_dir.rglob("*.md")):
        relative_path = path.relative_to(corpus_dir)
        category = CATEGORY_BY_DIRECTORY.get(relative_path.parts[0], "other")
        documents.append(
            document_from_bytes(
                content=path.read_bytes(),
                source_id=relative_path.as_posix(),
                filename=path.name,
                category=category,
                origin="bundled",
            )
        )
    return documents


def chunk_document(
    document: SourceDocument,
    *,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    """Split a document into stable, paragraph-aware character windows."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size.")

    text_chunks = _split_text(document.text, chunk_size, chunk_overlap)
    chunks: list[DocumentChunk] = []
    for chunk_index, text in enumerate(text_chunks):
        chunk_id = _chunk_id(document.source_id, chunk_index, text)
        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                text=text,
                source_id=document.source_id,
                filename=document.filename,
                display_filename=document.display_filename,
                category=document.category,
                origin=document.origin,
                chunk_index=chunk_index,
            )
        )
    return chunks


def chunk_documents(
    documents: Iterable[SourceDocument],
    *,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    """Chunk documents in their supplied order."""

    return [
        chunk
        for document in documents
        for chunk in chunk_document(
            document,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    ]


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0

    while start < len(text):
        hard_end = min(start + chunk_size, len(text))
        end = _preferred_break(text, start, hard_end, chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if hard_end == len(text):
            break

        next_start = max(start + 1, end - chunk_overlap)
        start = _align_to_word_boundary(text, next_start, end)

    return chunks


def _preferred_break(text: str, start: int, hard_end: int, chunk_size: int) -> int:
    if hard_end == len(text):
        return hard_end

    minimum_break = start + chunk_size // 2
    for separator in ("\n\n", "\n", " "):
        break_at = text.rfind(separator, minimum_break, hard_end)
        if break_at != -1:
            return break_at + len(separator)
    return hard_end


def _align_to_word_boundary(text: str, start: int, previous_end: int) -> int:
    while start < previous_end and start > 0 and not text[start - 1].isspace():
        start += 1
    while start < previous_end and text[start].isspace():
        start += 1
    return start


def _chunk_id(source_id: str, chunk_index: int, text: str) -> str:
    payload = f"{source_id}\0{chunk_index}\0{text}".encode("utf-8")
    return sha256(payload).hexdigest()
