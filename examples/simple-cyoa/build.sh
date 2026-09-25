#!/usr/bin/env bash
set -euo pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
TOOL_ROOT=$(cd -- "$HERE/../.." && pwd)
OUT="$HERE/build/project.json"
STATE="$HERE/build/state.json"

mkdir -p "$HERE/build"
rm -f "$STATE"

PYTHONPATH="$TOOL_ROOT" python -m iccplus_tools build \
  "$HERE/project-src/iccplus.build.json" \
  -o "$OUT" \
  --pretty

PYTHONPATH="$TOOL_ROOT" python -m iccplus_tools play \
  "$OUT" \
  "@$HERE/tests/playtest.json" \
  --state "$STATE" \
  --pretty
