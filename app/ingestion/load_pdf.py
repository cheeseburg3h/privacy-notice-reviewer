from __future__ import annotations

from pathlib import Path
from typing import Any


def extract_pdf_pages(path: str | Path) -> list[dict[str, Any]]:
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("pypdf is required for PDF extraction. Run `pip install pypdf`.") from exc

    reader = PdfReader(str(pdf_path))
    pages: list[dict[str, Any]] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({"page": index, "text": text, "source_location": str(pdf_path)})
    return pages

