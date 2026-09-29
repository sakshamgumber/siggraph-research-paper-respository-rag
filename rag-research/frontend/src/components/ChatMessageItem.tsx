"use client";

import React, { useState } from "react";
import { Avatar, Button, Card, Space, Tag, Typography, Tooltip, message } from "antd";
import {
  UserOutlined,
  RobotOutlined,
  CopyOutlined,
  CheckOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
  FileSearchOutlined,
  ApiOutlined,
} from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChatMessage } from "../types/chat";
import { SourceDrawer } from "./SourceDrawer";

const { Text } = Typography;

interface ChatMessageItemProps {
  message: ChatMessage;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message: msg }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.content);
    setCopied(true);
    message.success("Copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  const isUser = msg.role === "user";

  if (isUser) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          marginBottom: 20,
          paddingLeft: 40,
        }}
      >
        <Space direction="horizontal" align="start" size={12}>
          <div
            style={{
              backgroundColor: "#2563eb",
              color: "#ffffff",
              padding: "12px 18px",
              borderRadius: "18px 18px 4px 18px",
              maxWidth: 680,
              boxShadow: "0 2px 8px rgba(37, 99, 235, 0.2)",
              fontSize: 15,
              lineHeight: 1.5,
              wordBreak: "break-word",
            }}
          >
            {msg.content}
            <div
              style={{
                fontSize: 11,
                color: "rgba(255, 255, 255, 0.7)",
                textAlign: "right",
                marginTop: 4,
              }}
            >
              {msg.timestamp}
            </div>
          </div>
          <Avatar
            style={{ backgroundColor: "#1e40af" }}
            icon={<UserOutlined />}
            size={38}
          />
        </Space>
      </div>
    );
  }

  // Assistant Response Card
  const sourcesCount = msg.sources?.length || 0;

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "flex-start",
        marginBottom: 24,
        paddingRight: 40,
      }}
    >
      <Space direction="horizontal" align="start" size={12} style={{ width: "100%" }}>
        <Avatar
          style={{
            background: "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)",
            boxShadow: "0 2px 6px rgba(59, 130, 246, 0.3)",
          }}
          icon={<RobotOutlined />}
          size={38}
        />
        <div style={{ flex: 1, maxWidth: 840 }}>
          <Card
            style={{
              borderRadius: "4px 18px 18px 18px",
              boxShadow: "0 2px 10px rgba(0, 0, 0, 0.04)",
              border: msg.isError ? "1px solid #fecaca" : "1px solid #e2e8f0",
              background: msg.isError ? "#fff5f5" : "#ffffff",
            }}
            styles={{ body: { padding: "16px 20px" } }}
          >
            {/* Header Telemetry Badges */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 12,
                flexWrap: "wrap",
                gap: 6,
              }}
            >
              <Space wrap size={[6, 6]}>
                <Tag color="geekblue" icon={<ApiOutlined />}>
                  {msg.model || "Groq LLM"}
                </Tag>
                {msg.retrieval_latency_ms !== undefined && (
                  <Tag icon={<DatabaseOutlined />} color="cyan">
                    Retrieval: {(msg.retrieval_latency_ms / 1000).toFixed(2)}s
                  </Tag>
                )}
                {msg.generation_latency_ms !== undefined && (
                  <Tag icon={<ThunderboltOutlined />} color="purple">
                    Groq: {(msg.generation_latency_ms / 1000).toFixed(2)}s
                  </Tag>
                )}
                {msg.total_latency_ms !== undefined && (
                  <Tag icon={<ClockCircleOutlined />}>
                    Total: {(msg.total_latency_ms / 1000).toFixed(2)}s
                  </Tag>
                )}
              </Space>

              <Space size={6}>
                <Tooltip title="Copy Answer">
                  <Button
                    type="text"
                    size="small"
                    icon={copied ? <CheckOutlined style={{ color: "#16a34a" }} /> : <CopyOutlined />}
                    onClick={handleCopy}
                  />
                </Tooltip>
              </Space>
            </div>

            {/* Markdown Body */}
            <div className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.content}
              </ReactMarkdown>
            </div>

            {/* Footer with Source Evidence Button */}
            {sourcesCount > 0 && (
              <div
                style={{
                  marginTop: 14,
                  paddingTop: 10,
                  borderTop: "1px dashed #e2e8f0",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <Button
                  type="link"
                  size="small"
                  icon={<FileSearchOutlined />}
                  onClick={() => setDrawerOpen(true)}
                  style={{ padding: 0, fontWeight: 500 }}
                >
                  Inspect {sourcesCount} Retrieved Evidence Chunk{sourcesCount > 1 ? "s" : ""}
                </Button>

                {msg.token_usage?.total_tokens && (
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {msg.token_usage.total_tokens} tokens
                  </Text>
                )}
              </div>
            )}
          </Card>
        </div>
      </Space>

      {/* Sources Drawer */}
      {msg.sources && (
        <SourceDrawer
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          sources={msg.sources}
          query={msg.content}
        />
      )}
    </div>
  );
};
