export interface SourceChunk {
  rank: number;
  chunk_id: string | null;
  paper_id: string | null;
  title: string | null;
  section: string | null;
  page: number | null;
  score: number;
  rerank_score: number | null;
  vector_score: number | null;
  snippet: string;
}

export interface TokenUsage {
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sources?: SourceChunk[];
  model?: string;
  collection?: string;
  retrieval_latency_ms?: number;
  generation_latency_ms?: number;
  total_latency_ms?: number;
  token_usage?: TokenUsage;
  isError?: boolean;
}

export interface RagConfig {
  collection: string;
  limit: number;
  rerank: boolean;
  reranker_model: string;
  model: string;
  temperature: number;
  paper_id?: string;
  rescore: boolean;
}
