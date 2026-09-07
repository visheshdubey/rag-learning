from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.deps import build_container, set_container
from app.api.routes import router
from app.core.config import get_settings
from app.core.exceptions import RagError


@asynccontextmanager
async def lifespan(_: FastAPI):
    set_container(build_container())
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG Learning API",
        description="Local RAG over Ollama with multi-format document ingest.",
        version="0.1.0",
        lifespan=lifespan,
    )
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.exception_handler(RagError)
    async def rag_error_handler(_: Request, exc: RagError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
