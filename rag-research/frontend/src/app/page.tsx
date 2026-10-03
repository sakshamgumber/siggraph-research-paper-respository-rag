"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Layout,
  Typography,
  Input,
  Button,
  Space,
  Tag,
  Card,
  Slider,
  Switch,
  Select,
  Tooltip,
  Divider,
  Spin,
  Drawer,
  message,
} from "antd";
import {
  SendOutlined,
  SettingOutlined,
  ClearOutlined,
  BookOutlined,
  QuestionCircleOutlined,
  CheckCircleFilled,
  CloseCircleFilled,
  FireOutlined,
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

// Hook to detect mobile breakpoint
function useIsMobile(breakpoint = 768) {
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < breakpoint);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, [breakpoint]);
  return isMobile;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState<RagConfig>(DEFAULT_CONFIG);
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const isMobile = useIsMobile();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);

  // Check backend health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://reasonable-amazement-production-8284.up.railway.app";
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

    // Close settings drawer on mobile when sending
    if (isMobile) setSettingsOpen(false);

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setLoading(true);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://reasonable-amazement-production-8284.up.railway.app";

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
        content: `**Error generating response:**\n${err.message || "Failed to connect to RAG backend. Make sure the backend server is reachable."}`,
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

  // Shared settings panel content (used in both Sider and Drawer)
  const SettingsContent = (
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
            { label: "openai/gpt-oss-120b (High Reasoning)", value: "openai/gpt-oss-120b" },
            { label: "openai/gpt-oss-20b (Sub-second Speed)", value: "openai/gpt-oss-20b" },
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
          <Text strong style={{ fontSize: 13, display: "block" }}>Cross-Encoder Rerank</Text>
          <Text type="secondary" style={{ fontSize: 11 }}>jina-reranker-m0</Text>
        </div>
        <Switch
          checked={config.rerank}
          onChange={(checked) => setConfig({ ...config, rerank: checked })}
        />
      </div>

      {/* TurboQuant Rescore */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <Text strong style={{ fontSize: 13, display: "block" }}>TurboQuant Rescore</Text>
          <Text type="secondary" style={{ fontSize: 11 }}>16x PQ exact re-ranking</Text>
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
          <Text strong style={{ fontSize: 12, color: "#334155" }}>Stack Info</Text>
          <Text style={{ fontSize: 11, color: "#64748b" }}>• Vector DB: Qdrant Cloud (PQ-16)</Text>
          <Text style={{ fontSize: 11, color: "#64748b" }}>• Chunks: 81,439 points</Text>
          <Text style={{ fontSize: 11, color: "#64748b" }}>• Embedding: jina-v5 (1024-d)</Text>
          <Text style={{ fontSize: 11, color: "#64748b" }}>• LLM Engine: Groq High-Speed</Text>
        </Space>
      </Card>
    </Space>
  );

  return (
    <Layout style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* ── Top Header ── */}
      <Header
        style={{
          background: "#ffffff",
          borderBottom: "1px solid #e2e8f0",
          padding: isMobile ? "0 12px" : "0 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: isMobile ? 56 : 68,
          lineHeight: "normal",
          zIndex: 10,
          flexShrink: 0,
        }}
      >
        {/* Left — Logo + Title */}
        <div style={{ display: "flex", alignItems: "center", gap: isMobile ? 8 : 14, minWidth: 0 }}>
          <div
            style={{
              width: isMobile ? 32 : 38,
              height: isMobile ? 32 : 38,
              minWidth: isMobile ? 32 : 38,
              borderRadius: 8,
              background: "linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#ffffff",
              fontSize: isMobile ? 15 : 18,
              boxShadow: "0 2px 8px rgba(37, 99, 235, 0.3)",
            }}
          >
            <BookOutlined />
          </div>
          <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, lineHeight: 1.2, marginBottom: 2, flexWrap: "wrap" }}>
              <span style={{ fontSize: isMobile ? 13 : 16, fontWeight: 700, color: "#0f172a", whiteSpace: "nowrap" }}>
                {isMobile ? "SIGGRAPH RAG" : "SIGGRAPH Research Assistant"}
              </span>
              {!isMobile && (
                <Tag color="blue" style={{ fontSize: 11, fontWeight: 600, margin: 0, padding: "0 6px", lineHeight: "20px" }}>
                  TurboQuant + Groq
                </Tag>
              )}
            </div>
            {!isMobile && (
              <span style={{ fontSize: 12, color: "#64748b", lineHeight: 1.2 }}>
                81,439 Paper Chunks • Jina v5 • Cross-Encoder Rerank
              </span>
            )}
          </div>
        </div>

        {/* Right — Actions */}
        <Space size={isMobile ? 6 : 14} align="center">
          <Tooltip title={apiConnected ? "Backend API Connected" : "Backend Disconnected"}>
            <Tag
              icon={apiConnected ? <CheckCircleFilled /> : <CloseCircleFilled />}
              color={apiConnected ? "success" : "error"}
              style={{ padding: isMobile ? "2px 6px" : "3px 10px", borderRadius: 12, fontSize: isMobile ? 11 : 12, margin: 0 }}
            >
              {isMobile ? (apiConnected ? "Online" : "Offline") : (apiConnected ? "API Online" : "API Offline")}
            </Tag>
          </Tooltip>

          <Button
            icon={<ClearOutlined />}
            onClick={handleClear}
            disabled={messages.length === 0}
            size={isMobile ? "small" : "middle"}
          >
            {isMobile ? null : "Clear"}
          </Button>

          <Button
            icon={<SettingOutlined />}
            type={settingsOpen ? "primary" : "default"}
            onClick={() => setSettingsOpen(!settingsOpen)}
            size={isMobile ? "small" : "middle"}
          >
            {isMobile ? null : "Settings"}
          </Button>
        </Space>
      </Header>

      {/* ── Body ── */}
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
          {/* Scrollable Messages */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: isMobile ? "16px 14px" : "24px 28px",
              WebkitOverflowScrolling: "touch",
            }}
          >
            {messages.length === 0 ? (
              <div
                style={{
                  maxWidth: 720,
                  margin: isMobile ? "16px auto 0" : "40px auto 0",
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    width: isMobile ? 48 : 64,
                    height: isMobile ? 48 : 64,
                    borderRadius: "50%",
                    background: "#eff6ff",
                    color: "#2563eb",
                    fontSize: isMobile ? 20 : 28,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    margin: "0 auto 12px",
                  }}
                >
                  <FireOutlined />
                </div>
                <Title level={isMobile ? 4 : 3} style={{ marginBottom: 8, color: "#0f172a" }}>
                  Ask SIGGRAPH Research Questions
                </Title>
                <Paragraph
                  type="secondary"
                  style={{
                    fontSize: isMobile ? 13 : 15,
                    maxWidth: 520,
                    margin: "0 auto 20px",
                  }}
                >
                  {isMobile
                    ? "Grounded answers from 81,439 paper chunks with Qdrant, Jina reranking, and Groq LLM."
                    : "Grounded technical answers synthesized from 81,439 computer graphics paper chunks with Qdrant TurboQuant vector search, Jina cross-encoder reranking, and Groq LLM inference."}
                </Paragraph>

                {/* Suggestion Cards */}
                <div style={{ textAlign: "left" }}>
                  <Text strong style={{ fontSize: 12, color: "#64748b", textTransform: "uppercase", letterSpacing: 0.5 }}>
                    Suggested Benchmark Queries
                  </Text>
                  <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 10 }}>
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
                        styles={{ body: { padding: isMobile ? "8px 10px" : "10px 14px" } }}
                      >
                        <Space align="start">
                          <QuestionCircleOutlined style={{ color: "#2563eb", marginTop: 3, flexShrink: 0 }} />
                          <Text style={{ fontSize: isMobile ? 12.5 : 13.5, color: "#334155" }}>{q}</Text>
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

                {loading && (
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
                    <div
                      style={{
                        width: 34,
                        height: 34,
                        borderRadius: "50%",
                        background: "#2563eb",
                        color: "#fff",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
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
                        flex: 1,
                      }}
                      styles={{ body: { padding: "10px 14px" } }}
                    >
                      <Space>
                        <Spin size="small" />
                        <Text type="secondary" style={{ fontSize: isMobile ? 12 : 13 }}>
                          {isMobile
                            ? "Searching and synthesizing..."
                            : "Searching TurboQuant index, reranking chunks, and synthesizing answer with Groq..."}
                        </Text>
                      </Space>
                    </Card>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* ── Bottom Input Bar ── */}
          <div
            style={{
              padding: isMobile ? "10px 12px 14px" : "16px 28px 24px",
              background: "#ffffff",
              borderTop: "1px solid #e2e8f0",
              flexShrink: 0,
            }}
          >
            <div style={{ maxWidth: 960, margin: "0 auto" }}>
              <div
                style={{
                  display: "flex",
                  gap: 8,
                  alignItems: "flex-end",
                  background: "#ffffff",
                  border: "1.5px solid #cbd5e1",
                  borderRadius: 12,
                  padding: isMobile ? "6px 10px" : "8px 12px",
                  boxShadow: "0 2px 6px rgba(0,0,0,0.03)",
                }}
              >
                <TextArea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey && !isMobile) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder={
                    isMobile
                      ? "Ask about SIGGRAPH papers..."
                      : "Ask a question about computer graphics papers (e.g. low-poly meshing, NeRF, BRDFs, motion fields)..."
                  }
                  autoSize={{ minRows: 1, maxRows: isMobile ? 4 : 5 }}
                  bordered={false}
                  style={{ resize: "none", padding: 0, fontSize: isMobile ? 14 : 14.5 }}
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
                    height: isMobile ? 34 : 38,
                    padding: isMobile ? "0 12px" : "0 18px",
                    fontWeight: 600,
                  }}
                >
                  {isMobile ? null : "Ask"}
                </Button>
              </div>

              {/* Status bar — hidden on mobile to save space */}
              {!isMobile && (
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
              )}

              {/* Compact status on mobile */}
              {isMobile && (
                <div style={{ marginTop: 6, fontSize: 11, color: "#94a3b8", textAlign: "center" }}>
                  {config.model.includes("120b") ? "120b" : "20b"} · Top-K {config.limit} · Rerank {config.rerank ? "On" : "Off"}
                </div>
              )}
            </div>
          </div>
        </Content>

        {/* ── Desktop: fixed right Sider ── */}
        {!isMobile && settingsOpen && (
          <Sider
            width={310}
            theme="light"
            style={{
              borderLeft: "1px solid #e2e8f0",
              padding: "20px 18px",
              overflowY: "auto",
            }}
          >
            {SettingsContent}
          </Sider>
        )}
      </Layout>

      {/* ── Mobile: bottom Drawer for settings ── */}
      {isMobile && (
        <Drawer
          title="RAG Pipeline Controls"
          placement="bottom"
          open={settingsOpen}
          onClose={() => setSettingsOpen(false)}
          height="80vh"
          styles={{
            body: { padding: "16px 18px", overflowY: "auto", WebkitOverflowScrolling: "touch" },
            header: { padding: "14px 18px" },
          }}
        >
          {SettingsContent}
        </Drawer>
      )}
    </Layout>
  );
}
