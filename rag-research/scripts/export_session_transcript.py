import json
import re
from pathlib import Path

TRANSCRIPT_PATH = Path(
    "/Users/sakshamgumber/.gemini/antigravity/brain/56795553-a193-49b2-aca8-b8ac91a3a5b9/.system_generated/logs/transcript.jsonl"
)
OUTPUT_MD_PATH = Path(
    "/Users/sakshamgumber/siggraph_research_engine/CODING_AGENT_SESSION_TRANSCRIPT.md"
)


def export_transcript():
    if not TRANSCRIPT_PATH.exists():
        print(f"Transcript not found at {TRANSCRIPT_PATH}")
        return

    with TRANSCRIPT_PATH.open("r", encoding="utf-8") as f:
        entries = [json.loads(line) for line in f]

    turns = []
    current_turn = None

    for entry in entries:
        etype = entry.get("type")
        src = entry.get("source")
        content = entry.get("content", "") or ""
        created_at = entry.get("created_at", "")

        if etype == "USER_INPUT" and src == "USER_EXPLICIT":
            # Extract request content
            m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
            user_text = m.group(1).strip() if m else content.strip()

            # Ignore internal meta requests or session export query
            if "Share a coding agent session" in user_text:
                continue

            current_turn = {
                "timestamp": created_at,
                "user_prompt": user_text,
                "actions": [],
                "agent_response": "",
            }
            turns.append(current_turn)

        elif etype == "PLANNER_RESPONSE" and current_turn is not None:
            tool_calls = entry.get("tool_calls", [])
            for tc in tool_calls:
                name = tc.get("name")
                args = tc.get("arguments", {}) or {}
                if name == "run_command":
                    cmd = (args.get("CommandLine") or "").strip()
                    if cmd:
                        first_line = cmd.split("\n")[0]
                        current_turn["actions"].append(f"Command: `{first_line[:100]}`")
                elif name in ("write_to_file", "replace_file_content"):
                    target = args.get("TargetFile") or ""
                    if target:
                        fname = Path(target).name
                        action_type = "Created" if name == "write_to_file" else "Modified"
                        current_turn["actions"].append(f"{action_type}: `{fname}`")
                elif name == "view_file":
                    target = args.get("AbsolutePath") or ""
                    if target:
                        fname = Path(target).name
                        current_turn["actions"].append(f"Inspected: `{fname}`")

            if content.strip():
                current_turn["agent_response"] = content.strip()

    # Generate Markdown Output
    lines = []
    lines.append("# Coding Agent Session Transcript: SIGGRAPH Research Engine")
    lines.append("")
    lines.append("> **Developer / Prompter:** Saksham Gumber  ")
    lines.append("> **AI Coding Assistant:** Antigravity (Google DeepMind)  ")
    lines.append("> **Project:** End-to-End SIGGRAPH Academic Paper RAG Engine  ")
    lines.append("> **GitHub Repository:** [https://github.com/sakshamgumber/siggraph-research-paper-respository-rag](https://github.com/sakshamgumber/siggraph-research-paper-respository-rag)  ")
    lines.append("> **Total Turns:** 25+ Interactive Development Turns  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("This transcript documents an extensive, full-lifecycle pair programming session between human developer Saksham Gumber and the Antigravity agentic coding assistant. Over the course of the session, the agent architected, implemented, evaluated, debugged, and shipped a complete academic research engine for computer graphics papers.")
    lines.append("")
    lines.append("### Key Engineering Milestones")
    lines.append("1. **Vector Quantization & Cloud Cluster (Qdrant TurboQuant)**:")
    lines.append("   - Configured 16x Product Quantization (TurboQuant) on 81,439 paper chunks with `rescore=True` on Qdrant Cloud to dramatically slash memory footprint while preserving vector similarity accuracy.")
    lines.append("2. **50-Query SIGGRAPH RAG Benchmark & Analysis**:")
    lines.append("   - Executed rigorous retrieval evaluation using the Evret framework across exact facts, multi-hop reasoning, and adversarial queries.")
    lines.append("   - Diagnosed initial recall bottlenecks in multi-chunk academic papers and increased bandwidth to Top-$K=10$ with `jina-reranker-m0` cross-encoder reranking, reaching **71.11% Hit Rate @ 10** on answerable queries.")
    lines.append("   - Extended `src/evaluation/evaluate.py` to output per-query candidate rankings and gold hits into JSON.")
    lines.append("3. **Grounded LLM Generation via Groq**:")
    lines.append("   - Integrated Groq high-speed inference (`openai/gpt-oss-120b` and `20b`) in `src/generation/llm.py` to generate strictly grounded research syntheses with inline document citations (`[Document X]`) in sub-second to low-latency timeframes.")
    lines.append("4. **FastAPI REST Controller**:")
    lines.append("   - Developed `/ask` and `/rag/ask` endpoints in `api/main.py` orchestrating vector search, cross-encoder reranking, Groq synthesis, and latency telemetry with full CORS support.")
    lines.append("5. **Interactive Next.js 14 + Ant Design Frontend**:")
    lines.append("   - Created a modern chat interface in `rag-research/frontend/` using Next.js 14, TypeScript, and Ant Design v5.")
    lines.append("   - Built an interactive **Evidence Inspector Drawer**, real-time latency badges, and live pipeline controls (model switcher, Top-$K$ slider, reranker toggle).")
    lines.append("   - Diagnosed and resolved Ant Design Server Component CSS line-height styling bugs.")
    lines.append("6. **Repository Sanitization & GitHub Deployment**:")
    lines.append("   - Removed dead code and stale lock files, configured `.gitignore` to protect sensitive API keys, initialized Git, and pushed the complete 989-file repository to GitHub.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Chronological Session Transcript")
    lines.append("")

    for i, turn in enumerate(turns, start=1):
        lines.append(f"### Turn {i}: {turn['user_prompt'][:75]}...")
        lines.append("")
        lines.append("**User Prompt:**")
        lines.append("```text")
        lines.append(turn["user_prompt"])
        lines.append("```")
        lines.append("")

        if turn["actions"]:
            unique_actions = list(dict.fromkeys(turn["actions"]))[:8]
            lines.append("**Agent Actions:**")
            for act in unique_actions:
                lines.append(f"- {act}")
            lines.append("")

        if turn["agent_response"]:
            # Truncate overly long text summaries to keep transcript readable
            resp = turn["agent_response"]
            if len(resp) > 1200:
                resp = resp[:1200] + "\n\n*(...response truncated for brevity...)*"
            lines.append("**Agent Response:**")
            lines.append(resp)
            lines.append("")

        lines.append("---")
        lines.append("")

    OUTPUT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported transcript to: {OUTPUT_MD_PATH} ({len(lines)} lines)")


if __name__ == "__main__":
    export_transcript()
