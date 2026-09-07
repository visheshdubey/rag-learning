from typing import Protocol
from uuid import uuid4

from app.domain.models import Chunk, Document


class ChunkingStrategy(Protocol):
    def split(self, text: str) -> list[str]:
        """Split a document's text into overlapping pieces."""


class FixedSizeChunker:
    def __init__(self, chunk_size: int = 800, overlap: int = 150):
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, text: str) -> list[str]:
        cleaned = " ".join(text.split())
        if not cleaned:
            return []
        if len(cleaned) <= self.chunk_size:
            return [cleaned]

        step = self.chunk_size - self.overlap
        return [
            cleaned[start : start + self.chunk_size]
            for start in range(0, len(cleaned), step)
            if cleaned[start : start + self.chunk_size].strip()
        ]


class RecursiveChunker:
    """Prefer natural boundaries, then fall back to a hard size cut."""

    def __init__(
        self,
        chunk_size: int = 800,
        overlap: int = 150,
        separators: tuple[str, ...] = ("\n\n", "\n", ". ", " "),
    ):
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separators = separators
        self._fallback = FixedSizeChunker(chunk_size, overlap)

    def split(self, text: str) -> list[str]:
        cleaned = text.strip()
        if not cleaned:
            return []
        parts = self._split(cleaned, list(self.separators))
        return self._merge(parts)

    def _split(self, text: str, separators: list[str]) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]
        if not separators:
            return self._fallback.split(text)

        separator, *rest = separators
        pieces = [piece for piece in text.split(separator) if piece.strip()]
        parts: list[str] = []
        for piece in pieces:
            if len(piece) > self.chunk_size:
                parts.extend(self._split(piece, rest))
            else:
                parts.append(piece)
        return parts

    def _merge(self, parts: list[str]) -> list[str]:
        chunks: list[str] = []
        current = ""
        for part in parts:
            candidate = part if not current else f"{current} {part}"
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue
            if current:
                chunks.append(current)
            current = part if len(part) <= self.chunk_size else ""
            if len(part) > self.chunk_size:
                chunks.extend(self._fallback.split(part))
        if current:
            chunks.append(current)
        return chunks


class DocumentChunker:
    """Context that delegates splitting to a ChunkingStrategy."""

    def __init__(self, strategy: ChunkingStrategy):
        self._strategy = strategy

    def chunk(self, documents: list[Document]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for document in documents:
            parts = self._strategy.split(document.text)
            for index, part in enumerate(parts):
                chunks.append(
                    Chunk(
                        id=str(uuid4()),
                        text=part,
                        source=document.source,
                        metadata={**document.metadata, "chunk_index": index},
                    )
                )
        return chunks
