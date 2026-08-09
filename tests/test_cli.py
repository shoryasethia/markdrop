# Mock out any delayed litellm or heavy imports during CLI init
import sys
from unittest.mock import MagicMock, patch

import pytest

from markdrop.main import main
from markdrop.parse import AIProvider

sys.modules["litellm"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["openai"] = MagicMock()
sys.modules["anthropic"] = MagicMock()


@patch("markdrop.main.asyncio.run")
@patch("markdrop.main.process_markdown")
def test_describe_cli_overrides(mock_process, mock_run, monkeypatch):
    """Test that the CLI configures ProcessorConfig correctly with model overrides."""
    import sys

    test_args = [
        "markdrop",
        "describe",
        "dummy.md",
        "--ai_provider",
        "openai",
        "--model",
        "gpt-5.4-experimental",
        "--text-model",
        "gpt-5-mini",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    main()

    mock_run.assert_called_once()
    config = mock_process.call_args[0][0]

    assert config.input_path == "dummy.md"
    assert config.ai_provider == AIProvider.OPENAI
    assert config.model_name_override == "gpt-5.4-experimental"
    assert config.text_model_name_override == "gpt-5-mini"

    # Verify the effective model resolution works
    assert config.effective_model() == "gpt-5.4-experimental"
    assert config.effective_text_model() == "gpt-5-mini"


def test_version_flag(capsys, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["markdrop", "--version"],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "markdrop" in captured.out
