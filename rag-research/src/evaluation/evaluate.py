from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any

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
from evret.evaluation.results import EvaluationResults

from src.retrieval.vector_search import (
    DEFAULT_COLLECTION,
    DEFAULT_QDRANT_API_KEY,
    DEFAULT_QDRANT_PATH,
    DEFAULT_QDRANT_URL,
    search_chunks,
)

DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "evaluation" / "benchmark_qa.json"
)
DEFAULT_REPORT_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "evaluation" / "evaluation_report.json"
)


class ResearchEngineRetriever(BaseRetriever):
    """Evret BaseRetriever integration for the SIGGRAPH Jina v5 research engine."""

    def __init__(
        self,
        collection_name: str = DEFAULT_COLLECTION,
        *,
        qdrant_url: str = DEFAULT_QDRANT_URL,
        qdrant_path: str | Path | None = DEFAULT_QDRANT_PATH,
        api_key: str | None = None,
        paper_id: str | None = None,
        rerank: bool = False,
        reranker_model: str = "jina-reranker-m0",
    ) -> None:
        self.collection_name = collection_name
        self.qdrant_url = qdrant_url
        self.qdrant_path = qdrant_path
        self.api_key = api_key or DEFAULT_QDRANT_API_KEY
        self.paper_id = paper_id
        self.rerank = rerank
        self.reranker_model = reranker_model
        self.query_count = 0
        self.query_records: list[dict[str, Any]] = []

    def retrieve(self, query: str, k: int = 5) -> list[RetrievalResult]:
        """Execute dense retrieval via search_chunks and return Evret RetrievalResults."""
        self.query_count += 1
        print(f"[{self.query_count:02d}] Evaluating query: \"{query[:55]}...\"")
        hits = search_chunks(
            query=query,
            collection_name=self.collection_name,
            qdrant_url=self.qdrant_url,
            qdrant_path=self.qdrant_path,
            api_key=self.api_key,
            limit=k,
            paper_id=self.paper_id,
            rerank=self.rerank,
            reranker_model=self.reranker_model,
        )
        results = []
        for hit in hits:
            payload = hit.payload or {}
            doc_id = payload.get("chunk_id") or str(hit.id)
            results.append(
                RetrievalResult(
                    doc_id=doc_id,
                    score=float(hit.score),
                    metadata=payload,
                )
            )
        if results:
            print(f"     Top-1: {results[0].doc_id} (score: {results[0].score:.4f})")

        self.query_records.append({
            "query": query,
            "k": k,
            "results": [
                {
                    "rank": idx + 1,
                    "doc_id": r.doc_id,
                    "score": round(r.score, 6),
                    "paper_id": (r.metadata or {}).get("paper_id"),
                    "chunk_index": (r.metadata or {}).get("chunk_index"),
                    "text_snippet": ((r.metadata or {}).get("text") or "")[:250].replace("\n", " ").strip(),
                }
                for idx, r in enumerate(results)
            ],
        })
        return results


def load_dataset_for_evret(
    dataset_path: str | Path,
) -> tuple[EvaluationDataset, list[dict[str, Any]]]:
    """Load an evaluation dataset supporting both standard Evret format and flat list."""
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found: {dataset_path}")

    raw_data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw_data, dict) and "queries" in raw_data:
        raw_queries = raw_data["queries"]
        return EvaluationDataset.from_json(path), raw_queries
    elif isinstance(raw_data, list):
        raw_queries = raw_data
        temp_obj = {"queries": raw_data}
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".json", delete=False
        ) as tmp:
            tmp.write(json.dumps(temp_obj))
            tmp_path = Path(tmp.name)
        try:
            return EvaluationDataset.from_json(tmp_path), raw_queries
        finally:
            tmp_path.unlink(missing_ok=True)
    else:
        raise ValueError(
            "Dataset must be a JSON object with 'queries' list or a list of query objects."
        )


