from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    QuantizationSearchParams,
    SearchParams,
    VectorParams,
)

from src.embeddings.embedder import (
    JINA_EMBEDDING_SIZE,
    JINA_MODEL_NAME,
    JinaEmbedder,
    QWEN_EMBEDDING_SIZE,
    QwenHuggingFaceEmbedder,
)
from src.reranking.reranker import (
    DEFAULT_RERANKER_MODEL,
    JinaReranker,
)

DEFAULT_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DEFAULT_QDRANT_PATH = os.getenv("QDRANT_PATH") or None
DEFAULT_QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "research_chunks_jina_v5")
DEFAULT_VECTOR_SIZE = JINA_EMBEDDING_SIZE
DEFAULT_RERANK_PREFETCH_LIMIT = int(os.getenv("PREFETCH_LIMIT", "10"))


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def stable_point_id(chunk_id: str) -> int:
    digest = hashlib.sha256(chunk_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def ensure_collection(
    client: QdrantClient,
    collection_name: str,
    *,
    vector_size: int = DEFAULT_VECTOR_SIZE,
    recreate: bool = False,
) -> None:
    if recreate and client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )


def build_qdrant_client(
    *,
    qdrant_url: str | None = DEFAULT_QDRANT_URL,
    qdrant_path: str | Path | None = DEFAULT_QDRANT_PATH,
    api_key: str | None = None,
    timeout: float | None = 120.0,
) -> QdrantClient:
    key = api_key or DEFAULT_QDRANT_API_KEY
    if qdrant_path and str(qdrant_path).strip() and str(qdrant_path).strip() != ".":
        return QdrantClient(path=str(qdrant_path), timeout=timeout)
    return QdrantClient(url=qdrant_url or DEFAULT_QDRANT_URL, api_key=key, timeout=timeout)


def _payload_from_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.items()
        if key != "text" and value is not None
    } | {"text": record.get("text", "")}


def index_chunks(
    jsonl_path: str | Path,
    *,
    qdrant_url: str = DEFAULT_QDRANT_URL,
    qdrant_path: str | Path | None = DEFAULT_QDRANT_PATH,
    api_key: str | None = None,
    collection_name: str = DEFAULT_COLLECTION,
    batch_size: int = 8,
    recreate: bool = False,
) -> int:
    target = Path(jsonl_path)
    if target.is_dir():
        files = sorted(target.glob("*.jsonl"))
        records = []
        for f in files:
            records.extend(load_jsonl(f))
    else:
        records = load_jsonl(target)

    client = build_qdrant_client(qdrant_url=qdrant_url, qdrant_path=qdrant_path, api_key=api_key)
    ensure_collection(client, collection_name, recreate=recreate)

    collection_info = client.get_collection(collection_name)
    vectors_config = collection_info.config.params.vectors
    is_named_dense = isinstance(vectors_config, dict) and "dense" in vectors_config

    if not recreate and client.collection_exists(collection_name):
        id_to_record = {stable_point_id(r["chunk_id"]): r for r in records}
        all_ids = list(id_to_record.keys())
        existing_ids = set()
        for i in range(0, len(all_ids), 200):
            batch_ids = all_ids[i : i + 200]
            existing_pts = client.retrieve(
                collection_name=collection_name,
                ids=batch_ids,
                with_payload=False,
                with_vectors=False,
            )
            for pt in existing_pts:
                existing_ids.add(pt.id)
        records = [r for r in records if stable_point_id(r["chunk_id"]) not in existing_ids]
        if not records:
            return 0

    embedder = JinaEmbedder(batch_size=batch_size)
    indexed = 0

    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        vectors = embedder.embed_documents(
            record.get("text", "") for record in batch
        )
        points = [
            PointStruct(
                id=stable_point_id(record["chunk_id"]),
                vector={"dense": vector} if is_named_dense else vector,
                payload=_payload_from_record(record),
            )
            for record, vector in zip(batch, vectors, strict=True)
        ]
        client.upsert(collection_name=collection_name, points=points, wait=True)
        indexed += len(points)
        print(f"Indexed {indexed}/{len(records)} chunks...", flush=True)

    return indexed


