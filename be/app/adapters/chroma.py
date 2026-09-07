import os

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from chromadb import PersistentClient

from app.domain.models import Chunk, RetrievedChunk


class ChromaVectorStore:
    """Adapter: Chroma persistent collection -> VectorStore protocol."""

    def __init__(self, persist_path: str, collection_name: str):
        self._client = PersistentClient(path=persist_path)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must be the same length")

        self._collection.upsert(
            ids=[chunk.id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {"source": chunk.source, **_stringify(chunk.metadata)}
                for chunk in chunks
            ],
        )

    def search(self, embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        if top_k <= 0 or self.count() == 0:
            return []

        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, self.count()),
            include=["documents", "metadatas", "distances"],
        )
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for text, metadata, distance in zip(documents, metadatas, distances):
            metadata = metadata or {}
            retrieved.append(
                RetrievedChunk(
                    text=text,
                    source=str(metadata.get("source", "")),
                    score=_cosine_from_distance(distance),
                    metadata=dict(metadata),
                )
            )
        return retrieved

    def delete_by_source(self, source: str) -> int:
        existing = self._collection.get(where={"source": source})
        ids = existing.get("ids") or []
        if not ids:
            return 0
        self._collection.delete(ids=ids)
        return len(ids)

    def count(self) -> int:
        return self._collection.count()

    def list_sources(self) -> list[dict[str, str | int]]:
        existing = self._collection.get(include=["metadatas"])
        counts: dict[str, int] = {}
        for metadata in existing.get("metadatas") or []:
            source = str((metadata or {}).get("source") or "unknown")
            counts[source] = counts.get(source, 0) + 1
        return [
            {"source": source, "chunks": chunks}
            for source, chunks in sorted(counts.items())
        ]


def _cosine_from_distance(distance: float) -> float:
    # Chroma cosine space stores 1 - cosine_similarity.
    return max(0.0, min(1.0, 1.0 - float(distance)))


def _stringify(metadata: dict) -> dict[str, str | int | float | bool]:
    clean: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            clean[key] = str(value)
    return clean
