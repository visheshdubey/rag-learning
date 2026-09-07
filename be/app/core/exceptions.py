class RagError(Exception):
    """Base error for the RAG system."""


class UnsupportedFileTypeError(RagError):
    def __init__(self, extension: str, supported: list[str]):
        self.extension = extension
        self.supported = supported
        super().__init__(
            f"Unsupported file type '{extension}'. "
            f"Supported: {', '.join(supported)}"
        )


class LoaderError(RagError):
    pass


class OllamaError(RagError):
    pass


class EmptyDocumentError(RagError):
    pass
