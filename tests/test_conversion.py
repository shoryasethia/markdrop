import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from markdrop.config import MarkDropConfig
from markdrop.conversion.pipeline import convert_document
from markdrop.conversion.preflight import analyze_pdf
from markdrop.conversion.types import (
    BlockKind,
    DoclingConversionResult,
    DocumentBlock,
    PageKind,
)


def _make_pymupdf_page(text_coverage: float, has_images: bool = False):
    page = MagicMock()
    page.rect.width = 100.0
    page.rect.height = 100.0
    page.get_images.return_value = [(1,)] if has_images else []

    text_area = text_coverage * 10000
    side = text_area**0.5
    blocks = []
    if text_coverage > 0:
        blocks.append(
            {
                "type": 0,
                "lines": [
                    {
                        "spans": [
                            {
                                "text": "sample text",
                                "bbox": (0, 0, side, side),
                            }
                        ]
                    }
                ],
            }
        )
    if has_images:
        blocks.append({"type": 1, "xref": 42})

    page.get_text.return_value = {"blocks": blocks}
    return page


def _make_pymupdf_doc(pages: list):
    doc = MagicMock()
    doc.__enter__.return_value = doc
    doc.__exit__.return_value = False
    doc.__iter__.return_value = iter(pages)
    return doc


@patch("markdrop.conversion.preflight.fitz.open")
def test_preflight_classifies_digital_page(mock_open):
    page = _make_pymupdf_page(text_coverage=0.2, has_images=False)
    mock_open.return_value = _make_pymupdf_doc([page])

    result = analyze_pdf("sample.pdf")

    assert result.total_pages == 1
    assert result.page_classifications[0].kind == PageKind.DIGITAL
    assert result.page_classifications[0].text_coverage > 0


@patch("markdrop.conversion.preflight.fitz.open")
def test_preflight_classifies_scanned_page(mock_open):
    page = _make_pymupdf_page(text_coverage=0.0, has_images=True)
    mock_open.return_value = _make_pymupdf_doc([page])

    result = analyze_pdf("sample.pdf")

    assert result.page_classifications[0].kind == PageKind.SCANNED
    assert any("scanned" in warning.lower() for warning in result.warnings)


@patch("markdrop.conversion.preflight.fitz.open")
def test_preflight_classifies_mixed_page(mock_open):
    page = _make_pymupdf_page(text_coverage=0.02, has_images=True)
    mock_open.return_value = _make_pymupdf_doc([page])

    result = analyze_pdf("sample.pdf")

    assert result.page_classifications[0].kind == PageKind.MIXED


@patch("markdrop.conversion.pipeline._write_manifest")
@patch("markdrop.conversion.pipeline.extract_pymupdf_blocks")
@patch("markdrop.conversion.pipeline.extract_docling_blocks")
@patch("markdrop.conversion.pipeline.analyze_pdf")
@patch("markdrop.process._convert_with_docling")
def test_convert_document_writes_manifest(
    mock_docling,
    mock_preflight,
    mock_docling_blocks,
    mock_pymupdf_blocks,
    mock_write_manifest,
    tmp_path,
):
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    md_path = output_dir / "doc-markdroped.md"
    html_path = output_dir / "doc-markdroped.html"
    md_path.write_text("# Title\n\nBody\n", encoding="utf-8")
    html_path.write_text("<html></html>", encoding="utf-8")

    mock_docling.return_value = DoclingConversionResult(
        doc_filename="doc",
        md_path=md_path,
        html_path=html_path,
        conv_res=MagicMock(),
        tables_dir=output_dir / "tables",
        images_dir=output_dir / "images",
        table_counter=1,
        picture_counter=2,
    )

    from markdrop.conversion.types import PageClassification, PreflightResult

    mock_preflight.return_value = PreflightResult(
        page_classifications=[
            PageClassification(page=1, kind=PageKind.DIGITAL, text_coverage=0.25)
        ],
        total_pages=1,
        warnings=[],
    )
    mock_docling_blocks.return_value = [
        DocumentBlock(kind=BlockKind.PARAGRAPH, text="Body", page=1, confidence=1.0)
    ]
    mock_pymupdf_blocks.return_value = [
        DocumentBlock(
            kind=BlockKind.PARAGRAPH,
            text="Body",
            page=1,
            source="pymupdf",
            confidence=1.0,
        )
    ]

    result = convert_document("sample.pdf", output_dir, MarkDropConfig())

    assert result.markdown_path == md_path
    assert result.html_path == html_path
    assert result.manifest["stats"]["tables_exported"] == 1
    assert result.manifest["page_classifications"][0]["kind"] == "digital"
    mock_write_manifest.assert_called_once()

    manifest_path, manifest = mock_write_manifest.call_args[0]
    assert manifest_path == output_dir / "manifest.json"
    assert manifest["timings"]["docling_seconds"] >= 0


