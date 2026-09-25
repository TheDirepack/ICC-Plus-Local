from __future__ import annotations

import re
from typing import Any

_PARSE_INT_RE = re.compile(r"^[\t\n\v\f\r ]*([+-]?\d+)")


def parse_int(value: Any) -> int | None:
    """Small JavaScript ``parseInt`` compatibility helper for decimal ICC fields.

    ICC Plus calls ``parseInt`` without a radix for /ON# counts. The project
    format uses ordinary decimal counts, so reproducing its leading signed
    decimal-prefix behavior is sufficient and avoids Python ``int`` being more
    strict than the Viewer.
    """
    match = _PARSE_INT_RE.match(str(value))
    if not match:
        return None
    try:
        return int(match.group(1), 10)
    except ValueError:
        return None
