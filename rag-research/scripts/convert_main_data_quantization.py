"""Script to manage quantization and resilient collection replication.

Features:
1. Resilient streaming replication with automatic retry and exponential backoff
   to prevent WriteTimeout / ReadTimeout crashes on cloud clusters.
2. Checkpoint state persistence: resumes from the exact last offset if interrupted.
3. In-place quantization toggle on any collection (Turbo4 or INT8).
4. Live cluster status reporting.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from qdrant_client import models
from src.retrieval.vector_search import build_qdrant_client

CHECKPOINT_FILE = PROJECT_ROOT / "data" / "evaluation" / ".replicate_checkpoint.json"


def get_client(timeout: float = 120.0):
    return build_qdrant_client(timeout=timeout)


def retry_call(fn, max_retries: int = 5, initial_backoff: float = 2.0, desc: str = "operation"):
    """Execute a function with exponential backoff on transient network timeouts."""
    backoff = initial_backoff
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            err_msg = str(e)
            if "timeout" in err_msg.lower() or "connection" in err_msg.lower() or "responsehandlingexception" in err_msg.lower():
                print(f"\n[Warning] Transient network error on {desc} (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    print(f"Waiting {backoff:.1f}s before retrying...")
                    time.sleep(backoff)
                    backoff *= 2.0
            else:
                raise e
    raise last_exc


def load_checkpoint() -> dict[str, Any]:
    if CHECKPOINT_FILE.exists():
        try:
            return json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_checkpoint(offset: Any, transferred: int, target_collections: list[str]):
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "offset": offset,
        "transferred": transferred,
        "target_collections": target_collections,
        "timestamp": time.time(),
    }
    CHECKPOINT_FILE.write_text(json.dumps(data), encoding="utf-8")


def clear_checkpoint():
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink(missing_ok=True)


def enable_quantization(collection_name: str, quant_type: str = "turbo4"):
    """Enable quantization in-place on an existing collection."""
    client = get_client()
    print(f"Applying {quant_type.upper()} quantization to collection '{collection_name}'...")

    if quant_type == "turbo4":
        config = models.ProductQuantization(
            product=models.ProductQuantizationConfig(
                compression=models.CompressionRatio.X16,
                always_ram=True,
            )
        )
    elif quant_type == "int8":
        config = models.ScalarQuantization(
            scalar=models.ScalarQuantizationConfig(
                type=models.ScalarType.INT8,
                quantile=0.99,
                always_ram=True,
            )
        )
    else:
        raise ValueError(f"Unknown quantization type: {quant_type}")

    retry_call(
        lambda: client.update_collection(
            collection_name=collection_name,
            quantization_config=config,
        ),
        desc=f"update_collection({collection_name})",
    )
    print(f"Successfully configured {quant_type.upper()} on '{collection_name}'. Qdrant is indexing in the background.")


def replicate_to_quantized_collections(
    source_collection: str = "research_chunks_jina_v5",
    target_collections: list[str] | None = None,
    batch_size: int = 100,
    max_points: int | None = None,
    resume: bool = True,
):
    """Stream points with resilient timeouts, retries, and checkpointing."""
    if target_collections is None:
        # Default to quant_bench_int8 since research_chunks_jina_v5 is already Turbo4!
        target_collections = ["quant_bench_int8"]

    client = get_client(timeout=120.0)
    source_info = client.get_collection(source_collection)
    total_source = source_info.points_count

    # Check for existing checkpoint
    next_offset = None
    transferred = 0
    if resume:
        ckpt = load_checkpoint()
        if ckpt and ckpt.get("target_collections") == target_collections:
            next_offset = ckpt.get("offset")
            transferred = ckpt.get("transferred", 0)
            print(f"\n[Resume] Found checkpoint! Resuming from offset {next_offset} ({transferred} points already recorded).")

    print(f"\nSource '{source_collection}': {total_source} total points.")
    print(f"Target collections: {target_collections}")
    print(f"Batch size: {batch_size} points per request (HTTP write timeout: 120s)")

    # Verify target collections exist
    for target in target_collections:
        if not client.collection_exists(target):
            print(f"Target collection '{target}' does not exist! Creating...")
            client.create_collection(
                collection_name=target,
                vectors_config=models.VectorParams(
                    size=1024,
                    distance=models.Distance.COSINE,
                ),
            )
            if "int8" in target:
                enable_quantization(target, "int8")
            elif "turbo" in target:
                enable_quantization(target, "turbo4")

    start_time = time.time()
    batch_num = 0

    while True:
        # 1. Fetch batch from source with retry
        def _scroll():
            return client.scroll(
                collection_name=source_collection,
                limit=batch_size,
                offset=next_offset,
                with_payload=True,
                with_vectors=True,
            )

        scroll_res, new_offset = retry_call(_scroll, desc=f"scroll(batch {batch_num})")

        if not scroll_res:
            print("\nNo more points returned from source collection.")
            break

        points_to_upsert = [
            models.PointStruct(
                id=p.id,
                vector=p.vector,
                payload=p.payload,
            )
            for p in scroll_res
        ]

        # 2. Upsert into each target collection with retry
        for target in target_collections:
            def _upsert():
                return client.upsert(
                    collection_name=target,
                    points=points_to_upsert,
                    wait=False,
                )

            retry_call(_upsert, desc=f"upsert({target}, {len(points_to_upsert)} pts)")

        transferred += len(points_to_upsert)
        next_offset = new_offset
        batch_num += 1

        # Save checkpoint periodically
        save_checkpoint(next_offset, transferred, target_collections)

        elapsed = time.time() - start_time
        rate = transferred / elapsed if elapsed > 0 else 0
        total_goal = max_points or total_source
        percent = min(100.0, (transferred / total_goal) * 100)
        print(
            f"Progress: {transferred}/{total_goal} points ({percent:.1f}%) "
            f"| Rate: {rate:.1f} pts/sec | Batch: {batch_num} | Elapsed: {elapsed:.1f}s"
        )

        if max_points and transferred >= max_points:
            print(f"\nReached requested limit of {max_points} points.")
            break

        if next_offset is None:
            print("\nReached the end of the collection.")
            break

    clear_checkpoint()
    print(f"\nReplication complete! Transferred {transferred} points in {time.time() - start_time:.1f}s.")


def check_status():
    """Print status of all collections and their quantization configurations."""
    client = get_client()
    collections = client.get_collections().collections
    print("\n" + "=" * 65)
    print(" LIVE QDRANT CLUSTER STATUS")
    print("=" * 65)
    for c in collections:
        info = client.get_collection(c.name)
        quant = info.config.quantization_config
        q_label = "None (FP32)"
        if quant:
            if hasattr(quant, "scalar") and quant.scalar:
                q_label = f"Scalar ({quant.scalar.type.value.upper()})"
            elif hasattr(quant, "product") and quant.product:
                q_label = f"Product Quant (Turbo {quant.product.compression.value.upper()})"
        print(f"Collection : {c.name:<26} | Points: {info.points_count:<7} | Quantization: {q_label}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert and replicate collections with quantization.")
    parser.add_argument("--status", action="store_true", help="Display cluster collections status")
    parser.add_argument("--enable-quant", choices=["turbo4", "int8"], help="Enable quantization on a collection")
    parser.add_argument("--collection", default="research_chunks_jina_v5", help="Target collection for --enable-quant")
    parser.add_argument("--replicate", action="store_true", help="Replicate points from source to target collections")
    parser.add_argument("--targets", nargs="+", default=None, help="Target collection names to replicate into")
    parser.add_argument("--max-points", type=int, default=None, help="Limit number of points to replicate")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for point replication (default: 100)")
    parser.add_argument("--no-resume", action="store_true", help="Do not resume from checkpoint; restart from beginning")

    args = parser.parse_args()

    if args.status or (len(sys.argv) == 1 and not args.replicate and not args.enable_quant):
        check_status()
    elif args.enable_quant:
        enable_quantization(args.collection, args.enable_quant)
        check_status()
    elif args.replicate:
        replicate_to_quantized_collections(
            source_collection=args.collection,
            target_collections=args.targets,
            batch_size=args.batch_size,
            max_points=args.max_points,
            resume=not args.no_resume,
        )
        check_status()
