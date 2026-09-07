from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class SourceHit(BaseModel):
    source: str
    score: float
    text: str
    metadata: dict = Field(default_factory=dict)


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceHit]


class IngestResult(BaseModel):
    source: str
    documents: int
    chunks: int


class IngestResponse(BaseModel):
    ingested: list[IngestResult]


class DocumentSource(BaseModel):
    source: str
    chunks: int


class StatsResponse(BaseModel):
    chunks: int
    supported_types: list[str]
    sources: list[DocumentSource] = Field(default_factory=list)


class DeleteResponse(BaseModel):
    source: str
    deleted_chunks: int


class HealthResponse(BaseModel):
    status: str
    ollama: str
    llm_model: str
    embed_model: str
    indexed_chunks: int
    ollama_models: list[str] = Field(default_factory=list)
