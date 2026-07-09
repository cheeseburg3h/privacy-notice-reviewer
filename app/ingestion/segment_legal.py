from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from app.config import DEFAULT_EFFECTIVE_DATE
from app.ingestion.clean_text import compact_for_excerpt, normalize_legal_ocr
from app.ingestion.load_pdf import extract_pdf_pages
from app.io_utils import write_jsonl

ARTICLE_RE = re.compile(r"\bPasal\s+([0-9]+|[IVXLCDM]+)\b", re.IGNORECASE)


def _roman_to_int(value: str) -> int | None:
    value = value.upper()
    if value.isdigit():
        return int(value)
    numerals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    previous = 0
    for char in reversed(value):
        number = numerals.get(char)
        if number is None:
            return None
        if number < previous:
            total -= number
        else:
            total += number
            previous = number
    return total or None


def _page_for_offset(markers: list[tuple[int, int]], offset: int) -> int | None:
    page = None
    for marker_offset, marker_page in markers:
        if marker_offset <= offset:
            page = marker_page
        else:
            break
    return page


def segment_legal_source(
    source: str | Path,
    law: str,
    jurisdiction: str,
    source_url: str = "local:UU_No_27_Tahun_2022_PDP_official.pdf",
    effective_date: str = DEFAULT_EFFECTIVE_DATE,
) -> list[dict[str, Any]]:
    pages = extract_pdf_pages(source)
    combined_parts: list[str] = []
    page_markers: list[tuple[int, int]] = []
    offset = 0
    for page in pages:
        marker = f"\n[[PAGE:{page['page']}]]\n"
        combined_parts.append(marker)
        offset += len(marker)
        page_markers.append((offset, int(page["page"])))
        text = normalize_legal_ocr(page["text"])
        combined_parts.append(text)
        offset += len(text)

    combined = "\n".join(combined_parts)
    start_index = combined.find("BAB I")
    searchable = combined[start_index:] if start_index >= 0 else combined
    base_offset = start_index if start_index >= 0 else 0
    matches = list(ARTICLE_RE.finditer(searchable))
    chunks: list[dict[str, Any]] = []
    seen: set[int] = set()

    for index, match in enumerate(matches):
        pasal_number = _roman_to_int(match.group(1))
        if pasal_number is None or pasal_number in seen:
            continue
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(searchable)
        raw_text = searchable[match.start() : next_start]
        raw_text = re.sub(r"\[\[PAGE:\d+\]\]", " ", raw_text)
        raw_text = normalize_legal_ocr(raw_text)
        if len(raw_text) < 30:
            continue
        seen.add(pasal_number)
        page = _page_for_offset(page_markers, base_offset + match.start())
        source_id = f"UU-PDP-2022-P{pasal_number}"
        chunks.append(
            {
                "source_id": source_id,
                "law": law,
                "jurisdiction": jurisdiction,
                "pasal": str(pasal_number),
                "ayat": None,
                "huruf": None,
                "section_title": f"Pasal {pasal_number}",
                "legal_text": raw_text,
                "legal_excerpt": compact_for_excerpt(raw_text, 1200),
                "source_url": source_url,
                "source_location": str(source),
                "page": page,
                "effective_date": effective_date,
                "notes": "Segmented at article level from local UU PDP PDF.",
            }
        )
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Segment UU PDP legal source into article-level chunks.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--law", default="UU PDP")
    parser.add_argument("--jurisdiction", default="Indonesia")
    parser.add_argument("--source-url", default="local:UU_No_27_Tahun_2022_PDP_official.pdf")
    parser.add_argument("--effective-date", default=DEFAULT_EFFECTIVE_DATE)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    chunks = segment_legal_source(
        source=args.source,
        law=args.law,
        jurisdiction=args.jurisdiction,
        source_url=args.source_url,
        effective_date=args.effective_date,
    )
    write_jsonl(args.output, chunks)
    print(f"Wrote {len(chunks)} legal chunks to {args.output}")


if __name__ == "__main__":
    main()

