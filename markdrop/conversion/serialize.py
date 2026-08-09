from __future__ import annotations

import re
from pathlib import Path

from .types import BlockKind, DocumentBlock


def _block_to_markdown(block: DocumentBlock) -> str:
    text = block.text.strip()
    if not text:
        return ""

    if block.kind == BlockKind.HEADING:
        return f"## {text}"
    if block.kind == BlockKind.LIST_ITEM:
        return f"- {text}"
    if block.kind == BlockKind.CODE:
        return f"```\n{text}\n```"
    if block.kind == BlockKind.IMAGE:
        return text if text.startswith("!") else f"![image]({text})"
    if block.kind == BlockKind.TABLE:
        return text

    return text


def write_markdown_from_blocks(blocks: list[DocumentBlock], output_path: Path) -> Path:
    lines: list[str] = []
    for block in blocks:
        rendered = _block_to_markdown(block)
        if rendered:
            lines.append(rendered)
            lines.append("")

    content = "\n".join(lines).rstrip() + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def normalize_asset_paths(content: str, assets_dir: Path) -> str:
    assets_name = assets_dir.name

    def _replace(match: re.Match[str]) -> str:
        prefix = match.group(1)
        path = match.group(2)
        normalized = path.replace("\\", "/")
        for candidate in ("./images/", "./tables/", "images/", "tables/"):
            if normalized.startswith(candidate):
                subpath = normalized[len(candidate) :]
                folder = candidate.rstrip("/").lstrip("./")
                return f"{prefix}{assets_name}/{folder}/{subpath}"
        return match.group(0)

    pattern = re.compile(r"(!\[[^\]]*\]\()([^)]+)(\))")
    return pattern.sub(lambda m: _replace(m) + m.group(3), content)


def wrap_docling_markdown(
    md_path: Path,
    output_path: Path | None = None,
    assets_dir: Path | None = None,
) -> Path:
    target = output_path or md_path
    content = md_path.read_text(encoding="utf-8")

    if assets_dir is not None:
        content = normalize_asset_paths(content, assets_dir)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target
