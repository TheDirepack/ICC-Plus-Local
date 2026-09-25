from __future__ import annotations

from dataclasses import dataclass, field
import math
import re
from typing import Any

_MODIFIER_RE = re.compile(r"/(IMG|WORD|RND|RS)#")


@dataclass(slots=True)
class NativeBuildEntry:
    """One entry in ICC Plus 2.10.6's Build Form string."""

    raw: str
    id: str
    count: int = 0
    random_scores: dict[int, float] = field(default_factory=dict)
    random_activations: list[str] = field(default_factory=list)
    word: str | None = None
    image: str | None = None
    row_button_point: str | None = None
    row_button_value: int | None = None

    @property
    def is_row_button(self) -> bool:
        return self.row_button_point is not None


def _parse_int(value: str, default: int = 0) -> int:
    match = re.match(r"^[+-]?\d+", value)
    return int(match.group(0)) if match else default


def _parse_number(value: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


def parse_build_string(value: str) -> list[NativeBuildEntry]:
    """Parse the exact comma-delimited Build Form syntax used by ICC Plus 2.10.6.

    The upstream format only escapes commas inside WORD and IMG payloads using
    ``/CHAR#``. Other delimiter strings intentionally retain their upstream
    meaning rather than inventing a more permissive local format.
    """
    out: list[NativeBuildEntry] = []
    for raw in str(value).split(','):
        if not raw:
            continue
        if '/RP#' in raw:
            ident, rest = raw.split('/RP#', 1)
            point, sep, amount = rest.partition('/NUM#')
            out.append(NativeBuildEntry(
                raw=raw,
                id=ident,
                row_button_point=point,
                row_button_value=_parse_int(amount, 0) if sep else 0,
            ))
            continue

        parts = _MODIFIER_RE.split(raw)
        head = parts[0]
        if '/ON#' in head:
            ident, count_text = head.split('/ON#', 1)
            count = _parse_int(count_text, 0)
        else:
            ident, count = head, 0
        entry = NativeBuildEntry(raw=raw, id=ident, count=count)
        for i in range(1, len(parts), 2):
            name = parts[i]
            payload = parts[i + 1] if i + 1 < len(parts) else ''
            if name == 'RS':
                for token in payload.split('/AND#'):
                    index, sep, number = token.partition(':')
                    if not sep:
                        continue
                    try:
                        score_index = int(index)
                    except ValueError:
                        continue
                    if score_index >= 0:
                        entry.random_scores[score_index] = _parse_number(number)
            elif name == 'RND':
                entry.random_activations = [
                    token.replace('/RON#', '/ON#')
                    for token in payload.split('/AND#') if token
                ]
            elif name == 'WORD':
                entry.word = payload.replace('/CHAR#', ',')
            elif name == 'IMG':
                entry.image = payload.replace('/CHAR#', ',')
        out.append(entry)
    return out


def number_text(value: float | int) -> str:
    number = float(value)
    if math.isfinite(number) and number.is_integer():
        return str(int(number))
    return format(number, '.15g')


def build_entry_text(entry: NativeBuildEntry) -> str:
    if entry.is_row_button:
        return f'{entry.id}/RP#{entry.row_button_point or ""}/NUM#{entry.row_button_value or 0}'
    text = entry.id
    if entry.count != 0:
        text += f'/ON#{entry.count}'
    if entry.random_scores:
        text += '/RS#' + '/AND#'.join(
            f'{index}:{number_text(value)}' for index, value in sorted(entry.random_scores.items())
        )
    if entry.random_activations:
        text += '/RND#' + '/AND#'.join(token.replace('/ON#', '/RON#') for token in entry.random_activations)
    if entry.word is not None:
        text += '/WORD#' + entry.word.replace(',', '/CHAR#')
    if entry.image is not None:
        text += '/IMG#' + entry.image.replace(',', '/CHAR#')
    return text


def serialize_build_entries(entries: list[NativeBuildEntry]) -> str:
    return ','.join(build_entry_text(entry) for entry in entries)


def entry_to_dict(entry: NativeBuildEntry) -> dict[str, Any]:
    return {
        'id': entry.id,
        'count': entry.count,
        'random_scores': {str(k): v for k, v in entry.random_scores.items()},
        'random_activations': list(entry.random_activations),
        'word': entry.word,
        'image': entry.image,
        'row_button_point': entry.row_button_point,
        'row_button_value': entry.row_button_value,
    }
