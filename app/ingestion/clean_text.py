from __future__ import annotations

import re

WHITESPACE_RE = re.compile(r"[ \t]+")
BLANK_RE = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = WHITESPACE_RE.sub(" ", text)
    text = re.sub(r" *\n *", "\n", text)
    return BLANK_RE.sub("\n\n", text).strip()


def normalize_legal_ocr(text: str) -> str:
    text = normalize_text(text)
    replacements = {
        "Pasal I": "Pasal 1",
        "Pasal l": "Pasal 1",
        "ayat (l)": "ayat (1)",
        "ayat (I)": "ayat (1)",
        "(l)": "(1)",
        "(I)": "(1)",
        "Data Fribadi": "Data Pribadi",
        "ora.ng": "orang",
        "penggu.naan": "penggunaan",
        "ker.rangan": "keuangan",
        "rvilayah": "wilayah",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\bPasa[17lI](\d+)\b", r"Pasal \1", text)
    text = re.sub(r"\bPasal\s?(\d+)T\b", r"Pasal \g<1>7", text)
    text = re.sub(r"\bPasal(\d+)\b", r"Pasal \1", text)
    text = re.sub(r"(?m)^\s*l(\d+)l\s+", r"(\1) ", text)
    text = re.sub(r"\((\d+)l\)", r"(\1)", text)
    text = re.sub(r"\((\d+)l", r"(\1)", text)
    return text


def compact_for_excerpt(text: str, max_chars: int = 900) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


def split_paragraphs(text: str, min_chars: int = 25) -> list[str]:
    normalized = normalize_text(text)
    raw_parts = re.split(r"\n\s*\n|(?<=\.)\n(?=[A-Z0-9A-ZÄÖÜ])", normalized)
    parts: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            joined = " ".join(buffer).strip()
            if joined:
                parts.append(joined)
            buffer.clear()

    for part in raw_parts:
        candidate = part.strip()
        if not candidate:
            flush()
            continue
        if len(candidate) < min_chars and buffer:
            buffer.append(candidate)
        elif len(candidate) < min_chars:
            buffer.append(candidate)
        else:
            flush()
            parts.append(candidate)
    flush()
    return parts


def is_heading(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 3 or len(stripped) > 120:
        return False
    letters = [char for char in stripped if char.isalpha()]
    if letters and sum(char.isupper() for char in letters) / len(letters) > 0.7:
        return True
    return bool(re.match(r"^(\d+\.|[A-Z]\.|BAB\s+|Pasal\s+)", stripped, re.IGNORECASE))
