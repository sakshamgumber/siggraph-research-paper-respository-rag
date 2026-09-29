from __future__ import annotations

import os
import time
from typing import Any, Iterable
from pathlib import Path

from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter

# Load environment variables from .env if present
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv()

JINA_API_URL = "https://api.jina.ai/v1/embeddings"
JINA_MODEL_NAME = "jina-embeddings-v5-text-small"
JINA_EMBEDDING_SIZE = 1024

# Legacy Qwen constants for compatibility
QWEN_MODEL_NAME = "Qwen/Qwen3-Embedding-8B"
QWEN_EMBEDDING_SIZE = 4096

_SHARED_SESSION: requests.Session | None = None



def get_shared_session() -> requests.Session:
    """Return a shared requests.Session with connection pooling and TCP keep-alive."""
    global _SHARED_SESSION
    if _SHARED_SESSION is None:
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        _SHARED_SESSION = session
    return _SHARED_SESSION


class JinaEmbedder:
    """Jina v5 Text Small dense embedder via Jina AI Embeddings API with HTTP connection pooling."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = JINA_MODEL_NAME,
        dimensions: int = JINA_EMBEDDING_SIZE,
        *,
        batch_size: int = 16,
        timeout: float = 60.0,
        max_retries: int = 3,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("JINA_API_KEY")
        self.model_name = model_name
        self.dimensions = dimensions
        self.batch_size = batch_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = session or get_shared_session()

    def embed_documents(self, texts: Iterable[str]) -> list[list[float]]:
        """Embed a sequence of document passages using retrieval.passage task."""
        text_list = [text.strip() if text and text.strip() else " " for text in texts]
        if not text_list:
            return []

        embeddings: list[list[float]] = []
        for i in range(0, len(text_list), self.batch_size):
            batch = text_list[i : i + self.batch_size]
            batch_vecs = self._embed_batch(batch, task="retrieval.passage")
            embeddings.extend(batch_vecs)
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a search query using retrieval.query task."""
        clean_text = text.strip() if text and text.strip() else " "
        return self._embed_batch([clean_text], task="retrieval.query")[0]

    def _embed_batch(self, batch: list[str], task: str) -> list[list[float]]:
        if not batch:
            return []

        if not self.api_key:
            raise ValueError(
                "Jina API key not configured. Please set the JINA_API_KEY environment variable "
                "in your .env file or environment, or pass api_key to JinaEmbedder."
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model_name,
            "task": task,
            "dimensions": self.dimensions,
            "normalized": True,
            "input": [{"text": text} for text in batch],
        }

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.post(
                    JINA_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    # Sort data by index to guarantee ordering
                    sorted_items = sorted(data, key=lambda item: item.get("index", 0))
                    return [item["embedding"] for item in sorted_items]

                # Retry on rate limit (429) or temporary server error (5xx)
                if response.status_code == 429 and attempt < self.max_retries:
                    retry_after = int(response.headers.get("Retry-After", 20 * attempt))
                    time.sleep(retry_after)
                    continue

                if response.status_code in (500, 502, 503, 504) and attempt < self.max_retries:
                    time.sleep(2.0 * attempt)
                    continue

                raise RuntimeError(
                    f"Jina API request failed (HTTP {response.status_code}): {response.text}"
                )
            except (requests.RequestException, RuntimeError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(2.0 * attempt)
                else:
                    raise RuntimeError(
                        f"Failed to obtain embeddings from Jina API after {self.max_retries} attempts: {exc}"
                    ) from exc

        if last_error:
            raise last_error
        return []


# Keep QwenHuggingFaceEmbedder for backwards compatibility if needed
class QwenHuggingFaceEmbedder:
    """Qwen3-Embedding-8B dense embedder using Hugging Face Inference API."""

    def __init__(
        self,
        model_name: str = QWEN_MODEL_NAME,
        token: str | None = None,
        provider: str | None = None,
        *,
        batch_size: int = 8,
        query_instruction: str = "Instruct: Given a document query, retrieve the most relevant chunk.\nQuery: ",
    ) -> None:
        from huggingface_hub import InferenceClient
        import numpy as np

        self.np = np
        self.model_name = model_name
        self.token = (
            token
            or os.getenv("HF_TOKEN")
            or os.getenv("HUGGINGFACE_HUB_TOKEN")
        )
        self.provider = provider or os.getenv("HF_PROVIDER", "deepinfra")
        self.batch_size = batch_size
        self.query_instruction = query_instruction
        self.client = InferenceClient(
            provider=self.provider if self.provider != "none" else None,
            token=self.token,
        )

    def embed_documents(self, texts: Iterable[str]) -> list[list[float]]:
        text_list = [text.strip() if text and text.strip() else " " for text in texts]
        if not text_list:
            return []
        embeddings: list[list[float]] = []
        for i in range(0, len(text_list), self.batch_size):
            batch = text_list[i : i + self.batch_size]
            embeddings.extend(self._embed_batch(batch))
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        clean_text = text.strip() if text else ""
        formatted_query = (
            f"{self.query_instruction}{clean_text}"
            if self.query_instruction
            else clean_text
        )
        return self._embed_batch([formatted_query])[0]

    def _embed_batch(self, batch: list[str]) -> list[list[float]]:
        from huggingface_hub import InferenceClient
        if not batch:
            return []
        try:
            output = self.client.feature_extraction(batch, model=self.model_name)
        except Exception:
            fallback_client = InferenceClient(token=self.token)
            output = fallback_client.feature_extraction(batch, model=self.model_name)

        if isinstance(output, self.np.ndarray):
            if output.ndim == 1:
                return [output.astype(float).tolist()]
            return output.astype(float).tolist()
        if isinstance(output, list):
            if output and isinstance(output[0], (int, float)):
                return [[float(v) for v in output]]
            return [[float(v) for v in row] for row in output]
        return [self.np.asarray(output, dtype=float).tolist()]


# Default Embedder alias
Embedder = JinaEmbedder