@patch("markdrop.conversion.pipeline._write_manifest")
@patch("markdrop.conversion.pipeline.extract_pymupdf_blocks", return_value=[])
@patch("markdrop.conversion.pipeline.extract_docling_blocks", return_value=[])
@patch("markdrop.conversion.pipeline.analyze_pdf")
@patch("markdrop.process._convert_with_docling")
def test_manifest_json_roundtrip(
    mock_docling,
    mock_preflight,
    _mock_docling_blocks,
    _mock_pymupdf_blocks,
    mock_write_manifest,
    tmp_path,
):
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    md_path = output_dir / "paper-markdroped.md"
    html_path = output_dir / "paper-markdroped.html"
    md_path.write_text("# Paper\n", encoding="utf-8")
    html_path.write_text("<html></html>", encoding="utf-8")

    mock_docling.return_value = DoclingConversionResult(
        doc_filename="paper",
        md_path=md_path,
        html_path=html_path,
        conv_res=MagicMock(),
        tables_dir=output_dir / "tables",
        images_dir=output_dir / "images",
        table_counter=0,
        picture_counter=0,
    )

    from markdrop.conversion.types import PreflightResult

    mock_preflight.return_value = PreflightResult(
        page_classifications=[],
        total_pages=0,
        warnings=["test warning"],
    )

    def write_manifest(path: Path, manifest: dict):
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    mock_write_manifest.side_effect = write_manifest

    convert_document("paper.pdf", output_dir)

    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["warnings"] == ["test warning"]
    assert manifest["markdown_path"].endswith("paper-markdroped.md")


@patch("markdrop.conversion.pipeline._write_manifest")
@patch("markdrop.conversion.fast.convert_with_pymupdf")
@patch("markdrop.conversion.pipeline.extract_pymupdf_blocks")
@patch("markdrop.conversion.pipeline.analyze_pdf")
def test_convert_document_fast_mode(
    mock_preflight,
    mock_pymupdf_blocks,
    mock_fast,
    mock_write_manifest,
    tmp_path,
):
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    md_path = output_dir / "doc-markdroped.md"
    html_path = output_dir / "doc-markdroped.html"
    md_path.write_text("# Fast\n", encoding="utf-8")
    html_path.write_text("<html></html>", encoding="utf-8")

    mock_fast.return_value = DoclingConversionResult(
        doc_filename="doc",
        md_path=md_path,
        html_path=html_path,
        conv_res=None,
        tables_dir=output_dir / "tables",
        images_dir=output_dir / "images",
        table_counter=0,
        picture_counter=1,
    )

    from markdrop.conversion.types import PageClassification, PageKind, PreflightResult

    mock_preflight.return_value = PreflightResult(
        page_classifications=[
            PageClassification(page=1, kind=PageKind.DIGITAL, text_coverage=0.3)
        ],
        total_pages=1,
        warnings=[],
    )
    mock_pymupdf_blocks.return_value = [
        DocumentBlock(
            kind=BlockKind.PARAGRAPH,
            text="Fast body",
            page=1,
            source="pymupdf",
            confidence=1.0,
        )
    ]

    result = convert_document("doc.pdf", output_dir, MarkDropConfig(fast=True))

    assert result.markdown_path == md_path
    mock_fast.assert_called_once()
    mock_write_manifest.assert_called_once()
    _, manifest = mock_write_manifest.call_args[0]
    assert manifest["mode"] == "fast"
    assert manifest["stats"]["tables_exported"] == 0
    assert "pymupdf_seconds" in manifest["timings"]
