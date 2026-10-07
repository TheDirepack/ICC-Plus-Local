from __future__ import annotations

from html.parser import HTMLParser
from typing import Any


class _BrowserTextContent(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def browser_text_content(value: Any) -> str:
    """Small DOM ``textContent`` equivalent used by Viewer-facing text paths."""
    parser = _BrowserTextContent()
    parser.feed(str(value or ""))
    parser.close()
    return "".join(parser.parts)
