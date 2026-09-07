from pathlib import Path

from app.adapters.protocols import Embedder, LLM, VectorStore
from app.core.exceptions import EmptyDocumentError
from app.domain.models import RetrievedChunk
from app.ingestion.chunking import DocumentChunker
from app.ingestion.factory import LoaderFactory

SYSTEM_PROMPT = """You are a retrieval QA assistant.
Answer the question using the context.

If the context states the fact, answer it. Different wording still counts:
- "Vishesh's wife is Sweekriti" answers "Who is the wife of Vishesh?"
- Give the name or fact first. Do not start with "I do not know".

Say you do not know only when the context has no related fact.
Cite source file names."""


class RagPipeline:
    """Facade over load -> chunk -> embed -> store -> retrieve -> generate."""

    def __init__(
        self,
        *,
        loaders: LoaderFactory,
        chunker: DocumentChunker,
        embedder: Embedder,
        store: VectorStore,
        llm: LLM,
        embed_batch_size: int = 32,
    ):
        self._loaders = loaders
        self._chunker = chunker
        self._embedder = embedder
        self._store = store
        self._llm = llm
        self._embed_batch_size = embed_batch_size

    def ingest(self, path: Path) -> dict:
        documents = self._loaders.load(path)
        chunks = self._chunker.chunk(documents)
        if not chunks:
            raise EmptyDocumentError(f"Nothing to index from {path.name}")

        embeddings: list[list[float]] = []
        texts = [chunk.text for chunk in chunks]
        for start in range(0, len(texts), self._embed_batch_size):
            batch = texts[start : start + self._embed_batch_size]
            embeddings.extend(self._embedder.embed(batch))

        self._store.delete_by_source(path.name)
        self._store.upsert(chunks, embeddings)
        return {
            "source": path.name,
            "documents": len(documents),
            "chunks": len(chunks),
        }

    def query(self, question: str, top_k: int) -> dict:
        question = question.strip()
        if not question:
            raise ValueError("question must not be empty")

        [query_embedding] = self._embedder.embed([question])
        hits = self._store.search(query_embedding, top_k)
        context = _format_context(hits)
        prompt = (
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Give a direct answer from the context. Do not refuse a fact that is already written there.\n"
            "Answer:"
            if hits
            else (
                "No documents are indexed yet. Tell the user to ingest files first.\n\n"
                f"Question: {question}\n\nAnswer:"
            )
        )
        answer = self._llm.generate(prompt, system=SYSTEM_PROMPT)
        return {
            "answer": answer,
            "sources": [
                {
                    "source": hit.source,
                    "score": round(hit.score, 4),
                    "text": hit.text,
                    "metadata": hit.metadata,
                }
                for hit in hits
            ],
        }

    def delete_source(self, source: str) -> int:
        return self._store.delete_by_source(source)

    def stats(self) -> dict:
        return {
            "chunks": self._store.count(),
            "sources": self._store.list_sources(),
        }


def _format_context(hits: list[RetrievedChunk]) -> str:
    blocks = []
    for index, hit in enumerate(hits, start=1):
        location = hit.metadata.get("page") or hit.metadata.get("slide") or ""
        loc = f" ({location})" if location else ""
        blocks.append(f"[{index}] {hit.source}{loc}\n{hit.text}")
    return "\n\n".join(blocks)
