"""Shared paths for markdrop user configuration."""

import os
from pathlib import Path

# Canonical Gemini key (written by `markdrop setup gemini`). GOOGLE_API_KEY is the
# Google SDK convention and is accepted as a backward-compatible fallback (#8).
_GEMINI_KEY_NAMES = ("GEMINI_API_KEY", "GOOGLE_API_KEY")


def get_config_dir() -> Path:
    """Return the user config directory for markdrop."""
    try:
        import platformdirs

        return Path(platformdirs.user_config_dir("markdrop"))
    except ImportError:
        return Path.home() / ".config" / "markdrop"


def get_env_file_path() -> Path:
    """Return the path to the markdrop .env file."""
    return get_config_dir() / ".env"


def load_markdrop_env() -> Path | None:
    """Load API keys from the user config .env file if it exists."""
    from dotenv import load_dotenv

    env_file = get_env_file_path()
    if env_file.exists():
        load_dotenv(env_file)
        return env_file
    return None


def get_gemini_api_key(*, load_env: bool = True) -> str | None:
    """Return the Gemini API key from the environment.

    Checks ``GEMINI_API_KEY`` first, then ``GOOGLE_API_KEY`` for compatibility
    with Google's SDK and existing deployments.
    """
    if load_env:
        load_markdrop_env()
    for name in _GEMINI_KEY_NAMES:
        value = os.getenv(name)
        if value:
            return value
    return None
