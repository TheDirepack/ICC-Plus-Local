#!/usr/bin/env bash
set -euo pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd -- "$HERE/.." && pwd)
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
STATE=$(mktemp)
rm -f "$STATE"
trap 'rm -f "$STATE" "$HERE/simple-cyoa/build/state.json" "$HERE/main-cyoa-development/build/state.json"' EXIT

python -m compileall -q "$HERE" "$HERE/simple-cyoa" "$HERE/main-cyoa-development"

python -m iccplus_tools inspect "$HERE/demo_project.json" "@$HERE/agent_inspect.json" --compact >/dev/null
python -m iccplus_tools structure "$HERE/demo_project.json" "@$HERE/agent_operations.json" --dry-run --compact >/dev/null
python -m iccplus_tools structure "$HERE/demo_project.json" "@$HERE/bulk_selector_ops.json" --dry-run --compact >/dev/null
python -m iccplus_tools rules "$HERE/demo_project.json" "@$HERE/repair_ops.json" --dry-run --compact >/dev/null
python -m iccplus_tools style "$HERE/demo_project.json" "@$HERE/visual_manifest.json" --dry-run --compact >/dev/null
python -m iccplus_tools play "$HERE/demo_project.json" "@$HERE/demo_scenario.json" --compact >/dev/null
python -m iccplus_tools play "$HERE/demo_project.json" "@$HERE/session_request.json" --state "$STATE" --compact >/dev/null
python -m iccplus_tools play "$HERE/demo_project.json" "@$HERE/session_continue_request.json" --state "$STATE" --compact >/dev/null
python "$HERE/agent_automation.py" >/dev/null

"$HERE/simple-cyoa/build.sh" >/dev/null
"$HERE/main-cyoa-development/build.sh" >/dev/null

python -m iccplus_tools inspect "$HERE/simple-cyoa/build/project.json" '{"queries":[{"op":"check"}]}' --compact >/dev/null
python -m iccplus_tools inspect "$HERE/main-cyoa-development/build/project.json" '{"queries":[{"op":"check"}]}' --compact >/dev/null

echo "All examples passed."
