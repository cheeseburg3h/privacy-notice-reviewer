from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path


class _TextOnlyParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[no-untyped-def]
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag.lower() in {"p", "div", "section", "article", "br", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag.lower() in {"p", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        rendered: list[str] = []
        for part in self.parts:
            if part == "\n":
                rendered.append("\n")
                continue
            stripped = part.strip()
            if stripped:
                rendered.append(stripped + " ")
        text = "".join(rendered)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def html_to_text(html: str) -> str:
    parser = _TextOnlyParser()
    parser.feed(html)
    return parser.text()


def load_html_text(path: str | Path) -> str:
    html = Path(path).read_text(encoding="utf-8", errors="ignore")
    return html_to_text(html)
