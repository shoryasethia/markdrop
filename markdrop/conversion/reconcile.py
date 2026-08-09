from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import pymupdf as fitz

from .types import BlockKind, DocumentBlock


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _overlap_confidence(docling_text: str, pymupdf_text: str) -> float:
    left = _normalize_text(docling_text)
    right = _normalize_text(pymupdf_text)
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.3
    return SequenceMatcher(None, left, right).ratio()


def extract_pymupdf_blocks(input_path: str | Path) -> list[DocumentBlock]:
    blocks: list[DocumentBlock] = []
    with fitz.open(Path(input_path)) as doc:
        for page_num, page in enumerate(doc, start=1):
            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") != 0:
                    continue
                lines = []
                for line in block.get("lines", []):
                    spans = [span.get("text", "") for span in line.get("spans", [])]
                    lines.append("".join(spans))
                text = "\n".join(line for line in lines if line.strip())
                if not text.strip():
                    continue
                bbox = block.get("bbox")
                bbox_tuple = tuple(bbox) if bbox and len(bbox) == 4 else None
                blocks.append(
                    DocumentBlock(
                        kind=BlockKind.PARAGRAPH,
                        text=text,
                        page=page_num,
                        bbox=bbox_tuple,
                        source="pymupdf",
                        confidence=1.0,
                    )
                )
    return blocks


def extract_docling_blocks(conv_res: Any) -> list[DocumentBlock]:
    blocks: list[DocumentBlock] = []
    document = conv_res.document

    for element, _level in document.iterate_items():
        label = getattr(element, "label", None)
        text = getattr(element, "text", "") or ""
        if hasattr(element, "export_to_markdown"):
            try:
                exported = element.export_to_markdown()
                if exported:
                    text = exported
            except Exception:
                pass

        kind = BlockKind.OTHER
        label_name = str(label).lower() if label is not None else ""
        if "title" in label_name or "heading" in label_name or "section" in label_name:
            kind = BlockKind.HEADING
        elif "table" in label_name:
            kind = BlockKind.TABLE
        elif "picture" in label_name or "figure" in label_name or "image" in label_name:
            kind = BlockKind.IMAGE
        elif "list" in label_name:
            kind = BlockKind.LIST_ITEM
        elif "code" in label_name:
            kind = BlockKind.CODE
        elif text.strip():
            kind = BlockKind.PARAGRAPH

        page = getattr(element, "page", None)
        prov = getattr(element, "prov", None)
        if page is None and prov:
            page = getattr(prov[0], "page", None) if prov else None

        blocks.append(
            DocumentBlock(
                kind=kind,
                text=text.strip(),
                page=page,
                source="docling",
                confidence=1.0,
            )
        )

    return blocks


def reconcile_blocks(
    docling_blocks: list[DocumentBlock],
    pymupdf_blocks: list[DocumentBlock],
) -> list[DocumentBlock]:
    pymupdf_by_page: dict[int | None, list[DocumentBlock]] = {}
    for block in pymupdf_blocks:
        pymupdf_by_page.setdefault(block.page, []).append(block)

    reconciled: list[DocumentBlock] = []
    for block in docling_blocks:
        page_blocks = pymupdf_by_page.get(block.page, [])
        if not page_blocks or not block.text.strip():
            reconciled.append(block)
            continue

        best_match = max(
            page_blocks,
            key=lambda candidate: _overlap_confidence(block.text, candidate.text),
        )
        confidence = _overlap_confidence(block.text, best_match.text)
        reconciled.append(
            DocumentBlock(
                kind=block.kind,
                text=block.text,
                page=block.page,
                bbox=best_match.bbox or block.bbox,
                source=block.source,
                confidence=round(confidence, 4),
            )
        )

    return reconciled
