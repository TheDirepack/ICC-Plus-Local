#!/usr/bin/env python3
"""Generate the tiny example's phased authoring files from plain Python data.

This demonstrates a builder pattern without hard-coding project-specific source
formats. Real projects can replace the data below with YAML, a database export,
or another canonical source model, then emit the same ICC Plus phase files.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "generated-src"

ROWS = [
    {
        "id": "row_origin",
        "title": "Origin",
        "text": "Choose where your traveler grew up.",
        "allowed": 1,
        "choices": [
            ("origin_station", "Orbital station", "You grew up in a dense artificial habitat with reliable services.", 1),
            ("origin_frontier", "Frontier settlement", "You grew up in a small settlement where repairs and self-reliance were routine.", 1),
        ],
    },
    {
        "id": "row_specialty",
        "title": "Specialty",
        "text": "Choose your main field of training.",
        "allowed": 1,
        "choices": [
            ("specialty_engineer", "Engineer", "You can maintain machinery and diagnose common technical failures.", 2),
            ("specialty_scout", "Scout", "You are trained in navigation, field observation, and route planning.", 2),
        ],
    },
]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(exist_ok=True)

    structure_ops = []
    rules_ops = [
        {"op": "add", "kind": "point", "values": {"id": "cp", "name": "Choice Points", "startingSum": 6}}
    ]

    for row in ROWS:
        structure_ops.append({"op": "add", "kind": "row", "values": {"id": row["id"], "title": row["title"], "titleText": row["text"]}})
        rules_ops.append({"op": "update", "kind": "row", "ref": row["id"], "values": {"allowedChoices": row["allowed"]}})
        for choice_id, title, text, cost in row["choices"]:
            structure_ops.append({"op": "add", "kind": "choice", "parent": row["id"], "values": {"id": choice_id, "title": title, "text": text}})
            rules_ops.append({"op": "score_many", "target": choice_id, "point": "cp", "value": cost})

    write_json(
        OUT / "10-structure.json",
        {"format": "iccplus-structure-ops", "format_version": 1, "strict_fields": True, "operations": structure_ops},
    )
    write_json(
        OUT / "20-rules.json",
        {"format": "iccplus-rules-ops", "format_version": 1, "strict_fields": True, "operations": rules_ops},
    )
    write_json(
        OUT / "iccplus.build.json",
        {
            "format": "iccplus-build",
            "format_version": 2,
            "steps": [
                {"name": "content", "phase": "structure", "script": "10-structure.json"},
                {"name": "mechanics", "phase": "rules", "script": "20-rules.json"},
            ],
        },
    )

    print(f"Wrote example phase files to {OUT}")


if __name__ == "__main__":
    main()
