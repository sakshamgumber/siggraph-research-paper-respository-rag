import logging
from pathlib import Path

from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
)
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

_log = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

ALLOWED_FORMATS = [
    InputFormat.PDF,
    InputFormat.IMAGE,
    InputFormat.DOCX,
    InputFormat.HTML,
    InputFormat.PPTX,
    InputFormat.ASCIIDOC,
    InputFormat.CSV,
    InputFormat.MD,
]


def _build_converter(
    *,
    do_ocr: bool = False,
    do_formula_enrichment: bool = False,
) -> DocumentConverter:
    pdf_options = PdfPipelineOptions()
    pdf_options.do_table_structure = True
    pdf_options.do_ocr = do_ocr
    pdf_options.do_formula_enrichment = do_formula_enrichment
    pdf_options.generate_picture_images = False

    return DocumentConverter(
        allowed_formats=ALLOWED_FORMATS,
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=StandardPdfPipeline,
                backend=PyPdfiumDocumentBackend,
                pipeline_options=pdf_options,
            ),
            InputFormat.DOCX: WordFormatOption(pipeline_cls=SimplePipeline),
        },
    )


def convert_document(
    path: str | Path,
    *,
    do_ocr: bool = False,
    do_formula_enrichment: bool = False,
):
    """Convert a document with Docling and return the conversion result."""
    converter = _build_converter(
        do_ocr=do_ocr,
        do_formula_enrichment=do_formula_enrichment,
    )
    return converter.convert(Path(path))


def parse_document(path: str | Path, out_dir: Path | None = None) -> Path:
    """Parse a single document with Docling and write markdown to out_dir."""
    converter = _build_converter()
    result = converter.convert(Path(path))
    out_dir = out_dir or PROCESSED_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{result.input.file.stem}.md"
    out_path.write_text(result.document.export_to_markdown())
    _log.info("Parsed %s -> %s", path, out_path)
    return out_path


def parse_directory(in_dir: Path | None = None, out_dir: Path | None = None) -> list[Path]:
    """Parse every supported document in in_dir (default data/raw)."""
    in_dir = in_dir or RAW_DIR
    files = [p for p in in_dir.iterdir() if p.is_file()]
    if not files:
        _log.warning("No files found in %s", in_dir)
        return []

    converter = _build_converter()
    results = converter.convert_all(files)

    out_dir = out_dir or PROCESSED_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    outputs = []
    for res in results:
        out_path = out_dir / f"{res.input.file.stem}.md"
        out_path.write_text(res.document.export_to_markdown())
        outputs.append(out_path)
        _log.info("Parsed %s -> %s", res.input.file.name, out_path)
    return outputs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(parse_directory())
