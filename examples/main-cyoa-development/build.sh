#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
TOOL_ROOT=$(cd -- "$HERE/../.." && pwd)
mkdir -p "$HERE/build"
rm -f "$HERE/build/state.json"
PYTHONPATH="$TOOL_ROOT" python -m iccplus_tools build "$HERE/project-src/iccplus.build.json" -o "$HERE/build/project.json" --pretty
PYTHONPATH="$TOOL_ROOT" python -m iccplus_tools play "$HERE/build/project.json" "@$HERE/tests/playtest.json" --state "$HERE/build/state.json" --pretty
