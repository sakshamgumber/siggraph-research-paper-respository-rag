from __future__ import annotations

import copy
import os
import time
from typing import Any
from pathlib import Path

from dotenv import load_dotenv
import requests

from src.embeddings.embedder import get_shared_session

# Load environment variables from .env if present
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv()

JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"
DEFAULT_RERANKER_MODEL = "jina-reranker-m0"


class JinaReranker:
    """Cross-encoder reranker using Jina AI's Reranker API (jina-reranker-m0) with connection pooling."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = DEFAULT_RERANKER_MODEL,
        *,
        timeout: float = 45.0,
        max_retries: int = 3,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("JINA_API_KEY")
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = session or get_shared_session()

    def rerank(
        self,
        query: str,
        candidates: list[Any],
        *,
        top_n: int = 5,
    ) -> list[Any]:
        """Rerank a list of candidate chunks against a query.

        Args:
            query: The search query string.
            candidates: List of candidate objects (e.g. ScoredPoint, dicts, or strings).
            top_n: Maximum number of reranked results to return.

        Returns:
            List of candidates reordered by relevance score descending.
        """
        if not candidates or not query.strip():
            return candidates[:top_n]

        if not self.api_key:
            raise ValueError(
                "Jina API key not configured. Set JINA_API_KEY in .env or pass api_key to JinaReranker."
            )

        # Extract textual content from candidate objects
        doc_texts: list[str] = []
        for cand in candidates:
            if hasattr(cand, "payload") and isinstance(cand.payload, dict):
                text = cand.payload.get("text", "")
            elif isinstance(cand, dict):
                text = cand.get("text") or cand.get("payload", {}).get("text", "")
            elif isinstance(cand, str):
                text = cand
            else:
                text = str(cand)
            doc_texts.append(text.strip() if text and text.strip() else " ")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model_name,
            "query": query.strip(),
            "documents": doc_texts,
            "top_n": min(top_n, len(candidates)),
        }

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.post(
                    JINA_RERANK_URL,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    return self._build_reranked_output(candidates, results)

                if response.status_code == 429 and attempt < self.max_retries:
                    retry_after = int(response.headers.get("Retry-After", 10 * attempt))
                    time.sleep(retry_after)
                    continue

                if response.status_code in (500, 502, 503, 504) and attempt < self.max_retries:
                    time.sleep(2.0 * attempt)
                    continue

                raise RuntimeError(
                    f"Jina Rerank API failed (HTTP {response.status_code}): {response.text}"
                )
            except (requests.RequestException, RuntimeError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(2.0 * attempt)
                else:
                    raise RuntimeError(
                        f"Failed to rerank with Jina API after {self.max_retries} attempts: {exc}"
                    ) from exc

        if last_error:
            raise last_error
        return candidates[:top_n]

    def _build_reranked_output(
        self,
        candidates: list[Any],
        rerank_results: list[dict[str, Any]],
    ) -> list[Any]:
        reranked: list[Any] = []
        for item in rerank_results:
            orig_idx = item.get("index", 0)
            if orig_idx < 0 or orig_idx >= len(candidates):
                continue
            cand = candidates[orig_idx]
            relevance = float(item.get("relevance_score", 0.0))

            # If candidate is a Qdrant ScoredPoint or similar object
            if hasattr(cand, "score"):
                try:
                    cand_copy = copy.copy(cand)
                    if hasattr(cand, "payload") and isinstance(cand.payload, dict):
                        cand_copy.payload = copy.deepcopy(cand.payload)
                        cand_copy.payload["vector_score"] = cand.score
                        cand_copy.payload["rerank_score"] = relevance
                    cand_copy.score = relevance
                    reranked.append(cand_copy)
                except Exception:
                    cand.score = relevance
                    reranked.append(cand)
            elif isinstance(cand, dict):
                cand_copy = copy.deepcopy(cand)
                cand_copy["vector_score"] = cand.get("score")
                cand_copy["score"] = relevance
                cand_copy["rerank_score"] = relevance
                if "payload" in cand_copy and isinstance(cand_copy["payload"], dict):
                    cand_copy["payload"]["vector_score"] = cand.get("score")
                    cand_copy["payload"]["rerank_score"] = relevance
                reranked.append(cand_copy)
            else:
                reranked.append(cand)
        return reranked
