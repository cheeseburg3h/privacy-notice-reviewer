from __future__ import annotations

from dataclasses import dataclass
from socket import timeout as SocketTimeout
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


@dataclass(frozen=True)
class UrlFetchResult:
    url: str
    content_type: str
    body: bytes


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def fetch_url(url: str, timeout_seconds: int = 30, max_bytes: int = 15_000_000) -> UrlFetchResult:
    if not is_url(url):
        raise ValueError(f"Unsupported URL: {url}")

    request = Request(
        url,
        headers={
            "User-Agent": "PrivacyNoticeReviewer/1.0 (+https://github.com/cheeseburg3h/privacy-notice-reviewer)",
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
        },
    )
    try:
        # Review URLs are user-supplied inputs for this ingestion command.
        with urlopen(request, timeout=timeout_seconds) as response:  # nosec B310
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            body = response.read(max_bytes + 1)
    except HTTPError as exc:
        raise RuntimeError(
            f"Could not fetch URL {url}: HTTP {exc.code}. Upload a PDF/HTML export if the site blocks automated access."
        ) from exc
    except (URLError, SocketTimeout, TimeoutError) as exc:
        raise RuntimeError(
            f"Could not fetch URL {url}: {exc}. Upload a PDF/HTML export or use a browser-rendered capture for dynamic sites."
        ) from exc
    if len(body) > max_bytes:
        raise RuntimeError(f"URL response exceeds maximum supported size of {max_bytes} bytes.")
    return UrlFetchResult(url=url, content_type=content_type, body=body)


def looks_like_pdf(url: str, content_type: str, body: bytes) -> bool:
    return content_type == "application/pdf" or urlparse(url).path.lower().endswith(".pdf") or body.startswith(b"%PDF")
