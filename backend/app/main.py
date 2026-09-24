"""FastAPI entry point for DocLens ingestion and question-answering endpoints."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from logging import Logger
from time import perf_counter
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field, field_validator

from app.generation import (
    INSUFFICIENT_CONTEXT_ANSWER,
    AnswerConfigurationError,
    AnswerGenerationError,
    OpenAIAnswerGenerator,
)
from app.ingestion import (
    MAX_UPLOAD_BYTES,
    DocumentTooLargeError,
    DocumentValidationError,
    UnsupportedFileTypeError,
    chunk_document,
    document_from_upload,
)
from app.observability import configure_logging
from app.retrieval import PersistentRetriever, SearchResult, index_bundled_corpus


MAX_QUERY_CHARACTERS = 2_000


class UploadIndexResponse(BaseModel):
    filename: str
    source_id: str
    chunks_indexed: int


class CorpusIndexResponse(BaseModel):
    chunks_indexed: int


class QueryRequest(BaseModel):
    question: str = Field(max_length=MAX_QUERY_CHARACTERS)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Question must not be empty.")
        return normalized


class AnswerSource(BaseModel):
    source_id: str
    filename: str
    display_filename: str
    category: str
    origin: str
    chunk_index: int
    chunk_id: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[AnswerSource]


def create_app(
    retriever: PersistentRetriever | None = None,
    answer_generator: OpenAIAnswerGenerator | None = None,
) -> FastAPI:
    """Create the API, optionally using supplied retrieval and generation components."""

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.retriever = retriever or PersistentRetriever()
        application.state.answer_generator = answer_generator
        yield

    application = FastAPI(title="DocLens", lifespan=lifespan)
    logger = configure_logging()

    @application.middleware("http")
    async def log_request(request: Request, call_next):
        request_id = uuid4().hex
        request.state.request_id = request_id
        started_at = perf_counter()
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round((perf_counter() - started_at) * 1_000, 3),
                },
            )

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

    @application.post(
        "/api/query",
        response_model=QueryResponse,
    )
    def query_documents(payload: QueryRequest, request: Request) -> QueryResponse:
        results = request.app.state.retriever.search(payload.question)
        sources = [_answer_source(result) for result in results]
        if not results:
            _log_query(logger, request, results, outcome="insufficient_context")
            return QueryResponse(
                answer=INSUFFICIENT_CONTEXT_ANSWER,
                sources=[],
            )

        try:
            generator = request.app.state.answer_generator
            if generator is None:
                generator = OpenAIAnswerGenerator.from_environment()
                request.app.state.answer_generator = generator
            answer = generator.generate(payload.question, results)
        except AnswerConfigurationError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Answer generation is not configured.",
            ) from error
        except AnswerGenerationError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Answer generation is temporarily unavailable.",
            ) from error

        _log_query(logger, request, results, outcome="generated")
        return QueryResponse(answer=answer, sources=sources)

    return application


def _answer_source(result: SearchResult) -> AnswerSource:
    return AnswerSource(
        source_id=result.metadata["source_id"],
        filename=result.metadata["filename"],
        display_filename=result.metadata.get(
            "display_filename", result.metadata["filename"]
        ),
        category=result.metadata["category"],
        origin=result.metadata["origin"],
        chunk_index=result.metadata["chunk_index"],
        chunk_id=result.chunk_id,
    )


def _log_query(
    logger: Logger,
    request: Request,
    results: list[SearchResult],
    *,
    outcome: Literal["generated", "insufficient_context"],
) -> None:
    logger.info(
        "query_completed",
        extra={
            "request_id": request.state.request_id,
            "outcome": outcome,
            "retrieved_count": len(results),
            "retrieved": [
                {
                    "source_id": result.metadata["source_id"],
                    "chunk_id": result.chunk_id,
                    "distance": result.distance,
                }
                for result in results
            ],
        },
    )


app = create_app()
