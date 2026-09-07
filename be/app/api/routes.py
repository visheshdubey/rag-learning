from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from ollama import Client

from app.api.deps import AppContainer, get_container
from app.api.schemas import (
    DeleteResponse,
    HealthResponse,
    IngestResponse,
    IngestResult,
    QueryRequest,
    QueryResponse,
    StatsResponse,
)
from app.core.config import Settings
from app.core.exceptions import (
    EmptyDocumentError,
    LoaderError,
    OllamaError,
    RagError,
    UnsupportedFileTypeError,
)
from app.ingestion.factory import LoaderFactory
from app.rag.pipeline import RagPipeline


def get_pipeline(container: AppContainer = Depends(get_container)) -> RagPipeline:
    return container.pipeline


def get_settings_dep(container: AppContainer = Depends(get_container)) -> Settings:
    return container.settings


def get_ollama(container: AppContainer = Depends(get_container)) -> Client:
    return container.ollama


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(
    settings: Settings = Depends(get_settings_dep),
    pipeline: RagPipeline = Depends(get_pipeline),
    ollama: Client = Depends(get_ollama),
) -> HealthResponse:
    models: list[str] = []
    ollama_status = "ok"
    try:
        listing = ollama.list()
        raw_models = getattr(listing, "models", None) or listing.get("models") or []
        for item in raw_models:
            name = getattr(item, "model", None) or getattr(item, "name", None)
            if name is None and isinstance(item, dict):
                name = item.get("model") or item.get("name")
            if name:
                models.append(str(name))
    except Exception as exc:
        ollama_status = f"unreachable: {exc}"

    return HealthResponse(
        status="ok" if ollama_status == "ok" else "degraded",
        ollama=ollama_status,
        llm_model=settings.ollama_llm_model,
        embed_model=settings.ollama_embed_model,
        indexed_chunks=pipeline.stats()["chunks"],
        ollama_models=models,
    )


@router.get("/documents", response_model=StatsResponse)
def document_stats(pipeline: RagPipeline = Depends(get_pipeline)) -> StatsResponse:
    stats = pipeline.stats()
    return StatsResponse(
        chunks=stats["chunks"],
        supported_types=LoaderFactory.supported_extensions(),
        sources=stats["sources"],
    )


@router.post(
    "/documents",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_documents(
    files: list[UploadFile] = File(...),
    pipeline: RagPipeline = Depends(get_pipeline),
    settings: Settings = Depends(get_settings_dep),
) -> IngestResponse:
    if not files:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Upload at least one file")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    ingested: list[IngestResult] = []

    for upload in files:
        filename = Path(upload.filename or "upload").name
        suffix = Path(filename).suffix.lower()
        if suffix not in LoaderFactory.supported_extensions():
            raise HTTPException(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                str(
                    UnsupportedFileTypeError(
                        suffix, LoaderFactory.supported_extensions()
                    )
                ),
            )

        payload = await upload.read()
        if len(payload) > max_bytes:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                f"{filename} exceeds {settings.max_upload_mb} MB",
            )

        destination = settings.upload_dir / filename
        destination.write_bytes(payload)
        try:
            result = pipeline.ingest(destination)
        except (LoaderError, EmptyDocumentError, OllamaError, RagError) as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
        ingested.append(IngestResult(**result))

    return IngestResponse(ingested=ingested)


@router.delete("/documents/{source}", response_model=DeleteResponse)
def delete_document(
    source: str,
    pipeline: RagPipeline = Depends(get_pipeline),
) -> DeleteResponse:
    deleted = pipeline.delete_source(source)
    if deleted == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No chunks for '{source}'")
    return DeleteResponse(source=source, deleted_chunks=deleted)


@router.post("/query", response_model=QueryResponse)
def query(
    body: QueryRequest,
    pipeline: RagPipeline = Depends(get_pipeline),
    settings: Settings = Depends(get_settings_dep),
) -> QueryResponse:
    top_k = body.top_k or settings.default_top_k
    try:
        result = pipeline.query(body.question, top_k)
    except (OllamaError, RagError, ValueError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return QueryResponse(**result)
