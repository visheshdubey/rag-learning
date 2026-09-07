from typing import Protocol

from app.domain.models import Chunk, RetrievedChunk


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Turn texts into dense vectors."""


class LLM(Protocol):
    def generate(self, prompt: str, system: str | None = None) -> str:
        """Generate a completion from a prompt."""


class VectorStore(Protocol):
    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None: ...

    def search(
        self, embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]: ...

    def delete_by_source(self, source: str) -> int: ...

    def count(self) -> int: ...

    def list_sources(self) -> list[dict[str, str | int]]: ...
