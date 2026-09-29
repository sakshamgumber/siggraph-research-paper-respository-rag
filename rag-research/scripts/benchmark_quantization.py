import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from evret import (
    BaseRetriever,
    EvaluationDataset,
    Evaluator,
    HitRate,
    MRR,
    NDCG,
    Precision,
    Recall,
    RetrievalResult,
)

from src.embeddings.embedder import JinaEmbedder
from src.retrieval.vector_search import build_qdrant_client
from src.evaluation.evaluate import load_dataset_for_evret


class CachedVectorRetriever(BaseRetriever):
    """Retriever that uses precomputed query vectors to isolate Qdrant search performance."""

    def __init__(
        self,
        collection_name: str,
        query_vectors: dict[str, list[float]],
        client: Any,
    ) -> None:
        self.collection_name = collection_name
        self.query_vectors = query_vectors
        self.client = client
        self.latencies_ms: list[float] = []

    def retrieve(self, query: str, k: int = 5) -> list[RetrievalResult]:
        vector = self.query_vectors[query]
        t0 = time.perf_counter()
        points = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=k,
            with_payload=True,
        ).points
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        self.latencies_ms.append(elapsed_ms)

        results: list[RetrievalResult] = []
        for p in points:
            payload = p.payload or {}
            doc_id = payload.get("chunk_id") or str(p.id)
            results.append(
                RetrievalResult(
                    doc_id=doc_id,
                    score=float(p.score),
                    metadata=payload,
                )
            )
        return results


def run_quantization_benchmark(
    dataset_path: str | Path = "data/evaluation/styleid_benchmark_40q.json",
    top_k: int = 5,
    output_report: str | Path = "data/evaluation/quantization_comparison_report.json",
) -> dict[str, Any]:
    dataset = load_dataset_for_evret(dataset_path)
    client = build_qdrant_client()

    collections = [
        ("FP32 (Baseline)", "quant_bench_fp32", "1x (4.0 KB/vec)"),
        ("INT8 (Scalar Quant)", "quant_bench_int8", "4x (1.0 KB/vec)"),
        ("Turbo4 (Product Quant)", "quant_bench_turbo4", "16x (~0.25 KB/vec)"),
    ]

    print("\n" + "=" * 70)
    print(f" Pre-computing Query Embeddings for {len(dataset.queries)} Queries...")
    print("=" * 70)
    embedder = JinaEmbedder(batch_size=16)
    unique_queries = list(dict.fromkeys(q.query_text for q in dataset.queries))
    query_vectors_list: list[list[float]] = []
    for i in range(0, len(unique_queries), 16):
        batch = unique_queries[i : i + 16]
        query_vectors_list.extend(embedder._embed_batch(batch, task="retrieval.query"))
    query_vectors = dict(zip(unique_queries, query_vectors_list))
    print(f"Generated {len(query_vectors)} query vectors (dim={len(query_vectors_list[0])}).\n")

    metrics = [
        HitRate(k=1),
        HitRate(k=3),
        HitRate(k=top_k),
        MRR(k=top_k),
        NDCG(k=top_k),
        Precision(k=1),
        Recall(k=top_k),
    ]

    comparison_results = {}

    for label, col_name, compression_ratio in collections:
        print(f"--- Running Evret Benchmark on {label} ({col_name}) ---")
        retriever = CachedVectorRetriever(
            collection_name=col_name,
            query_vectors=query_vectors,
            client=client,
        )
        evaluator = Evaluator(retriever=retriever, metrics=metrics)
        res = evaluator.evaluate(dataset)
        scores = res.metric_scores

        latencies = retriever.latencies_ms
        avg_lat = statistics.mean(latencies)
        p50_lat = statistics.median(latencies)
        p95_lat = sorted(latencies)[int(0.95 * len(latencies))]

        col_info = client.get_collection(col_name)

        entry = {
            "label": label,
            "collection": col_name,
            "compression_ratio": compression_ratio,
            "points_count": col_info.points_count,
            "indexed_vectors_count": col_info.indexed_vectors_count,
            "hit_rate_at_1": round(scores.get("hit_rate@1", 0.0) * 100, 2),
            "hit_rate_at_3": round(scores.get("hit_rate@3", 0.0) * 100, 2),
            "hit_rate_at_5": round(scores.get(f"hit_rate@{top_k}", 0.0) * 100, 2),
            "mrr_at_5": round(scores.get(f"mrr@{top_k}", 0.0), 4),
            "ndcg_at_5": round(scores.get(f"ndcg@{top_k}", 0.0), 4),
            "precision_at_1": round(scores.get("precision@1", 0.0) * 100, 2),
            "recall_at_5": round(scores.get(f"recall@{top_k}", 0.0) * 100, 2),
            "latency_avg_ms": round(avg_lat, 2),
            "latency_p50_ms": round(p50_lat, 2),
            "latency_p95_ms": round(p95_lat, 2),
        }
        comparison_results[col_name] = entry
        print(f"  Hit Rate @ 1 : {entry['hit_rate_at_1']}%")
        print(f"  Hit Rate @ 5 : {entry['hit_rate_at_5']}%")
        print(f"  MRR @ 5      : {entry['mrr_at_5']}")
        print(f"  NDCG @ 5     : {entry['ndcg_at_5']}")
        print(f"  Avg Latency  : {entry['latency_avg_ms']} ms (p50: {entry['latency_p50_ms']} ms, p95: {entry['latency_p95_ms']} ms)\n")

    # Save to report file
    out_file = Path(output_report)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(comparison_results, indent=2), encoding="utf-8")
    print(f"Saved full comparison report to: {out_file}")

    return comparison_results


if __name__ == "__main__":
    run_quantization_benchmark()
