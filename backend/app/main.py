"""FastAPI entry point for DocLens ingestion endpoints."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel

from app.ingestion import (
    MAX_UPLOAD_BYTES,
    DocumentTooLargeError,
    DocumentValidationError,
    UnsupportedFileTypeError,
    chunk_document,
    document_from_upload,
)
from app.retrieval import PersistentRetriever, index_bundled_corpus


class UploadIndexResponse(BaseModel):
    filename: str
    source_id: str
    chunks_indexed: int


class CorpusIndexResponse(BaseModel):
    chunks_indexed: int


def create_app(retriever: PersistentRetriever | None = None) -> FastAPI:
    """Create the API, optionally using a supplied retriever for tests."""

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.retriever = retriever or PersistentRetriever()
        yield

    application = FastAPI(title="DocLens", lifespan=lifespan)

    @application.post(
        "/api/documents/upload",
        response_model=UploadIndexResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def upload_document(
        request: Request,
        file: Annotated[UploadFile, File(...)],
    ) -> UploadIndexResponse:
        filename = file.filename or ""
        try:
            content = await file.read(MAX_UPLOAD_BYTES + 1)
        finally:
            await file.close()

        try:
            document = document_from_upload(
                content=content,
                filename=filename,
            )
        except UnsupportedFileTypeError as error:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=str(error),
            ) from error
        except DocumentTooLargeError as error:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=str(error),
            ) from error
        except DocumentValidationError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(error),
            ) from error

        chunks = chunk_document(document)
        indexed_count = request.app.state.retriever.index(chunks)
        return UploadIndexResponse(
            filename=document.filename,
            source_id=document.source_id,
            chunks_indexed=indexed_count,
        )

    @application.post(
        "/api/corpus/index",
        response_model=CorpusIndexResponse,
    )
    def index_corpus(request: Request) -> CorpusIndexResponse:
        indexed_count = index_bundled_corpus(request.app.state.retriever)
        return CorpusIndexResponse(chunks_indexed=indexed_count)

    return application


app = create_app()
