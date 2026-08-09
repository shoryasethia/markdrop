"""Shared pytest fixtures for Markdrop."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def minimal_pdf_bytes() -> bytes:
    """Smallest valid PDF with one empty page."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 200 200]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000052 00000 n \n"
        b"0000000101 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n178\n%%EOF\n"
    )


@pytest.fixture
def minimal_pdf_path(tmp_path: Path, minimal_pdf_bytes: bytes) -> Path:
    path = tmp_path / "sample.pdf"
    path.write_bytes(minimal_pdf_bytes)
    return path


@pytest.fixture
def text_pdf_path(tmp_path: Path) -> Path:
    """PDF with extractable text when PyMuPDF is available."""
    try:
        import pymupdf as fitz
    except ImportError:
        pytest.skip("pymupdf not installed")

    path = tmp_path / "text.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Markdrop fixture paragraph.")
    doc.save(path)
    doc.close()
    return path
