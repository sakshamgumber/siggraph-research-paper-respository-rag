import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.generation.llm import GroqGenerator
from src.retrieval.vector_search import DEFAULT_COLLECTION, index_chunks, search_chunks

app = FastAPI(
    title="SIGGRAPH Research Engine API",
    description="Vector Search & LLM Generation powered by Qdrant TurboQuant, Jina v5, and Groq.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "RAG Research API", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    collection: str = DEFAULT_COLLECTION
    limit: int = Field(5, ge=1, le=50)
    paper_id: str | None = None
    fusion: str | None = Field(
        None,
        description="Deprecated. Dense vector search is used.",
    )
    prefetch_limit: int | None = Field(
        None,
        ge=1,
        le=500,
        description="Prefetch candidate count before reranking (default: max(limit*2, 10)).",
    )
    rerank: bool = Field(
        False,
        description="Enable cross-encoder reranking with jina-reranker-m0.",
    )
    reranker_model: str = Field(
        "jina-reranker-m0",
        description="Reranker model name.",
    )


class SearchHit(BaseModel):
    score: float
    chunk_id: str | None = None
    paper_id: str | None = None
    title: str | None = None
    section: str | None = None
    subsection: str | None = None
    page: int | None = None
    previous_page_number: int | None = None
    next_page_number: int | None = None
    rerank_score: float | None = None
    vector_score: float | None = None
    text: str
    payload: dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    collection: str
    count: int
    hits: list[SearchHit]
    search_type: str = "dense"
    rerank: bool = False
    reranker_model: str | None = None
    fusion: str | None = None


class IndexRequest(BaseModel):
    jsonl_path: str = "data/processed/paper_001_chunks.jsonl"
    collection: str = DEFAULT_COLLECTION
    batch_size: int = Field(8, ge=1, le=128)
    recreate: bool = False


class IndexResponse(BaseModel):
    collection: str
    indexed: int


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    try:
        hits = search_chunks(
            request.query,
            collection_name=request.collection,
            limit=request.limit,
            paper_id=request.paper_id,
            fusion=request.fusion,
            prefetch_limit=request.prefetch_limit,
            rerank=request.rerank,
            reranker_model=request.reranker_model,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    response_hits = []
    for hit in hits:
        payload = hit.payload or {}
        response_hits.append(
            SearchHit(
                score=hit.score,
                chunk_id=payload.get("chunk_id"),
                paper_id=payload.get("paper_id"),
                title=payload.get("title"),
                section=payload.get("section"),
                subsection=payload.get("subsection"),
                page=payload.get("page"),
                previous_page_number=payload.get("previous_page_number"),
                next_page_number=payload.get("next_page_number"),
                rerank_score=payload.get("rerank_score"),
                vector_score=payload.get("vector_score"),
                text=payload.get("text", ""),
                payload=payload,
            )
        )

    return SearchResponse(
        query=request.query,
        collection=request.collection,
        count=len(response_hits),
        hits=response_hits,
        search_type="dense",
        rerank=request.rerank,
        reranker_model=request.reranker_model if request.rerank else None,
        fusion=request.fusion,
    )


@app.post("/index", response_model=IndexResponse)
def index(request: IndexRequest):
    jsonl_path = Path(request.jsonl_path)
    if not jsonl_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Chunk file not found: {request.jsonl_path}",
        )

    try:
        indexed = index_chunks(
            jsonl_path,
            collection_name=request.collection,
            batch_size=request.batch_size,
            recreate=request.recreate,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return IndexResponse(collection=request.collection, indexed=indexed)


class RagAskRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question or research topic to ask.")
    collection: str = Field(DEFAULT_COLLECTION, description="Qdrant collection name.")
    limit: int = Field(5, ge=1, le=20, description="Number of top reranked chunks to feed to LLM.")
    paper_id: str | None = Field(None, description="Optional paper ID filter.")
    prefetch_limit: int | None = Field(
        None,
        ge=1,
        le=200,
        description="Candidate count before reranking (default: max(limit*2, 10)).",
    )
    rerank: bool = Field(True, description="Enable cross-encoder reranking before LLM generation.")
    reranker_model: str = Field("jina-reranker-m0", description="Reranker model name.")
    rescore: bool = Field(True, description="Enable quantization rescoring for TurboQuant.")
    model: str | None = Field(None, description="Groq model (default: openai/gpt-oss-120b).")
    temperature: float = Field(0.2, ge=0.0, le=1.0, description="Sampling temperature.")
    max_tokens: int = Field(1024, ge=64, le=4096, description="Max generated tokens.")
    system_prompt: str | None = Field(None, description="Optional custom system prompt.")


class RagSourceChunk(BaseModel):
    rank: int
    chunk_id: str | None = None
    paper_id: str | None = None
    title: str | None = None
    section: str | None = None
    page: int | None = None
    score: float
    rerank_score: float | None = None
    vector_score: float | None = None
    snippet: str


class RagAskResponse(BaseModel):
    query: str
    answer: str
    reasoning: str | None = None
    sources: list[RagSourceChunk]
    model: str
    collection: str
    retrieval_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float
    token_usage: dict[str, Any]


@app.post("/rag/ask", response_model=RagAskResponse, tags=["RAG"])
@app.post("/ask", response_model=RagAskResponse, tags=["RAG"])
def ask(request: RagAskRequest):
    """End-to-end RAG Controller:
    1. Query Qdrant vector database (TurboQuant PQ-16 with rescoring).
    2. Rerank retrieved candidate chunks via Jina Cross-Encoder (jina-reranker-m0).
    3. Feed reranked context into Groq LLM (openai/gpt-oss-120b).
    4. Return synthesized, grounded response with inline citations and sources.
    """
    t_start = time.perf_counter()

    # Step 1: Vector Search + Cross-Encoder Reranking
    t_retrieval = time.perf_counter()
    try:
        hits = search_chunks(
            query=request.query,
            collection_name=request.collection,
            limit=request.limit,
            paper_id=request.paper_id,
            prefetch_limit=request.prefetch_limit,
            rerank=request.rerank,
            reranker_model=request.reranker_model,
            rescore=request.rescore,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Vector search/rerank failed: {exc}",
        ) from exc
    retrieval_latency_ms = (time.perf_counter() - t_retrieval) * 1000.0

    # Step 2: Format Sources for response
    sources: list[RagSourceChunk] = []
    for idx, hit in enumerate(hits, start=1):
        payload = hit.payload or {}
        text = (payload.get("text") or "").strip()
        sources.append(
            RagSourceChunk(
                rank=idx,
                chunk_id=payload.get("chunk_id"),
                paper_id=payload.get("paper_id"),
                title=payload.get("title"),
                section=payload.get("section") or payload.get("subsection"),
                page=payload.get("page"),
                score=float(hit.score),
                rerank_score=payload.get("rerank_score"),
                vector_score=payload.get("vector_score"),
                snippet=text[:300].strip(),
            )
        )

    # Step 3: LLM Generation via Groq
    try:
        generator = GroqGenerator(
            model_name=request.model or None,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        kwargs: dict[str, Any] = {}
        if request.system_prompt:
            kwargs["system_prompt"] = request.system_prompt

        gen_result = generator.generate(
            query=request.query,
            retrieved_chunks=hits,
            model_name=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            **kwargs,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Groq LLM generation failed: {exc}",
        ) from exc

    total_latency_ms = (time.perf_counter() - t_start) * 1000.0

    return RagAskResponse(
        query=request.query,
        answer=gen_result["answer"],
        reasoning=gen_result.get("reasoning"),
        sources=sources,
        model=gen_result["model"],
        collection=request.collection,
        retrieval_latency_ms=round(retrieval_latency_ms, 2),
        generation_latency_ms=gen_result["latency_ms"],
        total_latency_ms=round(total_latency_ms, 2),
        token_usage=gen_result.get("usage", {}),
    )
