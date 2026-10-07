from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .scenario import run_scenario
from .simulator import Simulator
from .version import __version__


def _load_json(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def _print(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="iccplus-viewer-test",
        description="Minimal ICC Plus Viewer/runtime testing environment. It cannot build or edit CYOAs.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    view = sub.add_parser("view", help="Show the current player-visible view of a project")
    view.add_argument("project")
    view.add_argument("--seed", type=int, default=0)
    view.add_argument("--verbose", action="store_true")
    view.add_argument("--include-backpack", action="store_true")

    status = sub.add_parser("status", help="Inspect one selectable entity in the clean runtime state")
    status.add_argument("project")
    status.add_argument("id")
    status.add_argument("--seed", type=int, default=0)

    row = sub.add_parser("row-visible", help="Check a Row requirement directly")
    row.add_argument("project")
    row.add_argument("id")
    row.add_argument("--seed", type=int, default=0)

    scenario = sub.add_parser("scenario", help="Run a JSON selection/assertion scenario")
    scenario.add_argument("project")
    scenario.add_argument("spec")
    scenario.add_argument("--seed", type=int, default=0)

    args = parser.parse_args(argv)
    project = _load_json(args.project)

    if args.command == "view":
        _print(Simulator(project, seed=args.seed).player_view(
            verbose=args.verbose,
            include_backpack=args.include_backpack,
        ))
        return 0
    if args.command == "status":
        _print(Simulator(project, seed=args.seed).choice_status(args.id).to_dict())
        return 0
    if args.command == "row-visible":
        sim = Simulator(project, seed=args.seed)
        _print({"id": args.id, "visible": sim.row_visible(args.id)})
        return 0
    if args.command == "scenario":
        result = run_scenario(project, _load_json(args.spec), seed=args.seed)
        _print(result)
        return 0 if result.get("passed") else 1
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
