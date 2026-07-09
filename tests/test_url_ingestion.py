from __future__ import annotations

from app.ingestion.load_html import html_to_text
from app.ingestion.load_url import is_url, looks_like_pdf
from app.ingestion.segment_notice import _title_from_source


def test_url_detection_and_title() -> None:
    assert is_url("https://example.com/privacy-policy")
    assert not is_url("data/client_inputs/client/privacy_notice.pdf")
    assert _title_from_source("https://example.com/legal/privacy-policy") == "Privacy Policy"


def test_html_to_text_strips_active_content() -> None:
    text = html_to_text("<html><script>alert(1)</script><h1>Privacy</h1><p>We process data.</p></html>")
    assert "alert" not in text
    assert "Privacy" in text
    assert "We process data." in text


def test_pdf_url_detection() -> None:
    assert looks_like_pdf("https://example.com/privacy.pdf", "application/octet-stream", b"")
    assert looks_like_pdf("https://example.com/privacy", "application/pdf", b"")
    assert looks_like_pdf("https://example.com/privacy", "text/html", b"%PDF-1.7")

