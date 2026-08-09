from __future__ import annotations

import json
import logging
import tempfile
import time
from pathlib import Path
from typing import Any

from ..config import MarkDropConfig
from ..utils import cleanup_download_dir, download_pdf, is_remote_path
from .preflight import analyze_pdf
from .reconcile import extract_docling_blocks, extract_pymupdf_blocks, reconcile_blocks
from .serialize import wrap_docling_markdown, write_markdown_from_blocks
from .types import ConversionResult

logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.5


def _convert_document_fast(
    input_path: str | Path,
    output_dir: str | Path,
    config: MarkDropConfig,
) -> ConversionResult:
    from .fast import convert_with_pymupdf

    input_ref = str(input_path)
    output_dir = Path(output_dir)
    warnings: list[str] = [
        "Fast mode uses PyMuPDF only: no Docling layout, table structure, or ML table detection."
    ]
    timings: dict[str, float] = {}
    download_dir: str | None = None
    local_input: str | Path = input_ref

    try:
        if is_remote_path(input_ref):
            download_dir = tempfile.mkdtemp(prefix="markdrop_pdf_")
            downloaded = download_pdf(input_ref, download_dir)
            if not downloaded:
                raise ValueError(f"Failed to download PDF from {input_ref}")
            local_input = Path(downloaded)
        else:
            local_input = Path(input_ref)

        preflight_start = time.time()
        preflight = analyze_pdf(local_input)
        timings["preflight_seconds"] = round(time.time() - preflight_start, 3)
        warnings.extend(preflight.warnings)

        scanned = sum(1 for p in preflight.page_classifications if p.kind.value == "scanned")
        if scanned:
            warnings.append(
                f"{scanned} page(s) look scanned; fast mode has no OCR — use default mode for those."
            )

        convert_start = time.time()
        fast_result = convert_with_pymupdf(local_input, output_dir)
        timings["pymupdf_seconds"] = round(time.time() - convert_start, 3)

        pymupdf_blocks = extract_pymupdf_blocks(local_input)

        manifest = {
            "input_path": input_ref,
            "mode": "fast",
            "output_dir": str(output_dir.resolve()),
            "markdown_path": str(fast_result.md_path.resolve()),
            "html_path": str(fast_result.html_path.resolve()),
            "timings": timings,
            "warnings": warnings,
            "page_classifications": [
                {
                    "page": item.page,
                    "kind": item.kind.value,
                    "text_coverage": item.text_coverage,
                }
                for item in preflight.page_classifications
            ],
            "blocks": [
                {
                    "kind": block.kind.value,
                    "page": block.page,
                    "source": block.source,
                    "confidence": block.confidence,
                    "text_preview": block.text[:120],
                }
                for block in pymupdf_blocks[:200]
            ],
            "stats": {
                "total_pages": preflight.total_pages,
                "pymupdf_blocks": len(pymupdf_blocks),
                "tables_exported": 0,
                "pictures_exported": fast_result.picture_counter,
            },
        }

        manifest_path = output_dir / "manifest.json"
        _write_manifest(manifest_path, manifest)
        logger.info("Wrote conversion manifest to %s", manifest_path)

        return ConversionResult(
            markdown_path=fast_result.md_path,
            html_path=fast_result.html_path,
            assets_dir=output_dir,
            manifest=manifest,
            warnings=warnings,
        )
    finally:
        if download_dir:
            cleanup_download_dir(download_dir, verbose=False)


def _write_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")


def convert_document(
    input_path: str | Path,
    output_dir: str | Path,
    config: MarkDropConfig | None = None,
) -> ConversionResult:
    if config is None:
        config = MarkDropConfig()

    if config.fast:
        return _convert_document_fast(input_path, output_dir, config)

    from markdrop.process import _convert_with_docling

    input_ref = str(input_path)
    output_dir = Path(output_dir)
    warnings: list[str] = []
    timings: dict[str, float] = {}
    download_dir: str | None = None
    local_input: str | Path = input_ref

    try:
        if is_remote_path(input_ref):
            download_dir = tempfile.mkdtemp(prefix="markdrop_pdf_")
            downloaded = download_pdf(input_ref, download_dir)
            if not downloaded:
                raise ValueError(f"Failed to download PDF from {input_ref}")
            local_input = Path(downloaded)
        else:
            local_input = Path(input_ref)

        preflight_start = time.time()
        preflight = analyze_pdf(local_input)
        timings["preflight_seconds"] = round(time.time() - preflight_start, 3)
        warnings.extend(preflight.warnings)

        docling_start = time.time()
        docling_result = _convert_with_docling(str(local_input), output_dir, config)
        timings["docling_seconds"] = round(time.time() - docling_start, 3)

        reconcile_start = time.time()
        pymupdf_blocks = extract_pymupdf_blocks(local_input)
        docling_blocks = extract_docling_blocks(docling_result.conv_res)
        reconciled_blocks = reconcile_blocks(docling_blocks, pymupdf_blocks)
        timings["reconcile_seconds"] = round(time.time() - reconcile_start, 3)

        low_confidence = [b for b in reconciled_blocks if b.confidence < LOW_CONFIDENCE_THRESHOLD]
        if low_confidence:
            warnings.append(f"{len(low_confidence)} block(s) have low pymupdf text agreement.")

        assets_dir = output_dir
        serialize_start = time.time()
        if reconciled_blocks and all(
            b.confidence >= LOW_CONFIDENCE_THRESHOLD for b in reconciled_blocks
        ):
            markdown_path = write_markdown_from_blocks(
                reconciled_blocks,
                docling_result.md_path,
            )
        else:
            markdown_path = wrap_docling_markdown(
                docling_result.md_path,
                assets_dir=assets_dir,
            )
        timings["serialize_seconds"] = round(time.time() - serialize_start, 3)

        manifest = {
            "input_path": input_ref,
            "mode": "default",
            "output_dir": str(output_dir.resolve()),
            "markdown_path": str(markdown_path.resolve()),
            "html_path": str(docling_result.html_path.resolve()),
            "timings": timings,
            "warnings": warnings,
            "page_classifications": [
                {
                    "page": item.page,
                    "kind": item.kind.value,
                    "text_coverage": item.text_coverage,
                }
                for item in preflight.page_classifications
            ],
            "blocks": [
                {
                    "kind": block.kind.value,
                    "page": block.page,
                    "source": block.source,
                    "confidence": block.confidence,
                    "text_preview": block.text[:120],
                }
                for block in reconciled_blocks
            ],
            "stats": {
                "total_pages": preflight.total_pages,
                "docling_blocks": len(docling_blocks),
                "pymupdf_blocks": len(pymupdf_blocks),
                "reconciled_blocks": len(reconciled_blocks),
                "tables_exported": docling_result.table_counter,
                "pictures_exported": docling_result.picture_counter,
            },
        }

        manifest_path = output_dir / "manifest.json"
        _write_manifest(manifest_path, manifest)
        logger.info("Wrote conversion manifest to %s", manifest_path)

        return ConversionResult(
            markdown_path=markdown_path,
            html_path=docling_result.html_path,
            assets_dir=assets_dir,
            manifest=manifest,
            warnings=warnings,
        )
    finally:
        if download_dir:
            cleanup_download_dir(download_dir, verbose=False)
