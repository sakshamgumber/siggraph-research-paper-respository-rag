import argparse
import json
import re
from pathlib import Path
from typing import Any

from docling.chunking import HybridChunker

from src.ingestion.parser import PROCESSED_DIR, RAW_DIR, convert_document


def _label_to_text(label: Any) -> str:
    if label is None:
        return ""
    if hasattr(label, "value"):
        return str(label.value).lower()
    if hasattr(label, "name"):
        return str(label.name).lower()
    return str(label).lower()


def _first_page(chunk: Any) -> int | None:
    doc_items = getattr(getattr(chunk, "meta", None), "doc_items", None) or []
    for item in doc_items:
        for prov in getattr(item, "prov", None) or []:
            page_no = getattr(prov, "page_no", None)
            if page_no is not None:
                return page_no
    return None


def _doc_item_labels(chunk: Any) -> set[str]:
    labels = set()
    doc_items = getattr(getattr(chunk, "meta", None), "doc_items", None) or []
    for item in doc_items:
        labels.add(_label_to_text(getattr(item, "label", None)))
    return labels


def _headings(chunk: Any) -> list[str]:
    headings = getattr(getattr(chunk, "meta", None), "headings", None) or []
    return [str(heading).strip() for heading in headings if str(heading).strip()]


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "root"


def _element_type(chunk: Any) -> str:
    labels = _doc_item_labels(chunk)
    if any("picture" in label or "image" in label for label in labels):
        return "image"
    if any("table" in label for label in labels):
        return "table"
    if any("formula" in label or "equation" in label for label in labels):
        return "equation"
    return "text"


def _chunk_text(chunk: Any, doc: Any, element_type: str) -> str:
    if element_type == "table":
        tables = []
        doc_items = getattr(getattr(chunk, "meta", None), "doc_items", None) or []
        for item in doc_items:
            if "table" not in _label_to_text(getattr(item, "label", None)):
                continue
            export_to_markdown = getattr(item, "export_to_markdown", None)
            if not callable(export_to_markdown):
                continue
            table_text = export_to_markdown(doc=doc).strip()
            if table_text:
                caption = getattr(item, "caption_text", None)
                if callable(caption):
                    caption = caption(doc=doc)
                if caption and not table_text.startswith(caption.strip()):
                    table_text = f"{caption.strip()}\n\n{table_text}"
                tables.append(table_text)
        if tables:
            return "\n\n".join(tables)

    return str(getattr(chunk, "text", "")).strip()


def build_structured_chunks(
    doc: Any,
    *,
    paper_id: str,
    title: str | None = None,
    authors: list[str] | None = None,
    year: int | None = None,
    venue: str | None = None,
    start_index: int = 0,
    repeat_table_header: bool = True,
    omit_header_on_overflow: bool = False,
) -> list[dict[str, Any]]:
    """Create ordered JSON-serializable chunks from a Docling document."""
    chunker = HybridChunker(
        merge_peers=True,
        repeat_table_header=repeat_table_header,
        omit_header_on_overflow=omit_header_on_overflow,
    )
    records: list[dict[str, Any]] = []

    for chunk in chunker.chunk(dl_doc=doc):
        element_type = _element_type(chunk)
        text = _chunk_text(chunk, doc, element_type)
        if not text or element_type == "image":
            continue

        headings = _headings(chunk)
        section = headings[0] if headings else None
        subsection = headings[-1] if len(headings) > 1 else None
        chunk_index = start_index + len(records)
        chunk_id = f"{paper_id}_chunk_{chunk_index:03d}"

        records.append(
            {
                "chunk_id": chunk_id,
                "paper_id": paper_id,
                "title": title,
                "authors": authors or [],
                "year": year,
                "venue": venue,
                "section": section,
                "subsection": subsection,
                "page": _first_page(chunk),
                "previous_page_number": None,
                "next_page_number": None,
                "chunk_index": chunk_index,
                "element_type": element_type,
                "parent_chunk_id": (
                    f"{paper_id}_section_{_slug(section)}" if section else None
                ),
                "previous_chunk_id": None,
                "next_chunk_id": None,
                "text": text,
            }
        )

    for index, record in enumerate(records):
        curr_section = record.get("section") or record.get("parent_chunk_id")

        if index > 0:
            record["previous_chunk_id"] = records[index - 1]["chunk_id"]
            prev_section = (
                records[index - 1].get("section")
                or records[index - 1].get("parent_chunk_id")
            )
            # If a section gets divided across chunks, capture previous chunk's page number
            if curr_section and prev_section == curr_section:
                record["previous_page_number"] = records[index - 1].get("page")

        if index < len(records) - 1:
            record["next_chunk_id"] = records[index + 1]["chunk_id"]
            next_section = (
                records[index + 1].get("section")
                or records[index + 1].get("parent_chunk_id")
            )
            # If a section gets divided across chunks, capture next chunk's page number
            if curr_section and next_section == curr_section:
                record["next_page_number"] = records[index + 1].get("page")

    return records


