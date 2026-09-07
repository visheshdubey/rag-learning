from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    """Raw extracted text from a source file (page, slide, or whole file)."""

    text: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
