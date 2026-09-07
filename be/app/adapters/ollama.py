from ollama import Client, ResponseError

from app.core.exceptions import OllamaError
import re

_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


class OllamaEmbedder:
    """Adapter: Ollama HTTP client -> Embedder protocol."""

    def __init__(self, client: Client, model: str):
        self._client = client
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self._client.embed(model=self._model, input=texts)
        except ResponseError as exc:
            raise OllamaError(
                f"Embedding failed with model '{self._model}': {exc}. "
                f"Pull it with: ollama pull {self._model}"
            ) from exc
        except Exception as exc:
            raise OllamaError(f"Cannot reach Ollama for embeddings: {exc}") from exc

        embeddings = getattr(response, "embeddings", None) or response.get("embeddings")
        if not embeddings:
            raise OllamaError("Ollama returned no embeddings")
        return [list(vector) for vector in embeddings]


class OllamaLLM:
    """Adapter: Ollama HTTP client -> LLM protocol."""

    def __init__(self, client: Client, model: str):
        self._client = client
        self._model = model

    def generate(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            response = self._client.chat(
                model=self._model,
                messages=messages,
                think=False,
                options={"temperature": 0.1},
            )
        except ResponseError as exc:
            raise OllamaError(
                f"Chat failed with model '{self._model}': {exc}. "
                f"Pull it with: ollama pull {self._model}"
            ) from exc
        except Exception as exc:
            raise OllamaError(f"Cannot reach Ollama for chat: {exc}") from exc

        message = getattr(response, "message", None) or response.get("message") or {}
        content = getattr(message, "content", None) or message.get("content") or ""
        content = _visible_answer(content)
        if not content:
            raise OllamaError("Ollama returned an empty completion")
        return content


def _visible_answer(text: str) -> str:
    cleaned = _THINK_BLOCK.sub("", text)
    if "</think>" in cleaned.lower():
        cleaned = re.split(r"</think>", cleaned, flags=re.IGNORECASE)[-1]
    return cleaned.strip()
