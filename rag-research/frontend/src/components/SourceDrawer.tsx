"use client";

import React from "react";
import { Drawer, Card, Tag, Typography, Space, Divider, Empty } from "antd";
import {
  ThunderboltOutlined,
  AimOutlined,
  BookOutlined,
} from "@ant-design/icons";
import { SourceChunk } from "../types/chat";

const { Text, Paragraph, Title } = Typography;

interface SourceDrawerProps {
  open: boolean;
  onClose: () => void;
  sources: SourceChunk[];
  query?: string;
}

export const SourceDrawer: React.FC<SourceDrawerProps> = ({
  open,
  onClose,
  sources,
  query,
}) => {
  return (
    <Drawer
      title={
        <Space direction="vertical" size={2}>
          <Space>
            <BookOutlined style={{ color: "#2563eb" }} />
            <Text strong style={{ fontSize: 16 }}>
              Retrieved Research Evidence ({sources.length} chunks)
            </Text>
          </Space>
          {query && (
            <Text type="secondary" ellipsis style={{ maxWidth: 450, fontSize: 12 }}>
              Query: &quot;{query}&quot;
            </Text>
          )}
        </Space>
      }
      placement="right"
      width={560}
      onClose={onClose}
      open={open}
      styles={{
        body: { background: "#f8fafc", padding: "16px 20px" },
      }}
    >
      {sources.length === 0 ? (
        <Empty description="No retrieved document chunks for this response" />
      ) : (
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          {sources.map((chunk) => {
            const rerankColor =
              chunk.rerank_score && chunk.rerank_score > 0.9
                ? "success"
                : chunk.rerank_score && chunk.rerank_score > 0.7
                ? "processing"
                : "default";

            return (
              <Card
                key={chunk.chunk_id || chunk.rank}
                size="small"
                style={{
                  borderRadius: 10,
                  boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                  border: "1px solid #e2e8f0",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                  <Space wrap size={[6, 6]}>
                    <Tag color="blue" style={{ fontWeight: 600 }}>
                      Rank #{chunk.rank}
                    </Tag>
                    {chunk.rerank_score !== null && chunk.rerank_score !== undefined && (
                      <Tag icon={<ThunderboltOutlined />} color={rerankColor}>
                        Rerank: {(chunk.rerank_score).toFixed(4)}
                      </Tag>
                    )}
                    {chunk.vector_score !== null && chunk.vector_score !== undefined && (
                      <Tag icon={<AimOutlined />}>
                        Cosine: {(chunk.vector_score).toFixed(4)}
                      </Tag>
                    )}
                    {chunk.page && (
                      <Tag color="default">Page {chunk.page}</Tag>
                    )}
                  </Space>
                </div>

                <div style={{ marginBottom: 6 }}>
                  {chunk.title && (
                    <Text strong style={{ fontSize: 14, color: "#0f172a", display: "block" }}>
                      {chunk.title}
                    </Text>
                  )}
                  <Space split={<Divider type="vertical" />} style={{ fontSize: 12 }}>
                    {chunk.paper_id && (
                      <Text type="secondary">Paper ID: {chunk.paper_id}</Text>
                    )}
                    {chunk.section && (
                      <Text type="secondary">Section: {chunk.section}</Text>
                    )}
                  </Space>
                </div>

                <div
                  style={{
                    backgroundColor: "#f1f5f9",
                    padding: "10px 12px",
                    borderRadius: 6,
                    fontSize: 13,
                    lineHeight: 1.6,
                    color: "#334155",
                    maxHeight: 260,
                    overflowY: "auto",
                    whiteSpace: "pre-wrap",
                    fontFamily: "inherit",
                  }}
                >
                  {chunk.snippet}
                </div>

                <div style={{ marginTop: 8, display: "flex", justifyContent: "flex-end" }}>
                  <Text code style={{ fontSize: 11 }}>
                    {chunk.chunk_id}
                  </Text>
                </div>
              </Card>
            );
          })}
        </Space>
      )}
    </Drawer>
  );
};
