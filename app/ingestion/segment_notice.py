from __future__ import annotations

import argparse
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.ingestion.clean_text import compact_for_excerpt, is_heading, normalize_text, split_paragraphs
from app.ingestion.load_html import html_to_text, load_html_text
from app.ingestion.load_pdf import extract_pdf_pages
from app.ingestion.load_url import fetch_url, is_url, looks_like_pdf
from app.io_utils import write_jsonl


def _source_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".html", ".htm"}:
        return "html"
    return "text"


def _title_from_source(source: str | Path) -> str:
    source_text = str(source)
    if is_url(source_text):
        parsed_path = source_text.rstrip("/").split("/")[-1] or "privacy notice"
        return parsed_path.replace("_", " ").replace("-", " ").replace(".html", "").replace(".htm", "").title()
    source_path = Path(source)
    return source_path.stem.replace("_", " ").replace("-", " ").title()


def _chunks_from_page(
    company: str,
    title: str,
    source_location: str,
    page_number: int | None,
    text: str,
    retrieval_timestamp: str,
    source_type: str,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current_heading = title
    paragraphs = split_paragraphs(normalize_text(text))
    counter = 1
    for paragraph in paragraphs:
        first_line = paragraph.splitlines()[0] if paragraph.splitlines() else paragraph
        if is_heading(first_line) and len(paragraph) < 180:
            current_heading = first_line.strip()
            continue
        if paragraph.strip().lower().startswith("from <"):
            continue
        if len(paragraph.strip()) < 20:
            continue
        source_id = f"NOTICE-{company.upper()}-P{page_number or 0}-C{counter:03d}"
        chunks.append(
            {
                "source_id": source_id,
                "company": company,
                "document_title": title,
                "source_type": source_type,
                "source_location": source_location,
                "retrieval_timestamp": retrieval_timestamp,
                "heading": current_heading,
                "paragraph_number": counter,
                "page": page_number,
                "text": paragraph.strip(),
                "excerpt": compact_for_excerpt(paragraph.strip(), 900),
            }
        )
        counter += 1
    return chunks


def segment_notice(
    company: str,
    source: str | Path,
    title: str | None = None,
    retrieval_timestamp: str | None = None,
) -> list[dict[str, Any]]:
    timestamp = retrieval_timestamp or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    document_title = title or _title_from_source(source)

    chunks: list[dict[str, Any]] = []
    if is_url(str(source)):
        fetched = fetch_url(str(source))
        if looks_like_pdf(fetched.url, fetched.content_type, fetched.body):
            temp_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as handle:
                    handle.write(fetched.body)
                    temp_path = Path(handle.name)
                for page in extract_pdf_pages(temp_path):
                    chunks.extend(
                        _chunks_from_page(
                            company=company,
                            title=document_title,
                            source_location=fetched.url,
                            page_number=int(page["page"]),
                            text=page["text"],
                            retrieval_timestamp=timestamp,
                            source_type="url_pdf",
                        )
                    )
            finally:
                if temp_path and temp_path.exists():
                    temp_path.unlink()
        else:
            encoding = "utf-8"
            text = html_to_text(fetched.body.decode(encoding, errors="ignore"))
            chunks.extend(
                _chunks_from_page(
                    company=company,
                    title=document_title,
                    source_location=fetched.url,
                    page_number=None,
                    text=text,
                    retrieval_timestamp=timestamp,
                    source_type="url",
                )
            )
        return chunks

    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    source_kind = _source_type(source_path)

    if source_kind == "pdf":
        for page in extract_pdf_pages(source_path):
            chunks.extend(
                _chunks_from_page(
                    company=company,
                    title=document_title,
                    source_location=str(source_path),
                    page_number=int(page["page"]),
                    text=page["text"],
                    retrieval_timestamp=timestamp,
                    source_type="pdf",
                )
            )
    elif source_kind == "html":
        text = load_html_text(source_path)
        chunks.extend(
            _chunks_from_page(
                company=company,
                title=document_title,
                source_location=str(source_path),
                page_number=None,
                text=text,
                retrieval_timestamp=timestamp,
                source_type="html",
            )
        )
    else:
        text = source_path.read_text(encoding="utf-8", errors="ignore")
        chunks.extend(
            _chunks_from_page(
                company=company,
                title=document_title,
                source_location=str(source_path),
                page_number=None,
                text=text,
                retrieval_timestamp=timestamp,
                source_type="text",
            )
        )
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Segment a company privacy notice into evidence chunks.")
    parser.add_argument("--company", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--title")
    parser.add_argument("--retrieval-timestamp")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    chunks = segment_notice(
        company=args.company,
        source=args.source,
        title=args.title,
        retrieval_timestamp=args.retrieval_timestamp,
    )
    write_jsonl(args.output, chunks)
    print(f"Wrote {len(chunks)} notice chunks to {args.output}")


if __name__ == "__main__":
    main()
