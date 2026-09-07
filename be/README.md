# Local RAG with Ollama

A FastAPI service that ingests files, stores embeddings in Chroma, and answers questions with a local Ollama model. The dashboard lives in `../fe`.

## What you need

- Python 3.11+
- [Ollama](https://ollama.com) running locally (`ollama serve` if it is not already a service)

Pull the default models once:

```bash
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

Change models in `.env` if you prefer others (`llama3.1`, `mistral`, `qwen2.5`, …). The embed model and the LLM do not have to match.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

On macOS/Linux use `source .venv/bin/activate` and `cp .env.example .env`.

## Run

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the Swagger UI.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Ollama reachability, models, index size |
| `GET` | `/documents` | Chunk count and supported file types |
| `POST` | `/documents` | Upload one or more files |
| `DELETE` | `/documents/{source}` | Remove a file's chunks by original filename |
| `POST` | `/query` | Ask a question against the index |

Supported types: `.txt` `.md` `.pdf` `.docx` `.pptx` `.html` `.csv` `.json`

```bash
curl -F "files=@samples/company_handbook.md" http://127.0.0.1:8000/documents

curl -X POST http://127.0.0.1:8000/query ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"How many leave days do employees get?\"}"
```

Re-uploading the same filename replaces previous chunks for that source.

## Layout

```
app/
  api/          HTTP layer (thin)
  adapters/     Ollama + Chroma wrappers
  ingestion/    file loaders + chunking
  rag/          ingest and query pipeline
  domain/       Document / Chunk models
  core/         settings and errors
```

Patterns used, and only where they earn their keep:

- **Factory** (`LoaderFactory`) — pick a loader from the file extension. Add a type by writing a loader and registering its suffix.
- **Strategy** (`ChunkingStrategy`) — swap recursive vs fixed-size splitting without touching ingest.
- **Adapter** (`OllamaEmbedder`, `OllamaLLM`, `ChromaVectorStore`) — keep the pipeline on small protocols so Ollama or Chroma can be replaced later.
- **Facade** (`RagPipeline`) — one object for ingest, query, delete, and stats.

## Add a file type

1. Implement `load(self, path: Path) -> list[Document]` in `app/ingestion/loaders.py`.
2. Register the extension in `LoaderFactory._registry`.
3. No other files need to change.

## Config

See `.env.example`. The important knobs are `OLLAMA_LLM_MODEL`, `OLLAMA_EMBED_MODEL`, `CHUNK_SIZE`, and `CHUNK_OVERLAP`.
