"""PyMuPDF-only conversion path (no Docling / Torch)."""

from __future__ import annotations

import html
import logging
from pathlib import Path

import pymupdf as fitz

from .reconcile import extract_pymupdf_blocks
from .serialize import write_markdown_from_blocks
from .types import DoclingConversionResult

logger = logging.getLogger(__name__)


def _markdown_from_pymupdf(input_path: Path) -> str:
    try:
        import pymupdf4llm  # type: ignore[import-untyped]

        return pymupdf4llm.to_markdown(str(input_path))
    except ImportError:
        blocks = extract_pymupdf_blocks(input_path)
        tmp = input_path.parent / f".{input_path.stem}-fast.md"
        write_markdown_from_blocks(blocks, tmp)
        content = tmp.read_text(encoding="utf-8")
        tmp.unlink(missing_ok=True)
        return content


def _html_from_markdown(markdown: str, title: str) -> str:
    body = html.escape(markdown)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="UTF-8">\n'
        f"  <title>{html.escape(title)}</title>\n"
        "  <style>body{font-family:system-ui,sans-serif;max-width:48rem;margin:2rem auto;"
        "line-height:1.5;white-space:pre-wrap;}</style>\n"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )


def _export_images(doc: fitz.Document, images_dir: Path, doc_filename: str) -> int:
    images_dir.mkdir(parents=True, exist_ok=True)
    counter = 0
    seen: set[int] = set()

    for page in doc:
        for image in page.get_images():
            xref = image[0]
            if xref in seen:
                continue
            seen.add(xref)
            try:
                extracted = doc.extract_image(xref)
                ext = extracted.get("ext", "png")
                counter += 1
                out_path = images_dir / f"{doc_filename}-picture-{counter}.{ext}"
                out_path.write_bytes(extracted["image"])
            except Exception as exc:
                logger.debug("Skipping image xref %s: %s", xref, exc)

    return counter


def convert_with_pymupdf(
    input_doc_path: str | Path,
    output_dir: Path,
) -> DoclingConversionResult:
    input_path = Path(input_doc_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    images_dir = output_dir / "images"
    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    doc_filename = input_path.stem
    md_filename = output_dir / f"{doc_filename}-markdroped.md"
    html_filename = output_dir / f"{doc_filename}-markdroped.html"

    markdown = _markdown_from_pymupdf(input_path)
    md_filename.write_text(markdown, encoding="utf-8")

    with fitz.open(input_path) as doc:
        picture_counter = _export_images(doc, images_dir, doc_filename)

    html_filename.write_text(
        _html_from_markdown(markdown, doc_filename),
        encoding="utf-8",
    )

    logger.info("Fast conversion saved markdown and HTML (PyMuPDF only)")

    return DoclingConversionResult(
        doc_filename=doc_filename,
        md_path=md_filename,
        html_path=html_filename,
        conv_res=None,
        tables_dir=tables_dir,
        images_dir=images_dir,
        table_counter=0,
        picture_counter=picture_counter,
    )
