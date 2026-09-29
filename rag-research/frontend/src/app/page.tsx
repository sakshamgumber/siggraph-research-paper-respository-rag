"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Layout,
  Typography,
  Input,
  Button,
  Space,
  Tag,
  Badge,
  Card,
  Slider,
  Switch,
  Select,
  Tooltip,
  Divider,
  Spin,
  Alert,
  Empty,
  message,
} from "antd";
import {
  SendOutlined,
  ThunderboltOutlined,
  SettingOutlined,
  ClearOutlined,
  BookOutlined,
  QuestionCircleOutlined,
  CheckCircleFilled,
  CloseCircleFilled,
  FireOutlined,
  ExperimentOutlined,
} from "@ant-design/icons";
import { ChatMessage, RagConfig, SourceChunk } from "../types/chat";
import { ChatMessageItem } from "../components/ChatMessageItem";

const { Header, Content, Sider } = Layout;
const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const DEFAULT_CONFIG: RagConfig = {
  collection: "research_chunks_jina_v5",
  limit: 5,
  rerank: true,
  reranker_model: "jina-reranker-m0",
  model: "openai/gpt-oss-120b",
  temperature: 0.2,
  rescore: true,
};

const SUGGESTED_QUERIES = [
  "What are the three stages of the proposed low-poly mesh generation algorithm?",
  "How many building models were used to evaluate the low-poly mesh generation method?",
  "What two temporal coherence losses are proposed for portrait animation?",
  "How does MoRF represent multiple human identities while sharing a neural radiance field?",
  "What does CRF correction change about the correlation between objective metrics and visual quality?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState<RagConfig>(DEFAULT_CONFIG);
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const [siderCollapsed, setSiderCollapsed] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);

  // Check backend health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
        const res = await fetch(`${apiUrl}/health`);
        setApiConnected(res.ok);
      } catch (err) {
        setApiConnected(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (queryText?: string) => {
    const textToSend = (queryText || inputValue).trim();
    if (!textToSend || loading) return;

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setLoading(true);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

    try {
      const payload: Record<string, any> = {
        query: textToSend,
        collection: config.collection,
        limit: config.limit,
        rerank: config.rerank,
        reranker_model: config.reranker_model,
        model: config.model,
        temperature: config.temperature,
        rescore: config.rescore,
      };

      if (config.paper_id && config.paper_id.trim()) {
        payload.paper_id = config.paper_id.trim();
      }

      const res = await fetch(`${apiUrl}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errorData.detail || `Server responded with ${res.status}`);
      }

      const data = await res.json();

      const assistantMessage: ChatMessage = {
        id: `assistant_${Date.now()}`,
        role: "assistant",
        content: data.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        sources: data.sources as SourceChunk[],
        model: data.model,
        collection: data.collection,
        retrieval_latency_ms: data.retrieval_latency_ms,
        generation_latency_ms: data.generation_latency_ms,
        total_latency_ms: data.total_latency_ms,
        token_usage: data.token_usage,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error("RAG query failed:", err);
      const errorMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        role: "assistant",
        content: `**Error generating response:**\n${err.message || "Failed to connect to RAG backend. Make sure the FastAPI server is running on port 8000."}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
      message.error("Failed to generate response");
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleClear = () => {
    setMessages([]);
    message.info("Chat history cleared");
  };

  return (
    <Layout style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Top Header */}
      <Header
        style={{
          background: "#ffffff",
          borderBottom: "1px solid #e2e8f0",
          padding: "0 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: 68,
          lineHeight: "normal",
          zIndex: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div
            style={{
              width: 38,
              height: 38,
              minWidth: 38,
              borderRadius: 8,
              background: "linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#ffffff",
              fontSize: 18,
              boxShadow: "0 2px 8px rgba(37, 99, 235, 0.3)",
            }}
          >
            <BookOutlined />
          </div>
          <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, lineHeight: 1.2, marginBottom: 3 }}>
              <span style={{ fontSize: 16, fontWeight: 700, color: "#0f172a" }}>
                SIGGRAPH Research Assistant
              </span>
              <Tag color="blue" style={{ fontSize: 11, fontWeight: 600, margin: 0, padding: "0 6px", lineHeight: "20px" }}>
                TurboQuant + Groq
              </Tag>
            </div>
            <span style={{ fontSize: 12, color: "#64748b", lineHeight: 1.2 }}>
              81,439 Paper Chunks • Jina v5 • Cross-Encoder Rerank
            </span>
          </div>
        </div>

        <Space size={14} align="center">
          {/* Backend Status indicator */}
          <Tooltip title={apiConnected ? "Backend API Connected (port 8000)" : "Backend Disconnected"}>
            <Tag
              icon={apiConnected ? <CheckCircleFilled /> : <CloseCircleFilled />}
              color={apiConnected ? "success" : "error"}
              style={{ padding: "3px 10px", borderRadius: 12, fontSize: 12 }}
            >
              {apiConnected ? "API Online" : "API Offline"}
            </Tag>
          </Tooltip>

          <Button
            icon={<ClearOutlined />}
            onClick={handleClear}
            disabled={messages.length === 0}
            size="middle"
          >
            Clear
          </Button>

          <Button
            icon={<SettingOutlined />}
            type={siderCollapsed ? "default" : "primary"}
            onClick={() => setSiderCollapsed(!siderCollapsed)}
            size="middle"
          >
            Settings
          </Button>
        </Space>
      </Header>

      <Layout style={{ flex: 1, overflow: "hidden" }}>
        {/* Main Chat Area */}
        <Content
          style={{
            display: "flex",
            flexDirection: "column",
            height: "100%",
            background: "#f8fafc",
            overflow: "hidden",
          }}
        >
          {/* Scrollable Messages Container */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "24px 28px",
            }}
          >
            {messages.length === 0 ? (
              <div
                style={{
                  maxWidth: 720,
                  margin: "40px auto 0",
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    width: 64,
                    height: 64,
                    borderRadius: "50%",
                    background: "#eff6ff",
                    color: "#2563eb",
                    fontSize: 28,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    margin: "0 auto 16px",
                  }}
                >
                  <FireOutlined />
                </div>
                <Title level={3} style={{ marginBottom: 8, color: "#0f172a" }}>
                  Ask SIGGRAPH Research Questions
                </Title>
                <Paragraph type="secondary" style={{ fontSize: 15, maxWidth: 520, margin: "0 auto 28px" }}>
                  Grounded technical answers synthesized from 81,439 computer graphics paper chunks with Qdrant TurboQuant vector search, Jina cross-encoder reranking, and Groq LLM inference.
                </Paragraph>

                {/* Suggestions Grid */}
                <div style={{ textAlign: "left" }}>
                  <Text strong style={{ fontSize: 13, color: "#64748b", textTransform: "uppercase", letterSpacing: 0.5 }}>
                    Suggested Benchmark Queries
                  </Text>
                  <Space direction="vertical" size={10} style={{ width: "100%", marginTop: 12 }}>
                    {SUGGESTED_QUERIES.map((q, idx) => (
                      <Card
                        key={idx}
                        hoverable
                        size="small"
                        onClick={() => handleSend(q)}
                        style={{
                          borderRadius: 8,
                          borderColor: "#e2e8f0",
                          cursor: "pointer",
                          transition: "all 0.2s",
                        }}
                        styles={{ body: { padding: "10px 14px" } }}
                      >
                        <Space align="start">
                          <QuestionCircleOutlined style={{ color: "#2563eb", marginTop: 3 }} />
                          <Text style={{ fontSize: 13.5, color: "#334155" }}>{q}</Text>
                        </Space>
                      </Card>
                    ))}
                  </Space>
                </div>
              </div>
            ) : (
              <div style={{ maxWidth: 960, margin: "0 auto" }}>
                {messages.map((msg) => (
                  <ChatMessageItem key={msg.id} message={msg} />
                ))}

                {/* Thinking / Loading indicator */}
                {loading && (
                  <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
                    <div
                      style={{
                        width: 38,
                        height: 38,
                        borderRadius: "50%",
                        background: "#2563eb",
                        color: "#fff",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      <Spin size="small" />
                    </div>
                    <Card
                      size="small"
                      style={{
                        borderRadius: "4px 16px 16px 16px",
                        border: "1px solid #e2e8f0",
                        background: "#ffffff",
                      }}
                      styles={{ body: { padding: "12px 18px" } }}
                    >
                      <Space>
                        <Spin size="small" />
                        <Text type="secondary" style={{ fontSize: 13 }}>
                          Searching TurboQuant index, reranking chunks, and synthesizing answer with Groq...
                        </Text>
                      </Space>
                    </Card>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Bottom Chat Input Bar */}
          <div
            style={{
              padding: "16px 28px 24px",
              background: "#ffffff",
              borderTop: "1px solid #e2e8f0",
            }}
          >
            <div style={{ maxWidth: 960, margin: "0 auto" }}>
              <div
                style={{
                  display: "flex",
                  gap: 12,
                  alignItems: "flex-end",
                  background: "#ffffff",
                  border: "1.5px solid #cbd5e1",
                  borderRadius: 12,
                  padding: "8px 12px",
                  boxShadow: "0 2px 6px rgba(0, 0, 0, 0.03)",
                  transition: "border-color 0.2s",
                }}
              >
                <TextArea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Ask a question about computer graphics papers (e.g. low-poly meshing, NeRF, BRDFs, motion fields)..."
                  autoSize={{ minRows: 1, maxRows: 5 }}
                  bordered={false}
                  style={{
                    resize: "none",
                    padding: 0,
                    fontSize: 14.5,
                  }}
                  disabled={loading}
                />
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={() => handleSend()}
                  loading={loading}
                  disabled={!inputValue.trim()}
                  style={{
                    borderRadius: 8,
                    height: 38,
                    padding: "0 18px",
                    fontWeight: 600,
                  }}
                >
                  Ask
                </Button>
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginTop: 8,
                  fontSize: 12,
                  color: "#94a3b8",
                }}
              >
                <Space size={12}>
                  <span>Model: <strong>{config.model}</strong></span>
                  <span>•</span>
                  <span>Top-K: <strong>{config.limit}</strong></span>
                  <span>•</span>
                  <span>Reranker: <strong>{config.rerank ? "On (jina-reranker-m0)" : "Off"}</strong></span>
                </Space>
                <span>Press Enter to send, Shift + Enter for new line</span>
              </div>
            </div>
          </div>
        </Content>

        {/* Collapsible Settings Sider */}
        {!siderCollapsed && (
          <Sider
            width={310}
            theme="light"
            style={{
              borderLeft: "1px solid #e2e8f0",
              padding: "20px 18px",
              overflowY: "auto",
            }}
          >
            <Space direction="vertical" size={20} style={{ width: "100%" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <SettingOutlined style={{ color: "#2563eb", fontSize: 16 }} />
                <Title level={5} style={{ margin: 0 }}>
                  RAG Pipeline Controls
                </Title>
              </div>

              {/* Model Selection */}
              <div>
                <Text strong style={{ fontSize: 13, display: "block", marginBottom: 6 }}>
                  Groq LLM Model
                </Text>
                <Select
                  value={config.model}
                  onChange={(val) => setConfig({ ...config, model: val })}
                  style={{ width: "100%" }}
                  options={[
                    {
                      label: "openai/gpt-oss-120b (High Reasoning)",
                      value: "openai/gpt-oss-120b",
                    },
                    {
                      label: "openai/gpt-oss-20b (Sub-second Speed)",
                      value: "openai/gpt-oss-20b",
                    },
                  ]}
                />
              </div>

              {/* Top-K Chunks */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <Text strong style={{ fontSize: 13 }}>Top-K Chunks to Retrieve</Text>
                  <Tag color="blue">{config.limit}</Tag>
                </div>
                <Slider
                  min={1}
                  max={15}
                  value={config.limit}
                  onChange={(val) => setConfig({ ...config, limit: val })}
                />
                <Text type="secondary" style={{ fontSize: 11 }}>
                  Number of reranked research chunks fed into the LLM context.
                </Text>
              </div>

              {/* Reranker Toggle */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <Text strong style={{ fontSize: 13, display: "block" }}>
                    Cross-Encoder Rerank
                  </Text>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    jina-reranker-m0
                  </Text>
                </div>
                <Switch
                  checked={config.rerank}
                  onChange={(checked) => setConfig({ ...config, rerank: checked })}
                />
              </div>

              {/* TurboQuant Rescore */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <Text strong style={{ fontSize: 13, display: "block" }}>
                    TurboQuant Rescore
                  </Text>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    16x PQ exact re-ranking
                  </Text>
                </div>
                <Switch
                  checked={config.rescore}
                  onChange={(checked) => setConfig({ ...config, rescore: checked })}
                />
              </div>

              {/* Paper ID Filter */}
              <div>
                <Text strong style={{ fontSize: 13, display: "block", marginBottom: 6 }}>
                  Paper ID Filter (Optional)
                </Text>
                <Input
                  placeholder="e.g. 3528233.3530716"
                  value={config.paper_id || ""}
                  onChange={(e) => setConfig({ ...config, paper_id: e.target.value })}
                  allowClear
                />
                <Text type="secondary" style={{ fontSize: 11 }}>
                  Limit search strictly to a specific SIGGRAPH publication.
                </Text>
              </div>

              {/* Temperature */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <Text strong style={{ fontSize: 13 }}>Temperature</Text>
                  <Tag>{config.temperature}</Tag>
                </div>
                <Slider
                  min={0.0}
                  max={1.0}
                  step={0.1}
                  value={config.temperature}
                  onChange={(val) => setConfig({ ...config, temperature: val })}
                />
                <Text type="secondary" style={{ fontSize: 11 }}>
                  Lower temperature produces more strictly grounded answers.
                </Text>
              </div>

              <Divider style={{ margin: "10px 0" }} />

              <Card
                size="small"
                style={{ background: "#f1f5f9", border: "none", borderRadius: 8 }}
                styles={{ body: { padding: "12px 14px" } }}
              >
                <Space direction="vertical" size={4}>
                  <Text strong style={{ fontSize: 12, color: "#334155" }}>
                    Stack Info
                  </Text>
                  <Text style={{ fontSize: 11, color: "#64748b" }}>
                    • Vector DB: Qdrant Cloud (PQ-16)
                  </Text>
                  <Text style={{ fontSize: 11, color: "#64748b" }}>
                    • Chunks: 81,439 points
                  </Text>
                  <Text style={{ fontSize: 11, color: "#64748b" }}>
                    • Embedding: jina-v5 (1024-d)
                  </Text>
                  <Text style={{ fontSize: 11, color: "#64748b" }}>
                    • LLM Engine: Groq High-Speed
                  </Text>
                </Space>
              </Card>
            </Space>
          </Sider>
        )}
      </Layout>
    </Layout>
  );
}
