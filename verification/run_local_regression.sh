#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

./run-tests
python verification/scripts/generate_verification_kit.py
python - <<'PY'
from pathlib import Path
import hashlib
from iccplus_tools.upstream_2106 import default_export_bytes
expected = '35ba40a5e4a39b41c79d5e0f929404d9789d3173331059c9e635e72187c86faf'
actual = hashlib.sha256(default_export_bytes()).hexdigest()
assert actual == expected, (actual, expected)
assert len(default_export_bytes()) == 13414
assert not default_export_bytes().endswith(b'\n')
print('default export parity: OK')
PY

# Compression tests are intentionally separate from the normal regression suite.
./run-compression-tests
