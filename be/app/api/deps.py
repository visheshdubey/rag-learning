from dataclasses import dataclass

from ollama import Client

from app.adapters.chroma import ChromaVectorStore
from app.adapters.ollama import OllamaEmbedder, OllamaLLM
from app.core.config import Settings, get_settings
from app.ingestion.chunking import DocumentChunker, RecursiveChunker
from app.ingestion.factory import LoaderFactory
from app.rag.pipeline import RagPipeline

_container: "AppContainer | None" = None


@dataclass
class AppContainer:
    settings: Settings
    pipeline: RagPipeline
    ollama: Client


def build_container(settings: Settings | None = None) -> AppContainer:
    settings = settings or get_settings()
    settings.ensure_dirs()

    ollama = Client(host=settings.ollama_host)
    pipeline = RagPipeline(
        loaders=LoaderFactory(),
        chunker=DocumentChunker(
            RecursiveChunker(
                chunk_size=settings.chunk_size,
                overlap=settings.chunk_overlap,
            )
        ),
        embedder=OllamaEmbedder(ollama, settings.ollama_embed_model),
        store=ChromaVectorStore(
            persist_path=str(settings.chroma_path),
            collection_name=settings.collection_name,
        ),
        llm=OllamaLLM(ollama, settings.ollama_llm_model),
    )
    return AppContainer(settings=settings, pipeline=pipeline, ollama=ollama)


def set_container(container: AppContainer) -> None:
    global _container
    _container = container


def get_container() -> AppContainer:
    if _container is None:
        raise RuntimeError("application container is not initialized")
    return _container
