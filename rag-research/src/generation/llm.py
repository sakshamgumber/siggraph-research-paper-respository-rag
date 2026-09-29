from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq

# Load environment variables from project .env
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv()

DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
FALLBACK_GROQ_MODEL = "openai/gpt-oss-20b"

RAG_SYSTEM_PROMPT = """You are an expert AI research assistant specializing in Computer Graphics, Vision, and SIGGRAPH technical papers.
Your task is to answer the user's question using ONLY the provided retrieved research documents.

Guidelines:
1. Ground your answer strictly in the provided document chunks.
2. Provide technical, thorough, and precise explanations referencing formulas, algorithms, architecture components, and empirical metrics when mentioned in the context.
3. Use inline citations like [Document 1], [Document 2] to attribute facts to their source chunks.
4. If the retrieved documents do not contain sufficient evidence to answer the question, state clearly and concisely what information is missing instead of speculating or hallucinating.
"""


class GroqGenerator:
    """LLM Generation service powered by Groq high-speed inference."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = DEFAULT_GROQ_MODEL,
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Groq API key not found. Please set GROQ_API_KEY in .env or pass api_key to GroqGenerator."
            )
        self.model_name = model_name or DEFAULT_GROQ_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = Groq(api_key=self.api_key)

    def format_context(self, chunks: list[Any]) -> str:
        """Format retrieved and reranked chunks into structured context for the LLM."""
        if not chunks:
            return "No relevant research chunks retrieved."

        context_blocks: list[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            if hasattr(chunk, "payload") and isinstance(chunk.payload, dict):
                payload = chunk.payload
                score = getattr(chunk, "score", None)
            elif isinstance(chunk, dict):
                payload = chunk.get("payload", chunk)
                score = chunk.get("score")
            else:
                payload = {"text": str(chunk)}
                score = None

            chunk_id = payload.get("chunk_id", f"chunk_{idx}")
            paper_id = payload.get("paper_id", "Unknown")
            title = payload.get("title", "")
            section = payload.get("section") or payload.get("subsection") or ""
            text = (payload.get("text") or "").strip()
            rerank_score = payload.get("rerank_score")

            header_parts = [f"Chunk ID: {chunk_id}"]
            if paper_id and paper_id != "Unknown":
                header_parts.append(f"Paper: {paper_id}")
            if title:
                header_parts.append(f"Title: {title}")
            if section:
                header_parts.append(f"Section: {section}")
            if rerank_score is not None:
                header_parts.append(f"Rerank Score: {rerank_score:.4f}")
            elif score is not None:
                header_parts.append(f"Score: {score:.4f}")

            header_str = " | ".join(header_parts)
            context_blocks.append(f"--- [Document {idx}] ({header_str}) ---\n{text}\n")

        return "\n".join(context_blocks)

    def generate(
        self,
        query: str,
        retrieved_chunks: list[Any],
        *,
        system_prompt: str = RAG_SYSTEM_PROMPT,
        model_name: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate a grounded research answer from retrieved documents using Groq.

        Args:
            query: The user research query.
            retrieved_chunks: List of reranked research document chunks.
            system_prompt: Custom system prompt instructions.
            model_name: Optional override for the Groq model.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens in generated completion.

        Returns:
            Dictionary with 'answer', 'reasoning', 'model', 'usage', and 'latency_ms'.
        """
        model = model_name or self.model_name
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        formatted_context = self.format_context(retrieved_chunks)

        user_content = f"""Retrieved Research Context:
{formatted_context}

User Query:
{query}

Please provide a clear, factual answer synthesized from the retrieved research context above."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        t0 = time.perf_counter()
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
            )
        except Exception as exc:
            # If the primary model failed (e.g. rate limit/unsupported), try fallback model
            if model != FALLBACK_GROQ_MODEL:
                print(f"Model {model} failed ({exc}). Retrying with fallback {FALLBACK_GROQ_MODEL}...")
                model = FALLBACK_GROQ_MODEL
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens,
                )
            else:
                raise

        latency_ms = (time.perf_counter() - t0) * 1000.0

        choice = response.choices[0]
        answer_text = choice.message.content or ""
        reasoning_text = getattr(choice.message, "reasoning", None)

        usage = {}
        if getattr(response, "usage", None):
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return {
            "answer": answer_text.strip(),
            "reasoning": reasoning_text.strip() if reasoning_text else None,
            "model": model,
            "usage": usage,
            "latency_ms": round(latency_ms, 2),
        }
