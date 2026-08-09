import os

import pytest

from markdrop.config_paths import get_gemini_api_key


def test_get_gemini_api_key_prefers_gemini(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")

    assert get_gemini_api_key(load_env=False) == "gemini-key"


def test_get_gemini_api_key_falls_back_to_google(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")

    assert get_gemini_api_key(load_env=False) == "google-key"


def test_get_gemini_api_key_returns_none_when_missing(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    assert get_gemini_api_key(load_env=False) is None