def write_jsonl(records: list[dict[str, Any]], out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return out_path


def extract_pdf_chunks(
    pdf_path: str | Path,
    *,
    paper_id: str | None = None,
    title: str | None = None,
    authors: list[str] | None = None,
    year: int | None = None,
    venue: str | None = None,
    out_dir: str | Path | None = None,
    do_ocr: bool = False,
    do_formula_enrichment: bool = False,
    repeat_table_header: bool = True,
    omit_header_on_overflow: bool = False,
) -> Path:
    """Convert a PDF, chunk it with Docling HybridChunker, and write JSONL."""
    pdf_path = Path(pdf_path)
    paper_id = paper_id or pdf_path.stem
    out_dir = Path(out_dir) if out_dir else PROCESSED_DIR

    result = convert_document(
        pdf_path,
        do_ocr=do_ocr,
        do_formula_enrichment=do_formula_enrichment,
    )
    records = build_structured_chunks(
        result.document,
        paper_id=paper_id,
        title=title or getattr(result.input.file, "stem", pdf_path.stem),
        authors=authors,
        year=year,
        venue=venue,
        repeat_table_header=repeat_table_header,
        omit_header_on_overflow=omit_header_on_overflow,
    )
    return write_jsonl(records, out_dir / f"{paper_id}_chunks.jsonl")


def chunk_directory(
    in_dir: str | Path = RAW_DIR,
    *,
    out_dir: str | Path | None = None,
    do_ocr: bool = False,
    do_formula_enrichment: bool = False,
    repeat_table_header: bool = True,
    omit_header_on_overflow: bool = False,
) -> list[Path]:
    """Convert and chunk every PDF in in_dir to structured JSONL in out_dir."""
    in_path = Path(in_dir)
    if not in_path.exists():
        raise FileNotFoundError(f"Input directory not found: {in_dir}")

    pdf_files = sorted(in_path.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {in_dir}")
        return []

    print(f"Found {len(pdf_files)} PDF(s) in {in_dir} to chunk...")
    outputs: list[Path] = []
    for idx, pdf_file in enumerate(pdf_files, start=1):
        print(f"[{idx}/{len(pdf_files)}] Chunking {pdf_file.name}...")
        try:
            out_file = extract_pdf_chunks(
                pdf_file,
                out_dir=out_dir,
                do_ocr=do_ocr,
                do_formula_enrichment=do_formula_enrichment,
                repeat_table_header=repeat_table_header,
                omit_header_on_overflow=omit_header_on_overflow,
            )
            outputs.append(out_file)
            print(f"  -> Generated {out_file.name}")
        except Exception as exc:
            print(f"  ❌ Error chunking {pdf_file.name}: {exc}")

    print(f"\nChunking complete! Successfully generated {len(outputs)} JSONL file(s).")
    return outputs


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract Docling HybridChunker JSONL chunks from a PDF or directory of PDFs."
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        nargs="?",
        default=None,
        help="Path to a PDF file or a directory containing PDFs (defaults to data/raw).",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        dest="dir_path",
        help="Directory containing PDF files to chunk.",
    )
    parser.add_argument("--paper-id")
    parser.add_argument("--title")
    parser.add_argument("--author", action="append", dest="authors")
    parser.add_argument("--year", type=int)
    parser.add_argument("--venue")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Enable OCR for scanned PDFs. Off by default for born-digital papers.",
    )
    parser.add_argument(
        "--formula-enrichment",
        action="store_true",
        help="Enable Docling formula VLM enrichment. This may download large models.",
    )
    parser.add_argument(
        "--repeat-table-header",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Repeat table headers when a table spans multiple chunks (default: True).",
    )
    parser.add_argument(
        "--omit-header-on-overflow",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Omit repeated table header if row would overflow token limit (default: False).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    target = args.dir_path or args.pdf_path or RAW_DIR

    if target.is_dir():
        outputs = chunk_directory(
            target,
            out_dir=args.out_dir,
            do_ocr=args.ocr,
            do_formula_enrichment=args.formula_enrichment,
            repeat_table_header=args.repeat_table_header,
            omit_header_on_overflow=args.omit_header_on_overflow,
        )
    elif target.is_file():
        output = extract_pdf_chunks(
            target,
            paper_id=args.paper_id,
            title=args.title,
            authors=args.authors,
            year=args.year,
            venue=args.venue,
            out_dir=args.out_dir,
            do_ocr=args.ocr,
            do_formula_enrichment=args.formula_enrichment,
            repeat_table_header=args.repeat_table_header,
            omit_header_on_overflow=args.omit_header_on_overflow,
        )
        print(f"Output: {output}")
    else:
        print(f"Path not found: {target}")


