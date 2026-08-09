from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class BlockKind(Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    IMAGE = "image"
    LIST_ITEM = "list_item"
    CODE = "code"
    OTHER = "other"


class PageKind(str, Enum):
    DIGITAL = "digital"
    SCANNED = "scanned"
    MIXED = "mixed"


@dataclass
class DocumentBlock:
    kind: BlockKind
    text: str
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    source: str = "docling"
    confidence: float = 1.0


@dataclass
class PageClassification:
    page: int
    kind: PageKind
    text_coverage: float


@dataclass
class PreflightResult:
    page_classifications: list[PageClassification]
    total_pages: int
    warnings: list[str] = field(default_factory=list)


@dataclass
class DoclingConversionResult:
    doc_filename: str
    md_path: Path
    html_path: Path
    conv_res: object
    tables_dir: Path
    images_dir: Path
    table_counter: int
    picture_counter: int


@dataclass
class ConversionResult:
    markdown_path: Path
    html_path: Path
    assets_dir: Path
    manifest: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
