#!/usr/bin/env python3
"""Build and smoke-test the simple ICC Plus example."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TOOL_ROOT = (HERE / "../..").resolve()
BUILD_DIR = HERE / "build"
PROJECT = BUILD_DIR / "project.json"
STATE = BUILD_DIR / "state.json"


def run(*args: str) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(TOOL_ROOT)
    subprocess.run(
        [sys.executable, "-m", "iccplus_tools", *args],
        check=True,
        cwd=HERE,
        env=env,
    )


def main() -> None:
    BUILD_DIR.mkdir(exist_ok=True)
    STATE.unlink(missing_ok=True)
    run("build", "project-src/iccplus.build.json", "-o", str(PROJECT), "--pretty")
    run("play", str(PROJECT), "@tests/playtest.json", "--state", str(STATE), "--pretty")


if __name__ == "__main__":
    main()
