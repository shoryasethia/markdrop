from __future__ import annotations

from pathlib import Path

import pymupdf as fitz

from .types import PageClassification, PageKind, PreflightResult

DIGITAL_COVERAGE_THRESHOLD = 0.05
SCANNED_COVERAGE_THRESHOLD = 0.01


def _page_text_coverage(page: fitz.Page) -> float:
    page_area = page.rect.width * page.rect.height
    if page_area <= 0:
        return 0.0

    text_area = 0.0
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                bbox = span.get("bbox", (0, 0, 0, 0))
                text_area += (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])

    return min(text_area / page_area, 1.0)


def _page_has_images(page: fitz.Page) -> bool:
    blocks = page.get_text("dict").get("blocks", [])
    if any(block.get("type") == 1 for block in blocks):
        return True
    return bool(page.get_images())


def _classify_page(page: fitz.Page, page_num: int) -> PageClassification:
    coverage = _page_text_coverage(page)
    has_images = _page_has_images(page)

    if coverage < SCANNED_COVERAGE_THRESHOLD:
        kind = PageKind.SCANNED
    elif has_images and coverage < DIGITAL_COVERAGE_THRESHOLD:
        kind = PageKind.MIXED
    else:
        kind = PageKind.DIGITAL

    return PageClassification(page=page_num, kind=kind, text_coverage=round(coverage, 4))


def analyze_pdf(input_path: str | Path) -> PreflightResult:
    path = Path(input_path)
    warnings: list[str] = []
    classifications: list[PageClassification] = []

    with fitz.open(path) as doc:
        for page_num, page in enumerate(doc, start=1):
            classifications.append(_classify_page(page, page_num))

    scanned_pages = sum(1 for c in classifications if c.kind == PageKind.SCANNED)
    if scanned_pages == len(classifications) and classifications:
        warnings.append("All pages appear scanned; OCR quality may vary.")

    return PreflightResult(
        page_classifications=classifications,
        total_pages=len(classifications),
        warnings=warnings,
    )