def search_chunks(
    query: str,
    *,
    qdrant_url: str = DEFAULT_QDRANT_URL,
    qdrant_path: str | Path | None = DEFAULT_QDRANT_PATH,
    api_key: str | None = None,
    collection_name: str = DEFAULT_COLLECTION,
    limit: int = 5,
    paper_id: str | None = None,
    fusion: str | None = None,
    prefetch_limit: int | None = None,
    rerank: bool = False,
    reranker_model: str = DEFAULT_RERANKER_MODEL,
    rescore: bool = True,
) -> list[Any]:
    client = build_qdrant_client(qdrant_url=qdrant_url, qdrant_path=qdrant_path, api_key=api_key)
    embedder = JinaEmbedder(batch_size=1)
    query_vector = embedder.embed_query(query)

    query_filter = None
    if paper_id:
        query_filter = Filter(
            must=[FieldCondition(key="paper_id", match=MatchValue(value=paper_id))]
        )

    collection_info = client.get_collection(collection_name)
    vectors_config = collection_info.config.params.vectors
    using_name = (
        "dense"
        if isinstance(vectors_config, dict) and "dense" in vectors_config
        else None
    )

    fetch_limit = prefetch_limit or (
        max(limit * 2, DEFAULT_RERANK_PREFETCH_LIMIT) if rerank else limit
    )
    search_params = SearchParams(
        quantization=QuantizationSearchParams(
            rescore=rescore,
        )
    )
    points = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        using=using_name,
        query_filter=query_filter,
        limit=fetch_limit,
        with_payload=True,
        search_params=search_params,
    ).points

    if rerank and points:
        reranker = JinaReranker(model_name=reranker_model)
        points = reranker.rerank(query, points, top_n=limit)

    return points[:limit]


def _parse_path_or_none(value: str | None) -> Path | None:
    if not value or not str(value).strip() or str(value).strip() == ".":
        return None
    return Path(value)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index chunk JSONL into Qdrant.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index")
    index_parser.add_argument("jsonl_path", type=Path)
    index_parser.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    index_parser.add_argument(
        "--qdrant-path",
        type=_parse_path_or_none,
        default=DEFAULT_QDRANT_PATH,
    )
    index_parser.add_argument("--api-key", default=DEFAULT_QDRANT_API_KEY)
    index_parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    index_parser.add_argument("--batch-size", type=int, default=8)
    index_parser.add_argument("--recreate", action="store_true")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    search_parser.add_argument(
        "--qdrant-path",
        type=_parse_path_or_none,
        default=DEFAULT_QDRANT_PATH,
    )
    search_parser.add_argument("--api-key", default=DEFAULT_QDRANT_API_KEY)
    search_parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    search_parser.add_argument("--limit", type=int, default=5)
    search_parser.add_argument("--paper-id")
    search_parser.add_argument(
        "--rerank",
        action="store_true",
        help="Rerank candidates using cross-encoder (jina-reranker-m0).",
    )
    search_parser.add_argument(
        "--reranker-model",
        default=DEFAULT_RERANKER_MODEL,
        help="Reranker model name (default: jina-reranker-m0).",
    )
    search_parser.add_argument(
        "--fusion",
        choices=["rrf", "dbsf", "none"],
        default="none",
        help="Deprecated. Dense vector search is used.",
    )
    search_parser.add_argument(
        "--prefetch-limit",
        type=int,
        help="Prefetch count before reranking (default: max(limit*2, 10)).",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.command == "index":
        count = index_chunks(
            args.jsonl_path,
            qdrant_url=args.qdrant_url,
            qdrant_path=args.qdrant_path,
            api_key=args.api_key,
            collection_name=args.collection,
            batch_size=args.batch_size,
            recreate=args.recreate,
        )
        print(f"Indexed {count} chunks into {args.collection}")
    elif args.command == "search":
        hits = search_chunks(
            args.query,
            qdrant_url=args.qdrant_url,
            qdrant_path=args.qdrant_path,
            api_key=args.api_key,
            collection_name=args.collection,
            limit=args.limit,
            paper_id=args.paper_id,
            fusion=args.fusion,
            prefetch_limit=args.prefetch_limit,
            rerank=args.rerank,
            reranker_model=args.reranker_model,
        )
        for hit in hits:
            payload = hit.payload or {}
            print(
                json.dumps(
                    {
                        "score": hit.score,
                        "chunk_id": payload.get("chunk_id"),
                        "section": payload.get("section"),
                        "page": payload.get("page"),
                        "text": payload.get("text", "")[:500],
                    },
                    ensure_ascii=False,
                )
            )
