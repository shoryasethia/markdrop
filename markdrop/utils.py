import ipaddress
import logging
import os
import re
import socket
import urllib.parse
import urllib.request
from contextlib import suppress

import requests
from tqdm import tqdm

logger = logging.getLogger("markdrop.utils")

MAX_REDIRECTS = 5
MAX_PDF_BYTES = 200 * 1024 * 1024
DOWNLOAD_TIMEOUT = 30
PDF_MAGIC = b"%PDF"


def _is_blocked_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _hostname_blocked(hostname: str | None) -> bool:
    if not hostname:
        return True
    host = hostname.strip().lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"}:
        return True
    if host.endswith(".local") or host.endswith(".internal"):
        return True
    return False


def _resolve_host_ips(hostname: str) -> list[str]:
    ips: list[str] = []
    for family, _, _, _, sockaddr in socket.getaddrinfo(hostname, None):
        if family == socket.AF_INET:
            ips.append(sockaddr[0])
        elif family == socket.AF_INET6:
            ips.append(sockaddr[0])
    return ips


def validate_url_target(url: str) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    if _hostname_blocked(parsed.hostname):
        raise ValueError(f"Blocked hostname: {parsed.hostname}")
    for ip in _resolve_host_ips(parsed.hostname):
        if _is_blocked_ip(ip):
            raise ValueError(f"Blocked IP address for {parsed.hostname}: {ip}")
    return parsed


def is_safe_url(url: str) -> bool:
    try:
        validate_url_target(url)
        return True
    except Exception:
        return False


def resolve_safe_url(url: str) -> str:
    validate_url_target(url)
    return url


def _sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w.\-]+", "_", name).strip("._")
    return cleaned or "download.pdf"


def _looks_like_pdf(content: bytes) -> bool:
    return content.startswith(PDF_MAGIC)


def download_pdf(url: str, download_dir: str | os.PathLike) -> str | None:
    """Download PDF from a URL with redirect validation, size limits, and magic-byte checks."""
    current = resolve_safe_url(url)
    session = requests.Session()

    for _ in range(MAX_REDIRECTS + 1):
        response = session.get(
            current,
            stream=True,
            timeout=DOWNLOAD_TIMEOUT,
            allow_redirects=False,
        )

        if response.status_code in {301, 302, 303, 307, 308}:
            location = response.headers.get("Location")
            if not location:
                raise ValueError("Redirect response missing Location header")
            current = urllib.parse.urljoin(current, location)
            validate_url_target(current)
            continue

        response.raise_for_status()
        break
    else:
        raise ValueError(f"Too many redirects while downloading: {url}")

    parsed = urllib.parse.urlparse(current)
    filename = _sanitize_filename(os.path.basename(parsed.path) or "download.pdf")
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    os.makedirs(download_dir, exist_ok=True)
    file_path = os.path.join(download_dir, filename)

    downloaded = 0
    first_chunk = b""
    content_type = (response.headers.get("content-type") or "").lower()
    if content_type and "pdf" not in content_type and "octet-stream" not in content_type:
        logger.warning("Unexpected content-type %s for %s", content_type, current)

    with (
        open(file_path, "wb") as handle,
        tqdm(
            desc=f"Downloading {filename}",
            total=int(response.headers.get("content-length", 0)) or None,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar,
    ):
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            if not first_chunk:
                first_chunk = chunk[:8]
            downloaded += len(chunk)
            if downloaded > MAX_PDF_BYTES:
                raise ValueError(
                    f"Download aborted: exceeded {MAX_PDF_BYTES // (1024 * 1024)} MB size limit"
                )
            handle.write(chunk)
            bar.update(len(chunk))

    if not _looks_like_pdf(first_chunk):
        with suppress(OSError):
            os.remove(file_path)
        raise ValueError("Downloaded file is not a valid PDF")

    logger.info("Successfully downloaded PDF to %s", file_path)
    return file_path


def cleanup_download_dir(download_dir: str | os.PathLike, verbose: bool = False) -> None:
    """Clean up downloaded PDF files."""
    try:
        for filename in os.listdir(download_dir):
            file_path = os.path.join(download_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                if verbose:
                    logger.info("Removed temporary file: %s", file_path)
        os.rmdir(download_dir)
        if verbose:
            logger.info("Removed temporary directory: %s", download_dir)
    except Exception as exc:
        logger.error("Error cleaning up download directory: %s", exc)


def is_remote_path(path: str) -> bool:
    return path.startswith(("http://", "https://"))
