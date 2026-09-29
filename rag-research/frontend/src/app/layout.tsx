import React from "react";
import type { Metadata } from "next";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import ThemeWrapper from "../components/ThemeWrapper";
import "./globals.css";

export const metadata: Metadata = {
  title: "SIGGRAPH RAG Assistant | Groq & TurboQuant",
  description: "AI Research Assistant grounded in 80k+ SIGGRAPH paper chunks using Qdrant TurboQuant and Groq LLM.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AntdRegistry>
          <ThemeWrapper>{children}</ThemeWrapper>
        </AntdRegistry>
      </body>
    </html>
  );
}
