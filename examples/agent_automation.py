"""Small subprocess client for the canonical ICC Plus Local agent contract."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _command() -> tuple[list[str], dict[str, str] | None]:
    installed = shutil.which("iccplus-local")
    if installed:
        return [installed], None

    source_root = Path(__file__).resolve().parents[1]
    if (source_root / "iccplus_tools").is_dir():
        env = os.environ.copy()
        current = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(source_root) if not current else f"{source_root}{os.pathsep}{current}"
        return [sys.executable, "-m", "iccplus_tools"], env

    raise RuntimeError("iccplus-local is not installed and a source checkout was not found")


def call_json(args: list[str], payload: Any | None = None) -> dict[str, Any]:
    command, env = _command()
    proc = subprocess.run(
        [*command, *args, "--compact"],
        input=None if payload is None else json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    stream = proc.stdout if proc.stdout.strip() else proc.stderr
    result = json.loads(stream)
    if proc.returncode != 0:
        raise RuntimeError(f"iccplus-local exit {proc.returncode}: {result}")
    return result


def inspect(project: str | Path, queries: list[dict[str, Any]]) -> dict[str, Any]:
    return call_json(["inspect", str(project), "-"], {"queries": queries})


def structure(project: str | Path, operations: list[dict[str, Any]], *, dry_run: bool = False) -> dict[str, Any]:
    request = {
        "format": "iccplus-structure-ops",
        "format_version": 1,
        "strict_fields": True,
        "operations": operations,
    }
    args = ["structure", str(project), "-"]
    if dry_run:
        args.append("--dry-run")
    return call_json(args, request)


if __name__ == "__main__":
    project = Path(__file__).with_name("demo_project.json")
    result = {
        "capabilities": call_json(["reference", "capabilities", "--brief"]),
        "inspection": inspect(project, [{"op": "check"}, {"op": "search", "query": "gear", "kind": "row"}]),
        "dry_run": structure(
            project,
            [{"op": "update", "kind": "choice", "ref": "sword", "values": {"title": "Blade"}}],
            dry_run=True,
        ),
    }
    print(json.dumps(result, separators=(",", ":")))
