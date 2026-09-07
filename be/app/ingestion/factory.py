from pathlib import Path

from app.core.exceptions import LoaderError, UnsupportedFileTypeError
from app.domain.models import Document
from app.ingestion.interfaces import DocumentLoader
from app.ingestion.loaders import (
    CsvLoader,
    DocxLoader,
    HtmlLoader,
    JsonLoader,
    PdfLoader,
    PptxLoader,
    TextLoader,
)


class LoaderFactory:
    """Registry factory: pick a loader from the file extension.

    Adding a type is: implement DocumentLoader, then register it here.
    Clients only depend on DocumentLoader, not on concrete classes.
    """

    _registry: dict[str, type[DocumentLoader]] = {
        ".txt": TextLoader,
        ".md": TextLoader,
        ".markdown": TextLoader,
        ".pdf": PdfLoader,
        ".docx": DocxLoader,
        ".pptx": PptxLoader,
        ".html": HtmlLoader,
        ".htm": HtmlLoader,
        ".csv": CsvLoader,
        ".json": JsonLoader,
    }

    @classmethod
    def supported_extensions(cls) -> list[str]:
        return sorted(cls._registry)

    @classmethod
    def register(cls, extension: str, loader: type[DocumentLoader]) -> None:
        cls._registry[extension.lower()] = loader

    @classmethod
    def create(cls, path: Path) -> DocumentLoader:
        extension = path.suffix.lower()
        loader_cls = cls._registry.get(extension)
        if loader_cls is None:
            raise UnsupportedFileTypeError(extension, cls.supported_extensions())
        return loader_cls()

    @classmethod
    def load(cls, path: Path) -> list[Document]:
        if not path.exists():
            raise LoaderError(f"File not found: {path}")
        return cls.create(path).load(path)
