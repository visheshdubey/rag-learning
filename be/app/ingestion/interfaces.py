from pathlib import Path
from typing import Protocol

from app.domain.models import Document


class DocumentLoader(Protocol):
    def load(self, path: Path) -> list[Document]:
        """Extract text documents from a file."""
