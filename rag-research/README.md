# SIGGRAPH Research RAG

## PDF extraction with Docling

Extract ordered, structured JSONL chunks from a single PDF or all PDFs in a directory:

```bash
# Chunk all PDFs in data/raw:
python3 -m src.chunking.chunker data/raw

# Or chunk a single PDF with custom metadata:
python3 -m src.chunking.chunker data/raw/paper_001.pdf \
  --paper-id paper_001 \
  --title "Neural Rendering for 3D Reconstruction" \
  --author "Author A" \
  --author "Author B" \
  --year 2024 \
  --venue SIGGRAPH
```

The output JSONL files are written to `data/processed/<paper_id>_chunks.jsonl`. Each line follows
the chunk schema used by the RAG pipeline, including `chunk_id`, `paper_id`,
paper metadata, section metadata, page number, ordered `previous_chunk_id` /
`next_chunk_id`, `element_type`, and extracted `text`.

The PDF converter enables Docling table-structure extraction and formula
enrichment can be enabled with `--formula-enrichment` when needed. OCR is off by
default for born-digital papers and can be enabled with `--ocr` for scanned PDFs.
Images are skipped for now. Tables are emitted in Docling's serialized text form,
so Markdown table column order is preserved during chunking.


## Embedding and vector storage

Embeddings are generated using **`jina-embeddings-v5-text-small`** via the Jina AI Embeddings API (`https://api.jina.ai/v1/embeddings`), producing 1024-dimensional dense vectors with task-specific adapters (`retrieval.passage` for document chunks and `retrieval.query` for search queries). Retrieval is performed using direct dense vector similarity search in Qdrant.

Configure your Jina AI API key in `rag-research/.env`:

```bash
JINA_API_KEY=your_jina_api_key_here
```
Or export it in your shell:

```bash
export JINA_API_KEY="your_jina_api_key_here"
```

Start Qdrant:

```bash
docker compose up -d qdrant
```

Index generated chunks with Jina v5 Text Small embeddings:

```bash
# Index a single paper or the entire data/processed directory:
python3 -m src.retrieval.vector_search index \
  data/processed \
  --collection research_chunks_jina_v5 \
  --batch-size 16 \
  --recreate
```

Search the indexed chunks:

```bash
python3 -m src.retrieval.vector_search search \
  "What is the multi-scale content aggregation block?" \
  --collection research_chunks_jina_v5 \
  --paper-id paper_001
```

If Docker is not running, use Qdrant's local embedded storage instead:

```bash
python3 -m src.retrieval.vector_search index \
  data/processed \
  --qdrant-path data/qdrant_local \
  --collection research_chunks_jina_v5 \
  --batch-size 16 \
  --recreate
```

## FastAPI retrieval endpoints

Run Qdrant and the API:

```bash
docker compose up -d --build qdrant api
```

Index chunks through FastAPI:

```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "jsonl_path": "data/processed",
    "collection": "research_chunks_jina_v5",
    "batch_size": 16,
    "recreate": true
  }'
```

Search through FastAPI:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the multi-scale content aggregation block?",
    "collection": "research_chunks_jina_v5",
    "limit": 5
  }'
```

## End-to-End RAG Generation with Groq LLM

Ask research questions with full retrieval, cross-encoder reranking, and Groq LLM synthesis:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the three stages of the proposed low-poly mesh generation algorithm?",
    "limit": 5,
    "rerank": true,
    "reranker_model": "jina-reranker-m0",
    "model": "openai/gpt-oss-120b"
  }'
```

The response includes:
- `answer`: Factually grounded explanation with inline citations (e.g. `[Document 1]`).
- `sources`: List of ranked chunks with titles, section names, chunk IDs, and rerank scores.
- `model`: LLM model used (e.g. `openai/gpt-oss-120b` or `openai/gpt-oss-20b`).
- `retrieval_latency_ms`, `generation_latency_ms`, `total_latency_ms`.

## Next.js + Ant Design Chat Interface

A smooth, interactive research chat UI built with Next.js 14, TypeScript, and Ant Design v5:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to chat with the research engine.

### Frontend Features:
- **Interactive Chat Interface**: Clean message bubbles with auto-scroll and quick benchmark query prompts.
- **Rich Markdown Formatting**: Supports technical formulas, code blocks, lists, and tables with inline document citations.
- **Evidence Inspector Drawer**: Inspect all retrieved evidence chunks, cosine vector similarity, and cross-encoder rerank scores.
- **Pipeline Controls**: Live switching between `openai/gpt-oss-120b` and `openai/gpt-oss-20b`, Top-$K$ slider, cross-encoder rerank toggle, and paper ID filtering.
- **Latency Telemetry**: Real-time breakdown of retrieval time, Groq LLM generation time, and token counts.

## Retrieval Evaluation & Benchmarking

Run the retrieval benchmark suite with the Evret framework against the ground-truth QA dataset:

```bash
python3 -m src.evaluation.evaluate \
  --collection research_chunks_jina_v5 \
  --rerank \
  --reranker-model jina-reranker-m0 \
  --top-k 10 \
  --output data/evaluation/siggraph_rag_eval_top10_detailed_report.json
```


