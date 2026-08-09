import socket
from unittest.mock import MagicMock, patch

import pytest

from markdrop.utils import download_pdf, is_safe_url, resolve_safe_url, validate_url_target


def test_is_safe_url_http_https(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda hostname, *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0))
        ],
    )
    assert is_safe_url("https://example.com/file.pdf") is True
    assert is_safe_url("http://example.com/file.pdf") is True
    assert is_safe_url("ftp://example.com/file.pdf") is False
    assert is_safe_url("file:///etc/passwd") is False


def test_is_safe_url_blocks_private_ips(monkeypatch):
    def mock_getaddrinfo(hostname, *args, **kwargs):
        if hostname == "localhost":
            return [(socket.AF_INET, None, None, None, ("127.0.0.1", 0))]
        if hostname == "private.internal":
            return [(socket.AF_INET, None, None, None, ("192.168.1.5", 0))]
        if hostname == "public.com":
            return [(socket.AF_INET, None, None, None, ("8.8.8.8", 0))]
        return [(socket.AF_INET, None, None, None, ("127.0.0.1", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    assert is_safe_url("https://localhost/file.pdf") is False
    assert is_safe_url("http://private.internal/file.pdf") is False
    assert is_safe_url("https://public.com/file.pdf") is True


def test_validate_url_target_rejects_invalid_scheme():
    with pytest.raises(ValueError):
        validate_url_target("file:///etc/passwd")


def test_resolve_safe_url_returns_url(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda hostname, *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0))
        ],
    )
    url = "https://public.com/doc.pdf"
    assert resolve_safe_url(url) == url


def test_download_pdf_rejects_non_pdf_content(monkeypatch, tmp_path):
    response = MagicMock()
    response.status_code = 200
    response.headers = {"content-type": "text/html"}
    response.iter_content.return_value = [b"<html"]
    response.raise_for_status = MagicMock()

    session = MagicMock()
    session.get.return_value = response

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda hostname, *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0))
        ],
    )
    with patch("markdrop.utils.requests.Session", return_value=session):
        with pytest.raises(ValueError, match="not a valid PDF"):
            download_pdf("https://public.com/doc.pdf", tmp_path)


def test_download_pdf_accepts_pdf_magic_bytes(monkeypatch, tmp_path, minimal_pdf_bytes):
    response = MagicMock()
    response.status_code = 200
    response.headers = {"content-type": "application/octet-stream"}
    response.iter_content.return_value = [minimal_pdf_bytes]
    response.raise_for_status = MagicMock()

    session = MagicMock()
    session.get.return_value = response

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda hostname, *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0))
        ],
    )
    with patch("markdrop.utils.requests.Session", return_value=session):
        path = download_pdf("https://public.com/report.pdf", tmp_path)

    assert path is not None
    assert path.endswith(".pdf")
    with open(path, "rb") as handle:
        assert handle.read(4) == b"%PDF"


def test_download_pdf_blocks_redirect_to_private_ip(monkeypatch, tmp_path):
    redirect_response = MagicMock()
    redirect_response.status_code = 302
    redirect_response.headers = {"Location": "https://internal.after-redirect/secret.pdf"}
    redirect_response.close = MagicMock()

    session = MagicMock()
    session.get.return_value = redirect_response

    def mock_getaddrinfo(hostname, *args, **kwargs):
        if hostname == "internal.after-redirect":
            return [(socket.AF_INET, None, None, None, ("10.0.0.1", 0))]
        return [(socket.AF_INET, None, None, None, ("8.8.8.8", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    with patch("markdrop.utils.requests.Session", return_value=session):
        with pytest.raises(ValueError, match="Blocked IP"):
            download_pdf("https://evil.redirect/start.pdf", tmp_path)


def test_download_pdf_follows_safe_redirect(monkeypatch, tmp_path, minimal_pdf_bytes):
    redirect_response = MagicMock()
    redirect_response.status_code = 302
    redirect_response.headers = {"Location": "/final.pdf"}
    redirect_response.close = MagicMock()

    final_response = MagicMock()
    final_response.status_code = 200
    final_response.headers = {"content-type": "application/pdf"}
    final_response.iter_content.return_value = [minimal_pdf_bytes]
    final_response.raise_for_status = MagicMock()

    session = MagicMock()
    session.get.side_effect = [redirect_response, final_response]

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda hostname, *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0))
        ],
    )
    with patch("markdrop.utils.requests.Session", return_value=session):
        path = download_pdf("https://public.com/start.pdf", tmp_path)

    assert path is not None
    assert session.get.call_count == 2


def test_is_remote_path_detects_http_urls():
    from markdrop.utils import is_remote_path

    assert is_remote_path("https://arxiv.org/pdf/1706.03762.pdf")
    assert not is_remote_path("report.pdf")


def test_path_does_not_break_remote_url_detection():
    """Windows Path() mangles URLs; pipeline must check the raw string first."""
    from pathlib import Path

    url = "https://arxiv.org/pdf/1706.03762"
    mangled = str(Path(url))
    assert mangled != url
    from markdrop.utils import is_remote_path

    assert is_remote_path(url)
    assert not is_remote_path(mangled)


def test_processor_config_max_concurrency_default():
    from markdrop.parse import AIProvider, ProcessorConfig

    config = ProcessorConfig(
        input_path="test.md",
        output_dir="out",
        ai_provider=AIProvider.GEMINI,
    )
    assert config.max_concurrency == 8
    assert config.timeout_seconds == 120