def run_evret_evaluation(
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
    *,
    collection_name: str = DEFAULT_COLLECTION,
    qdrant_url: str = DEFAULT_QDRANT_URL,
    qdrant_path: str | Path | None = DEFAULT_QDRANT_PATH,
    api_key: str | None = None,
    top_k: int = 5,
    paper_id: str | None = None,
    rerank: bool = False,
    reranker_model: str = "jina-reranker-m0",
    output_report_path: str | Path | None = DEFAULT_REPORT_PATH,
) -> EvaluationResults:
    """Run retrieval evaluation using the Evret framework."""
    dataset, raw_queries = load_dataset_for_evret(dataset_path)

    retriever = ResearchEngineRetriever(
        collection_name=collection_name,
        qdrant_url=qdrant_url,
        qdrant_path=qdrant_path,
        api_key=api_key,
        paper_id=paper_id,
        rerank=rerank,
        reranker_model=reranker_model,
    )

    metrics = [
        HitRate(k=1),
        HitRate(k=3),
    ]
    if top_k != 5:
        metrics.extend([HitRate(k=5), Recall(k=5)])
    metrics.extend([
        HitRate(k=top_k),
        MRR(k=top_k),
        NDCG(k=top_k),
        Precision(k=1),
        Recall(k=top_k),
    ])

    print(f"\n========================================================")
    print(f" Evret Retrieval Evaluation")
    print(f" Collection : {collection_name}")
    print(f" Dataset    : {dataset_path} ({len(dataset.queries)} queries)")
    print(f" Top-K      : {top_k}")
    print(f"========================================================\n")

    evaluator = Evaluator(retriever=retriever, metrics=metrics)
    start_time = time.perf_counter()
    results = evaluator.evaluate(dataset)
    elapsed_total_ms = (time.perf_counter() - start_time) * 1000.0

    scores = results.metric_scores
    avg_latency = elapsed_total_ms / max(len(dataset.queries), 1)

    print("========================================================")
    print("                 EVRET EVALUATION SUMMARY")
    print("========================================================")
    print(f" Total Queries Tested    : {results.query_count}")
    print(f" Hit Rate @ 1            : {scores.get('hit_rate@1', 0.0) * 100:.2f}%")
    print(f" Hit Rate @ 3            : {scores.get('hit_rate@3', 0.0) * 100:.2f}%")
    if top_k != 5 and "hit_rate@5" in scores:
        print(f" Hit Rate @ 5            : {scores.get('hit_rate@5', 0.0) * 100:.2f}%")
    print(f" Hit Rate @ {top_k:<2}           : {scores.get(f'hit_rate@{top_k}', 0.0) * 100:.2f}%")
    print(f" MRR @ {top_k:<2}                : {scores.get(f'mrr@{top_k}', 0.0):.4f}")
    print(f" NDCG @ {top_k:<2}               : {scores.get(f'ndcg@{top_k}', 0.0):.4f}")
    print(f" Precision @ 1           : {scores.get('precision@1', 0.0) * 100:.2f}%")
    if top_k != 5 and "recall@5" in scores:
        print(f" Recall @ 5              : {scores.get('recall@5', 0.0) * 100:.2f}%")
    print(f" Recall @ {top_k:<2}             : {scores.get(f'recall@{top_k}', 0.0) * 100:.2f}%")
    print(f" Avg Query Latency       : {avg_latency:.2f} ms")
    print("========================================================\n")

    # Build per-query detailed records and category breakdown
    per_query_results: list[dict[str, Any]] = []
    category_buckets: dict[str, list[dict[str, Any]]] = {}

    for idx, (raw_q, rec) in enumerate(zip(raw_queries, retriever.query_records)):
        expected_ids = set(raw_q.get("expected_doc_ids", []))
        retrieved_list = rec.get("results", [])

        annotated_chunks = []
        retrieved_gold_ids = []
        first_hit_rank = None

        for c in retrieved_list:
            c_doc_id = c["doc_id"]
            is_gold = c_doc_id in expected_ids
            if is_gold:
                retrieved_gold_ids.append(c_doc_id)
                if first_hit_rank is None:
                    first_hit_rank = c["rank"]
            annotated_chunks.append({
                "rank": c["rank"],
                "doc_id": c_doc_id,
                "score": c["score"],
                "is_gold": is_gold,
                "paper_id": c.get("paper_id"),
                "chunk_index": c.get("chunk_index"),
                "text_snippet": c.get("text_snippet"),
            })

        hit_at_1 = any(c["is_gold"] for c in annotated_chunks if c["rank"] <= 1)
        hit_at_3 = any(c["is_gold"] for c in annotated_chunks if c["rank"] <= 3)
        hit_at_5 = any(c["is_gold"] for c in annotated_chunks if c["rank"] <= 5)
        hit_at_k = any(c["is_gold"] for c in annotated_chunks if c["rank"] <= top_k)

        unique_gold_found = list(dict.fromkeys(retrieved_gold_ids))
        unique_expected = list(dict.fromkeys(raw_q.get("expected_doc_ids", [])))

        recall_k = (
            (len(unique_gold_found) / len(unique_expected))
            if unique_expected
            else (1.0 if not raw_q.get("answerable", True) else 0.0)
        )

        gold_at_5 = [
            c["doc_id"]
            for c in annotated_chunks
            if c["rank"] <= 5 and c["is_gold"]
        ]
        recall_5 = (
            (len(set(gold_at_5)) / len(unique_expected))
            if unique_expected
            else (1.0 if not raw_q.get("answerable", True) else 0.0)
        )

        q_item = {
            "query_id": raw_q.get("query_id", f"rag_{idx+1:03d}"),
            "question_number": raw_q.get("question_number", idx + 1),
            "query_text": raw_q.get("query_text") or raw_q.get("query"),
            "category": raw_q.get("category", "General"),
            "difficulty": raw_q.get("difficulty"),
            "pdf_number": raw_q.get("pdf_number"),
            "paper_id": raw_q.get("paper_id"),
            "paper_title": raw_q.get("paper_title"),
            "answerable": raw_q.get("answerable", True),
            "expected_doc_ids": unique_expected,
            "expected_answers": raw_q.get("expected_answers", []),
            "retrieved_gold_ids": unique_gold_found,
            "hits_found_count": len(unique_gold_found),
            "expected_count": len(unique_expected),
            "first_hit_rank": first_hit_rank,
            "hit_at_1": hit_at_1,
            "hit_at_3": hit_at_3,
            "hit_at_5": hit_at_5,
            f"hit_at_{top_k}": hit_at_k,
            "precision_at_1": 1.0 if hit_at_1 else 0.0,
            "recall_at_5": round(recall_5, 4),
            f"recall_at_{top_k}": round(recall_k, 4),
            "mrr": round(1.0 / first_hit_rank, 4) if first_hit_rank else 0.0,
            "retrieved_chunks": annotated_chunks,
        }
        per_query_results.append(q_item)

        cat = q_item["category"]
        category_buckets.setdefault(cat, []).append(q_item)

    category_metrics: dict[str, Any] = {}
    for cat, items in category_buckets.items():
        cat_count = len(items)
        cat_hits_k = sum(1 for it in items if it[f"hit_at_{top_k}"])
        cat_recall_k = sum(it[f"recall_at_{top_k}"] for it in items) / max(cat_count, 1)
        category_metrics[cat] = {
            "query_count": cat_count,
            f"hit_rate@{top_k}": round(cat_hits_k / max(cat_count, 1), 4),
            f"avg_recall@{top_k}": round(cat_recall_k, 4),
        }

    answerable_items = [it for it in per_query_results if it["answerable"]]
    answerable_count = len(answerable_items)
    answerable_metrics = {
        "total_answerable": answerable_count,
        f"hit_rate@{top_k}": round(
            sum(1 for it in answerable_items if it[f"hit_at_{top_k}"]) / max(answerable_count, 1),
            4,
        ),
        f"avg_recall@{top_k}": round(
            sum(it[f"recall_at_{top_k}"] for it in answerable_items) / max(answerable_count, 1),
            4,
        ),
    }

    if output_report_path:
        out_path = Path(output_report_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        report_dict = results.to_dict()
        report_dict["collection"] = collection_name
        report_dict["top_k"] = top_k
        report_dict["rerank"] = rerank
        report_dict["reranker_model"] = reranker_model if rerank else None
        report_dict["avg_latency_ms"] = round(avg_latency, 2)
        report_dict["answerable_metrics"] = answerable_metrics
        report_dict["category_metrics"] = category_metrics
        report_dict["per_query_results"] = per_query_results
        out_path.write_text(json.dumps(report_dict, indent=2), encoding="utf-8")
        print(f"Detailed Evret report saved to: {out_path}\n")

    return results

    return results


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate RAG retrieval engine with Evret framework."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to evaluation JSON dataset.",
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help="Qdrant collection name.",
    )
    parser.add_argument(
        "--qdrant-url",
        default=DEFAULT_QDRANT_URL,
        help="Qdrant service URL.",
    )
    parser.add_argument(
        "--qdrant-path",
        type=Path,
        default=DEFAULT_QDRANT_PATH,
        help="Local embedded Qdrant directory.",
    )
    parser.add_argument(
        "--api-key",
        default=DEFAULT_QDRANT_API_KEY,
        help="Qdrant API key for online cluster.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of top candidates to retrieve.",
    )
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="Enable cross-encoder reranking with jina-reranker-m0.",
    )
    parser.add_argument(
        "--reranker-model",
        default="jina-reranker-m0",
        help="Reranker model name (default: jina-reranker-m0).",
    )
    parser.add_argument(
        "--paper-id",
        help="Optional paper ID filter.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Path to save evaluation results JSON.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_evret_evaluation(
        dataset_path=args.dataset,
        collection_name=args.collection,
        qdrant_url=args.qdrant_url,
        qdrant_path=args.qdrant_path,
        api_key=args.api_key,
        top_k=args.top_k,
        paper_id=args.paper_id,
        rerank=args.rerank,
        reranker_model=args.reranker_model,
        output_report_path=args.output,
    )
