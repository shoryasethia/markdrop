import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from markdrop.parse import AIProvider, ProcessorConfig, process_markdown


def test_processor_config_defaults():
    config = ProcessorConfig(
        input_path="test.md",
        output_dir="out",
        ai_provider=AIProvider.ANTHROPIC,
    )

    assert config.effective_model() == "claude-opus-5"
    assert config.effective_text_model() == "claude-sonnet-5"
    assert config.max_concurrency == 8
    assert config.timeout_seconds == 120


def test_processor_config_overrides():
    config = ProcessorConfig(
        input_path="test.md",
        output_dir="out",
        ai_provider=AIProvider.ANTHROPIC,
        model_name_override="custom-vision-model",
        text_model_name_override="custom-text-model",
        max_concurrency=3,
        timeout_seconds=60,
    )

    assert config.effective_model() == "custom-vision-model"
    assert config.effective_text_model() == "custom-text-model"
    assert config.max_concurrency == 3
    assert config.timeout_seconds == 60


def test_litellm_table_uses_effective_text_model():
    config = ProcessorConfig(
        input_path="test.md",
        output_dir="out",
        ai_provider=AIProvider.LITELLM,
        text_model_name_override="anthropic/claude-sonnet-5",
    )
    assert config.effective_text_model() == "anthropic/claude-sonnet-5"


def test_path_containment_blocks_sibling_directory(tmp_path):
    root = tmp_path / "doc"
    root.mkdir()
    outside = tmp_path / "doc-evil"
    outside.mkdir()
    secret = outside / "secret.png"
    secret.write_bytes(b"secret")

    malicious_ref = "../doc-evil/secret.png"
    resolved_root = root.resolve()
    resolved_target = (resolved_root / malicious_ref).resolve()

    with pytest.raises(ValueError):
        resolved_target.relative_to(resolved_root)


@pytest.mark.asyncio
async def test_path_containment_blocks_traversal_in_process_markdown(tmp_path):
    doc_dir = tmp_path / "doc"
    doc_dir.mkdir()
    outside = tmp_path / "secret.png"
    outside.write_bytes(b"png")

    md_path = doc_dir / "readme.md"
    md_path.write_text("![alt](../secret.png)\n", encoding="utf-8")

    config = ProcessorConfig(
        input_path=str(md_path),
        output_dir=str(tmp_path / "out"),
        ai_provider=AIProvider.OPENAI,
        image_descriptions=True,
        table_descriptions=False,
        max_concurrency=2,
    )

    mock_processor = MagicMock()
    mock_processor.process_image = AsyncMock()

    with patch("markdrop.parse.AIProcessor", return_value=mock_processor):
        processed = await process_markdown(config)

    content = processed.read_text(encoding="utf-8")
    assert "path outside document directory" in content
    mock_processor.process_image.assert_not_called()


@pytest.mark.asyncio
async def test_max_concurrency_limits_parallel_tasks(tmp_path):
    doc_dir = tmp_path / "doc"
    doc_dir.mkdir()
    images_dir = doc_dir / "images"
    images_dir.mkdir()

    for idx in range(4):
        (images_dir / f"img{idx}.png").write_bytes(b"png")

    md_lines = [f"![alt](images/img{i}.png)" for i in range(4)]
    md_path = doc_dir / "readme.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    active = 0
    peak = 0

    async def slow_process_image(_path):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.05)
        active -= 1
        return "description"

    mock_processor = MagicMock()
    mock_processor.process_image = AsyncMock(side_effect=slow_process_image)
    mock_processor.process_table = AsyncMock()

    config = ProcessorConfig(
        input_path=str(md_path),
        output_dir=str(tmp_path / "out"),
        ai_provider=AIProvider.OPENAI,
        image_descriptions=True,
        table_descriptions=False,
        max_concurrency=2,
    )

    with patch("markdrop.parse.AIProcessor", return_value=mock_processor):
        await process_markdown(config)

    assert peak <= 2
    assert mock_processor.process_image.call_count == 4
